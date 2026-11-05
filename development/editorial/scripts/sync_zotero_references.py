"""Add only missing AssistiveVision records to the user's Zotero web library.

The API key is read from a private file. Never pass it as a CLI argument.
Without --apply this script performs a read-only comparison.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
import uuid

from prepare_zotero_library import OUT, compare, records, normalized

BASE='https://api.zotero.org'

def resolved_comparison(wanted,existing,resolutions):
    result=compare(wanted,existing)
    by_key={i['key']:i for i in existing}
    for row in result:
        decision=resolutions.get(str(row['reference_id']))
        if not decision:continue
        key=decision['key']
        if key not in by_key:raise SystemExit('A previously reviewed Zotero item is no longer available.')
        item=by_key[key]['data']
        if normalized(item.get('title',''))!=normalized(row['title']):
            raise SystemExit('A reviewed item title changed; inspect the saved correspondence before writing.')
        row['status']='existing';row['matches']=[dict(key=key,reason='reviewed: '+decision['reason'],title=item['title'],date=item.get('date'),DOI=item.get('DOI'))]
    return result

class Zotero:
    def __init__(self,secret_file):
        self.key=Path(secret_file).read_text().strip()
        if not self.key or len(self.key)>256 or any(c.isspace() for c in self.key):
            raise SystemExit('The private file must contain a Zotero API key only.')

    def call(self,path,method='GET',data=None,version=None):
        headers={'Zotero-API-Version':'3','Zotero-API-Key':self.key}
        if data is not None:headers['Content-Type']='application/json'
        if method=='POST':headers['Zotero-Write-Token']=uuid.uuid4().hex
        if version is not None:headers['If-Unmodified-Since-Version']=str(version)
        request=urllib.request.Request(BASE+path,data=json.dumps(data).encode() if data is not None else None,headers=headers,method=method)
        try:
            with urllib.request.urlopen(request,timeout=30) as response:
                raw=response.read();content_type=response.headers.get('Content-Type','')
                result=json.loads(raw) if 'json' in content_type else raw.decode()
                return result,response.headers
        except urllib.error.HTTPError as exc:
            # Do not include request URLs or headers: the key-info URL contains a secret.
            if path.startswith('/keys/'):
                raise SystemExit('Zotero rejected the API key (HTTP '+str(exc.code)+').') from None
            detail=exc.read().decode(errors='replace').replace(self.key,'[redacted]')
            raise SystemExit('Zotero API HTTP '+str(exc.code)+': '+detail[:600]) from None
        except urllib.error.URLError:
            raise SystemExit('Unable to connect to the Zotero API; no credential was printed.') from None

    def identify(self):
        info,_=self.call('/keys/'+urllib.parse.quote(self.key,safe=''))
        access=info.get('access',{}).get('user',{})
        if not access.get('library'):raise SystemExit('The key does not allow reading the personal library.')
        return str(info['userID']),bool(access.get('write'))

    def paged(self,path):
        rows=[];start=0
        while True:
            sep='&' if '?' in path else '?'
            batch,_=self.call(path+sep+urllib.parse.urlencode(dict(format='json',limit=100,start=start)))
            if not isinstance(batch,list):raise SystemExit('Unexpected Zotero list response.')
            rows.extend(batch)
            if len(batch)<100:return rows
            start+=len(batch)

def main():
    p=argparse.ArgumentParser();p.add_argument('--secret-file',required=True,type=Path)
    p.add_argument('--apply',action='store_true');p.add_argument('--collection',default='AssistiveVision — Trabajo de grado')
    p.add_argument('--normalize-reviewed',action='store_true',help='Apply the specifically reviewed bibliographic corrections, preserving keys and child items')
    args=p.parse_args()
    api=Zotero(args.secret_file);uid,can_write=api.identify();prefix='/users/'+uid
    wanted=records();existing=api.paged(prefix+'/items/top')
    decisions_path=OUT/'coincidencias_confirmadas.json'
    decisions=json.loads(decisions_path.read_text()) if decisions_path.exists() else {}
    if decisions and str(decisions.get('user_id'))!=uid:raise SystemExit('The correspondence file belongs to another Zotero account.')
    resolutions=decisions.get('resolutions',{})
    comparison=resolved_comparison(wanted,existing,resolutions)
    # Persist only report-related matches, never the user's complete library inventory.
    receipt=dict(user_id=uid,library_url='https://www.zotero.org/users/'+uid,
                 applied=False,comparison_before=comparison,created=[],reused=[],ambiguous=[])
    OUT.mkdir(parents=True,exist_ok=True)
    receipt_path=OUT/'resultado_zotero.json'
    def save():receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    save()
    missing={r['reference_id'] for r in comparison if r['status']=='missing'}
    receipt['ambiguous']=[r for r in comparison if r['status']=='ambiguous']
    receipt['reused']=[r for r in comparison if r['status']=='existing']
    if args.apply:
        if not can_write:raise SystemExit('The key allows reads but does not allow writes to the personal library.')
        receipt['normalized']=[]
        if args.normalize_reviewed:
            wanted_by_id={r['reference_id']:r['item'] for r in wanted}
            selected={r['reference_id']:r for r in comparison if r['status']=='existing'}
            for rid in decisions.get('normalize_reference_ids',[]):
                if rid not in selected:raise SystemExit('A reviewed bibliographic correction no longer matches an existing item.')
                key=selected[rid]['matches'][0]['key']
                before,_=api.call(prefix+'/items/'+key)
                canonical=dict(wanted_by_id[rid])
                template,_=api.call('/items/new?'+urllib.parse.urlencode(dict(itemType=canonical['itemType'])))
                # Preserve all compatible metadata outside the specifically canonical fields.
                after={k:v for k,v in before['data'].items() if k in template}
                for k,v in canonical.items():
                    if k not in ['tags','extra','creators']:after[k]=v
                # Keep full given names where a canonical surname/initial matches.
                people=[]
                for person in canonical['creators']:
                    person=dict(person)
                    if person.get('lastName'):
                        old=next((p for p in before['data'].get('creators',[]) if p.get('creatorType')==person['creatorType'] and normalized(p.get('lastName',''))==normalized(person['lastName']) and p.get('firstName','')[:1].lower()==person.get('firstName','')[:1].lower()),None)
                        if old and len(old.get('firstName',''))>len(person.get('firstName','')):person['firstName']=old['firstName']
                    people.append(person)
                after['creators']=people
                prior_date=before['data'].get('date','')
                if canonical.get('date') and prior_date.startswith(canonical['date']):after['date']=prior_date
                backup=dict(reference_id=rid,key=key,before=before,after=after)
                receipt['normalized'].append(backup);save()
                api.call(prefix+'/items/'+key,method='PUT',data=after,version=before['version'])
            existing=api.paged(prefix+'/items/top')
        collections=api.paged(prefix+'/collections')
        found=[c for c in collections if c['data']['name']==args.collection and not c['data'].get('parentCollection')]
        if len(found)>1:raise SystemExit('There is more than one matching destination collection; choose a unique name.')
        if found:collection_key=found[0]['key']
        else:
            created,_=api.call(prefix+'/collections',method='POST',data=[dict(name=args.collection,parentCollection=False)])
            if created.get('failed'):raise SystemExit('Zotero could not create the destination collection.')
            collection_key=created['successful']['0']['key']
        receipt['collection_key']=collection_key
        receipt['collection_name']=args.collection
        payload=[];reference_ids=[]
        for r in wanted:
            if r['reference_id'] not in missing:continue
            item=dict(r['item']);item['collections']=[collection_key]
            payload.append(item);reference_ids.append(r['reference_id'])
        if payload:
            result,_=api.call(prefix+'/items',method='POST',data=payload)
            for index,created in result.get('successful',{}).items():
                receipt['created'].append(dict(reference_id=reference_ids[int(index)],key=created['key'],title=created['data']['title']))
            receipt['failures']=result.get('failed',{})
            save()
            if receipt['failures']:raise SystemExit('Some references were rejected; see the saved receipt before retrying.')
        # Add existing matched records to the collection without changing their metadata.
        items_by_key={i['key']:i for i in existing}
        for match in receipt['reused']:
            key=match['matches'][0]['key'];item=items_by_key[key]
            current=list(item['data'].get('collections',[]))
            if collection_key not in current:
                api.call(prefix+'/items/'+key,method='PATCH',data=dict(collections=current+[collection_key]),version=item['version'])
        receipt['applied']=True
        receipt['comparison_after']=resolved_comparison(wanted,api.paged(prefix+'/items/top'),resolutions)
        keys=[r['key'] for r in receipt['created']]+[m['matches'][0]['key'] for m in receipt['reused']]
        if keys:
            query=urllib.parse.urlencode(dict(itemKey=','.join(keys),format='bib',style='apa',locale='es-ES',linkwrap=1))
            bibliography,_=api.call(prefix+'/items?'+query)
            (OUT/'Bibliografia_APA_Zotero.html').write_text(bibliography)
        state=json.loads((OUT/'estado_preparacion.json').read_text()) if (OUT/'estado_preparacion.json').exists() else {}
        state.update(imported_into_zotero=True,created_count=len(receipt['created']),reused_count=len(receipt['reused']),ambiguous_count=len(receipt['ambiguous']))
        (OUT/'estado_preparacion.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    save()
    print(json.dumps(dict(applied=receipt['applied'],created=len(receipt['created']),reused=len(receipt['reused']),normalized=len(receipt.get('normalized',[])),missing_before=len(missing),ambiguous=len(receipt['ambiguous'])),indent=2))

if __name__=='__main__':main()
