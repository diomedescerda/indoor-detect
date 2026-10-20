"""Add navigable citations and source links without changing reference text or layout."""
from copy import deepcopy
from pathlib import Path
import re
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree as E

W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
P='http://schemas.openxmlformats.org/package/2006/relationships'
NS={'w':W,'r':R}
def tag(s):return '{'+W+'}'+s

def link_references(path):
    path=Path(path)
    with ZipFile(path) as z:parts={n:z.read(n) for n in z.namelist()}
    root=E.fromstring(parts['word/document.xml']);rels=E.fromstring(parts['word/_rels/document.xml.rels'])
    paragraphs=root.findall('.//w:body/w:p',NS)
    text=lambda p:''.join(p.xpath('.//w:t/text()',namespaces=NS))
    refs={int(m.group(1)):p for p in paragraphs if (m:=re.match(r'^\[(\d+)\]\s',text(p)))}
    assert refs and set(refs)==set(range(1,len(refs)+1)), 'References must be consecutive.'
    next_id=max([int(v) for v in root.xpath('//w:bookmarkStart/@w:id',namespaces=NS)]+[0])+1
    names=set(root.xpath('//w:bookmarkStart/@w:name',namespaces=NS))
    for n,p in refs.items():
        name=f'bib_ref_{n}'
        if name not in names:
            start=E.Element(tag('bookmarkStart'),{tag('id'):str(next_id),tag('name'):name})
            end=E.Element(tag('bookmarkEnd'),{tag('id'):str(next_id)})
            p.insert(1 if p.find(tag('pPr')) is not None else 0,start);p.append(end);next_id+=1
    targets={x.get('Target'):x.get('Id') for x in rels if x.get('Type','').endswith('/hyperlink')}
    all_ids={x.get('Id') for x in rels};counter=1
    def external(url):
        nonlocal counter
        if url not in targets:
            while f'rIdBib{counter}' in all_ids:counter+=1
            rid=f'rIdBib{counter}';counter+=1;all_ids.add(rid)
            E.SubElement(rels,'{'+P+'}Relationship',Id=rid,Type=R+'/hyperlink',Target=url,TargetMode='External');targets[url]=rid
        return targets[url]
    added_internal=added_external=0
    for p in paragraphs:
        reference=p in refs.values()
        pattern=r'https?://[^\s]+|10\.\d{4,9}/[^\s]+|arXiv:\d{4}\.\d{4,5}' if reference else r'\[(\d+)\]'
        for run in list(p.findall('w:r',NS)):
            ts=run.findall('w:t',NS)
            if len(ts)!=1 or len([c for c in run if c.tag!=tag('rPr')])!=1:continue
            s=ts[0].text or '';matches=list(re.finditer(pattern,s))
            if not matches:continue
            items=[];pos=0
            def segment(value):
                r=deepcopy(run);r.find('w:t',NS).text=value;r.find('w:t',NS).set('{http://www.w3.org/XML/1998/namespace}space','preserve');return r
            for m in matches:
                end=m.end();token=m.group()
                if reference:
                    token=token.rstrip('.,;');end=m.start()+len(token)
                    url=token if token.startswith('http') else ('https://arxiv.org/abs/'+token[6:] if token.startswith('arXiv:') else 'https://doi.org/'+token)
                    attrs={'{'+R+'}id':external(url)};added_external+=1
                else:
                    n=int(m.group(1))
                    if n not in refs:continue
                    attrs={tag('anchor'):f'bib_ref_{n}'};added_internal+=1
                if m.start()>pos:items.append(segment(s[pos:m.start()]))
                link=E.Element(tag('hyperlink'),attrs);link.set(tag('history'),'1');link.append(segment(token));items.append(link);pos=end
            if not items:continue
            if pos<len(s):items.append(segment(s[pos:]))
            index=p.index(run);p.remove(run)
            for offset,item in enumerate(items):p.insert(index+offset,item)
    parts['word/document.xml']=E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
    parts['word/_rels/document.xml.rels']=E.tostring(rels,xml_declaration=True,encoding='UTF-8',standalone=True)
    with ZipFile(path,'w',ZIP_DEFLATED) as z:
        for n,data in parts.items():z.writestr(n,data)
    print(f'Bibliography:{len(refs)} references; added{added_internal} internal citation links and{added_external} source links.')

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('docx',type=Path);link_references(p.parse_args().docx)
