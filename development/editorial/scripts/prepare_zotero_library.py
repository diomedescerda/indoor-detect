"""Build structured Zotero/CSL records from the report's verified reference map.

This command prepares files. It never writes to a Zotero library on its own.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import unicodedata

from tutor_revision_content import REFERENCES

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'development/editorial/revision/Zotero'

# Source types and fields are explicit. Dates of undated documentation stay empty;
# APA's n.d./s. f. and a/b suffixes are formatting, never publication metadata.
DETAILS = {
1: dict(itemType='report',institution='World Health Organization'),
2: dict(itemType='journalArticle',publicationTitle='Procedia Computer Science',volume='252',pages='457–469'),
3: dict(itemType='journalArticle',publicationTitle='Computers, Materials & Continua',volume='73',issue='2',pages='3473–3495'),
4: dict(itemType='journalArticle',publicationTitle='Procedia Computer Science',volume='218',pages='1144–1155'),
5: dict(itemType='webpage',websiteTitle='TensorFlow'),
6: dict(itemType='preprint',repository='arXiv',archiveID='1506.01497',genre='Preprint'),
7: dict(itemType='conferencePaper',proceedingsTitle='2016 IEEE Conference on Computer Vision and Pattern Recognition (CVPR)',publisher='IEEE',pages='779–788'),
8: dict(itemType='bookSection',bookTitle='Computer Vision – ECCV 2016',publisher='Springer',pages='21–37'),
9: dict(itemType='conferencePaper',proceedingsTitle='2020 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)',publisher='IEEE',pages='10781–10790'),
10: dict(itemType='report',reportType='Propuesta de pasantía en investigación',institution='Universidad del Magdalena',language='es'),
11: dict(itemType='report',institution='Universidad del Magdalena',language='es'),
12: dict(itemType='report',institution='Universidad del Magdalena',language='es'),
13: dict(itemType='preprint',repository='ResearchGate',genre='Preprint'),
14: dict(itemType='journalArticle',publicationTitle='Journal of Computer Sciences Institute',volume='34',pages='8–13'),
15: dict(itemType='preprint',repository='arXiv',archiveID='1704.04861',genre='Preprint'),
16: dict(itemType='conferencePaper',proceedingsTitle='2018 IEEE/CVF Conference on Computer Vision and Pattern Recognition',publisher='IEEE',pages='4510–4520'),
17: dict(itemType='journalArticle',publicationTitle='Journal of Physics: Conference Series',volume='1651',issue='1',pages='012114'),
18: dict(itemType='journalArticle',publicationTitle='Scientific Reports',volume='15',pages='16163'),
19: dict(itemType='webpage',websiteTitle='Google AI Edge'),
20: dict(itemType='webpage',websiteTitle='Ultralytics'),
21: dict(itemType='webpage',websiteTitle='Ultralytics'),
22: dict(itemType='bookSection',bookTitle='Computer Vision – ECCV 2014',publisher='Springer',pages='740–755'),
23: dict(itemType='journalArticle',publicationTitle='International Journal of Computer Vision',volume='128',pages='1956–1981'),
24: dict(itemType='webpage',websiteTitle='ONNX Runtime'),
25: dict(itemType='webpage',websiteTitle='PyTorch'),
26: dict(itemType='bookSection',bookTitle='Computer Vision – ECCV 2020',publisher='Springer',pages='213–229'),
27: dict(itemType='computerProgram',company='GitHub'),
28: dict(itemType='book',publisher='Cambridge University Press'),
29: dict(itemType='webpage',websiteTitle='GitHub'),
30: dict(itemType='webpage',websiteTitle='Android Developers'),
31: dict(itemType='webpage',websiteTitle='Google AI Edge'),
32: dict(itemType='webpage',websiteTitle='Khronos Group'),
33: dict(itemType='webpage',websiteTitle='Roboflow'),
34: dict(itemType='computerProgram',company='GitHub',versionNumber='85c852ddcb543bce1bd69ad0db307f895d597881'),
35: dict(itemType='webpage',websiteTitle='Android Developers'),
36: dict(itemType='webpage',websiteTitle='Google AI Edge'),
37: dict(itemType='webpage',websiteTitle='sherpa-onnx'),
38: dict(itemType='preprint',repository='arXiv',archiveID='2106.06103',genre='Preprint'),
39: dict(itemType='computerProgram',company='GitHub'),
40: dict(itemType='webpage',websiteTitle='Android Developers'),
41: dict(itemType='webpage',websiteTitle='Android Developers'),
42: dict(itemType='webpage',websiteTitle='NIST/SEMATECH e-Handbook of Statistical Methods'),
43: dict(itemType='journalArticle',publicationTitle='The Annals of Statistics',volume='7',issue='1',pages='1–26'),
44: dict(itemType='journalArticle',publicationTitle='Journal of the Royal Statistical Society: Series B (Statistical Methodology)',volume='69',issue='3',pages='369–390'),
45: dict(itemType='book',publisher='Springer'),
46: dict(itemType='report',institution='Camera & Imaging Products Association',reportNumber='CIPA DC-X010-2017',reportType='Draft'),
47: dict(itemType='webpage',websiteTitle='NumPy documentation'),
48: dict(itemType='webpage',websiteTitle='Pillow documentation'),
49: dict(itemType='journalArticle',publicationTitle='Computing in Science & Engineering',volume='9',issue='3',pages='90–95'),
}

CORPORATE={1,5,11,12,19,20,21,24,25,27,29,30,31,32,33,35,36,37,39,40,41,42,46,47,48}
EDITORS={
8:[('Leibe','B.'),('Matas','J.'),('Sebe','N.'),('Welling','M.')],
22:[('Fleet','D.'),('Pajdla','T.'),('Schiele','B.'),('Tuytelaars','T.')],
26:[('Vedaldi','A.'),('Bischof','H.'),('Brox','T.'),('Frahm','J.-M.')],
}

def normalized(s):
    return ''.join(c for c in unicodedata.normalize('NFKD',s).casefold() if c.isalnum())

def doi_normalized(s):
    return re.sub(r'^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)','',s.strip(),flags=re.I).rstrip('.').lower()

def creators(k,entry,year):
    prefix=entry.split(' ('+year+').',1)[0]
    if k in CORPORATE:return [dict(creatorType='author',name=prefix.rstrip('.'))]
    parts=prefix.replace(', & ',', ').split(', ')
    if len(parts)%2:raise ValueError('Cannot parse creators of reference '+str(k))
    return [dict(creatorType='author',lastName=parts[i],firstName=parts[i+1]) for i in range(0,len(parts),2)]

def records():
    result=[]
    for k,(author,year,entry) in REFERENCES.items():
        item=dict(DETAILS[k]);item['creators']=creators(k,entry,year)
        if item['itemType']=='computerProgram':
            for person in item['creators']:person['creatorType']='programmer'
        body=entry.split(' ('+year+'). ',1)[1]
        if item['itemType'] in ['journalArticle','conferencePaper','bookSection']:
            title=body.split('. *',1)[0].split('. En ',1)[0]
            if k in [8,22,26]:title=body.split('. En ',1)[0]
        elif k==42:title='Analysis of paired observations'
        else:
            matches=re.findall(r'\*([^*]+)\*',body)
            if not matches:raise ValueError('No title for '+str(k))
            title=matches[0]
        item['title']=title
        if year!='s. f.':item['date']=year
        else:item['date']=''
        if item['itemType']!='computerProgram':item.setdefault('language','en')
        urls=re.findall(r'https?://[^\s*]+',entry)
        if urls:item['url']=urls[-1].rstrip('.')
        match=re.search(r'https?://doi\.org/(\S+)',entry)
        if match:item['DOI']=match[1].rstrip('.')
        if 'Recuperado el 5 de noviembre de 2026' in entry:item['accessDate']='2026-11-05'
        for last,first in EDITORS.get(k,[]):item['creators'].append(dict(creatorType='editor',lastName=last,firstName=first))
        # Store local reference IDs in a tag, not in the publication's title or date.
        item['tags']=[dict(tag='AssistiveVision'),dict(tag=f'AssistiveVision-ref-{k:02d}')]
        item['extra']='Original reference number in AssistiveVision: '+str(k)
        result.append(dict(reference_id=k,item=item))
    assert len(result)==49
    assert len({normalized(r['item']['title']) for r in result})==49
    return result

def csl(r):
    item=r['item'];typ=item['itemType']
    out=dict(id='assistivevision-'+str(r['reference_id']),type={
        'report':'report','journalArticle':'article-journal','conferencePaper':'paper-conference',
        'bookSection':'chapter','webpage':'webpage','preprint':'article',
        'computerProgram':'software','book':'book',
    }[typ],title=item['title'],language=item.get('language','en'))
    for role in ['author','editor']:
        people=[]
        for person in item['creators']:
            effective_role='author' if person['creatorType']=='programmer' else person['creatorType']
            if effective_role!=role:continue
            people.append(dict(literal=person['name']) if person.get('name') else dict(family=person['lastName'],given=person.get('firstName','')))
        if people:out[role]=people
    for source,target in [('publicationTitle','container-title'),('proceedingsTitle','container-title'),('bookTitle','container-title'),('websiteTitle','container-title'),('repository','publisher'),('publisher','publisher'),('institution','publisher'),('company','publisher'),('volume','volume'),('issue','issue'),('pages','page'),('DOI','DOI'),('url','URL'),('versionNumber','version'),('reportNumber','number'),('reportType','genre'),('genre','genre')]:
        if item.get(source):out[target]=item[source]
    if item['date']:out['issued']={'date-parts':[[int(item['date'])]]}
    if item.get('accessDate'):out['accessed']={'date-parts':[[int(x) for x in item['accessDate'].split('-')]]}
    if item.get('archiveID'):out['number']=item['archiveID']
    out['note']=item['extra']
    return out

def ris(r):
    item=r['item'];typ=item['itemType'];lines=[]
    def add(tag,value):
        if value:lines.append(tag+'  - '+str(value).replace('\n',' '))
    add('TY',{'journalArticle':'JOUR','book':'BOOK','bookSection':'CHAP','conferencePaper':'CPAPER','report':'RPRT','preprint':'UNPB','computerProgram':'COMP','webpage':'ELEC'}[typ])
    add('ID','assistivevision-'+str(r['reference_id']));add('TI',item['title'])
    for p in item['creators']:
        # A final comma preserves single-field corporate creators in Zotero's RIS translator.
        name=p['name']+',' if p.get('name') else p['lastName']+', '+p.get('firstName','')
        add('A2' if p['creatorType']=='editor' else 'AU',name)
    add('PY',item['date']);add('T2',item.get('publicationTitle') or item.get('proceedingsTitle') or item.get('bookTitle') or item.get('websiteTitle'))
    add('PB',item.get('publisher') or item.get('institution') or item.get('company'))
    add('VL',item.get('volume'));add('IS',item.get('issue'));add('DO',item.get('DOI'));add('UR',item.get('url'))
    pages=re.split('[–-]',item.get('pages',''),maxsplit=1)
    add('SP',pages[0]);add('EP',pages[1] if len(pages)>1 else '')
    add('M1',item.get('reportNumber') or item.get('archiveID'));add('ET',item.get('versionNumber'));add('LA',item.get('language'))
    for tag in item['tags']:add('KW',tag['tag'])
    add('N1',item['extra']);add('Y2',item.get('accessDate'))
    lines.append('ER  - ')
    return '\n'.join(lines)+'\n'

def compare(wanted,existing):
    """Classify exact DOI/URL/title matches. Ambiguous matches never create items."""
    result=[]
    for record in wanted:
        item=record['item'];matches=[]
        for raw in existing:
            data=raw.get('data',raw)
            if data.get('itemType') in ['attachment','note','annotation']:continue
            reason=None
            if item.get('DOI') and data.get('DOI') and doi_normalized(item['DOI'])==doi_normalized(data['DOI']):reason='doi'
            elif item.get('url') and data.get('url') and item['url'].rstrip('/').lower()==data['url'].rstrip('/').lower():reason='url'
            elif normalized(item['title'])==normalized(data.get('title','')):
                wanted_author=next((p.get('name') or p.get('lastName','') for p in item['creators'] if p.get('creatorType') in ['author','programmer']), '')
                existing_author=next((p.get('name') or p.get('lastName','') for p in data.get('creators',[]) if p.get('creatorType') in ['author','programmer']), '')
                reason='title+author' if normalized(wanted_author)==normalized(existing_author) else 'possible-title-match'
            if reason:matches.append(dict(key=raw.get('key') or data.get('key'),reason=reason,title=data.get('title'),date=data.get('date'),DOI=data.get('DOI')))
        # A specific identifier outranks an alternate edition with the same title.
        if any(m['reason']=='doi' for m in matches):matches=[m for m in matches if m['reason']=='doi']
        elif any(m['reason']=='url' for m in matches):matches=[m for m in matches if m['reason']=='url']
        status='missing' if not matches else 'existing' if len(matches)==1 and matches[0]['reason']!='possible-title-match' else 'ambiguous'
        result.append(dict(reference_id=record['reference_id'],title=item['title'],status=status,matches=matches))
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--existing',type=Path,help='JSON export of native Zotero API items, for deduplication');args=p.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    rr=records()
    (OUT/'registros_zotero.json').write_text(json.dumps(rr,ensure_ascii=False,indent=2)+'\n')
    (OUT/'referencias_assistivevision.csl.json').write_text(json.dumps([csl(r) for r in rr],ensure_ascii=False,indent=2)+'\n')
    (OUT/'referencias_assistivevision.ris').write_text('\n'.join(ris(r) for r in rr))
    report=dict(reference_count=len(rr),types=dict(Counter(r['item']['itemType'] for r in rr)),imported_into_zotero=False)
    if args.existing:
        existing=json.loads(args.existing.read_text())
        if isinstance(existing,dict):existing=existing.get('items',existing.get('data',[]))
        checks=compare(rr,existing);report['comparison']=checks
        report['counts']=dict(Counter(c['status'] for c in checks))
        missing={c['reference_id'] for c in checks if c['status']=='missing'}
        (OUT/'solo_referencias_ausentes.csl.json').write_text(json.dumps([csl(r) for r in rr if r['reference_id'] in missing],ensure_ascii=False,indent=2)+'\n')
        (OUT/'solo_referencias_ausentes.ris').write_text('\n'.join(ris(r) for r in rr if r['reference_id'] in missing))
    (OUT/'estado_preparacion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report if not args.existing else {k:v for k,v in report.items() if k!='comparison'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
