"""Apply the reviewed attribution corrections, then number references by first citation.

Input: constructor output with the original35 reference identifiers.
Already revised49-entry documents are left unchanged. No sources are invented or fetched.
"""
from pathlib import Path
from copy import deepcopy
import json,re
from difflib import SequenceMatcher
from zipfile import ZipFile,ZIP_DEFLATED
from lxml import etree as E

W='http://schemas.openxmlformats.org/wordprocessingml/2006/main';NS={'w':W};tag=lambda s:'{'+W+'}'+s
HERE=Path(__file__).resolve().parent

def apply_revision(path):
    path=Path(path)
    with ZipFile(path) as z:parts={n:z.read(n) for n in z.namelist()}
    root=E.fromstring(parts['word/document.xml']);body=root.find('w:body',NS)
    def text(p):return ''.join(p.xpath('.//w:t/text()',namespaces=NS))
    refs={int(m.group(1)):p for p in body.findall('w:p',NS) if (m:=re.match(r'^\[(\d+)\]\s',text(p)))}
    if len(refs)==49:
        print('Attribution revision already applied.');return
    assert set(refs)==set(range(1,36)), 'Expected original35 references before attribution revision.'
    # Flatten citation links before changing their numeric identities.
    for p in body.findall('w:p',NS):
        for link in list(p.findall('w:hyperlink',NS)):
            if p not in refs.values() and not link.get(tag('anchor'),'').startswith('bib_ref_'):continue
            index=p.index(link)
            for i,child in enumerate(list(link)):p.insert(index+i,child)
            p.remove(link)
    ids={a.get(tag('id')) for a in root.findall('.//w:bookmarkStart',NS) if a.get(tag('name'),'').startswith('bib_ref_')}
    for kind in ['bookmarkStart','bookmarkEnd']:
        for element in list(root.findall('.//w:'+kind,NS)):
            if element.get(tag('id')) in ids:element.getparent().remove(element)
    revision=json.loads((HERE/'citation_revision.json').read_text())
    def replace(p,old,new):
        s=text(p);start=s.index(old)
        # Edit from the end so the unchanged words retain their existing run styles.
        for action,a,b,c,d in reversed(SequenceMatcher(None,old,new,autojunk=False).get_opcodes()):
            if action=='equal':continue
            left=start+a;right=start+b;value=new[c:d]
            ts=p.findall('.//w:t',NS);offset=0;started=False
            for t in ts:
                chunk=t.text or '';lo=offset;hi=offset+len(chunk);offset=hi
                if left==right:
                    if not started and lo<=left<=hi:
                        pos=left-lo;t.text=chunk[:pos]+value+chunk[pos:];started=True
                    continue
                if hi<=left or lo>=right:continue
                t.text=chunk[:max(0,left-lo)]+(value if not started else '')+chunk[max(0,right-lo):];started=True
                t.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
            assert started,(action,a,b)
        assert text(p)==s.replace(old,new,1)
    for edit in revision['edits']:
        matches=[p for p in body.findall('w:p',NS) if text(p)==edit['old']]
        assert len(matches)==1,edit['old'][:100]
        replace(matches[0],edit['old'],edit['new'])
    for p in body.findall('w:p',NS):
        if text(p).startswith('La memoria se reporta como la huella aproximada'):
            for italic in p.findall('.//w:i',NS)+p.findall('.//w:iCs',NS):italic.set(tag('val'),'0')
    sample=deepcopy(refs[1]);last=refs[35]
    def settext(p,s):
        for child in list(p):
            if child.tag!=tag('pPr'):p.remove(child)
        run=E.SubElement(p,tag('r'));E.SubElement(run,tag('t')).text=s
    for number,s in revision['references'].items():
        n=int(number)
        if n not in refs:
            p=deepcopy(sample);last.addnext(p);last=p;refs[n]=p
        settext(refs[n],f'[{n}] {s}')
    order=[]
    for p in body.iter(tag('p')):
        if p in refs.values():continue
        for m in re.finditer(r'\[(\d+)\]',text(p)):
            n=int(m.group(1));assert n in refs,(n,text(p))
            if n not in order:order.append(n)
    assert set(order)==set(refs),('Uncited references',set(refs)-set(order))
    numbering={n:i+1 for i,n in enumerate(order)}
    for p in body.iter(tag('p')):
        if p in refs.values():continue
        for t in p.findall('.//w:t',NS):
            if t.text:t.text=re.sub(r'\[(\d+)\]',lambda m:f'[{numbering[int(m.group(1))]}]',t.text)
    anchor=refs[1].getprevious()
    for p in refs.values():body.remove(p)
    for old in order:
        p=refs[old];s=text(p);settext(p,re.sub(r'^\[\d+\]',f'[{numbering[old]}]',s));anchor.addnext(p);anchor=p
        pr=p.find('w:pPr',NS)
        if pr is None:pr=E.Element(tag('pPr'));p.insert(0,pr)
        keep=pr.find('w:keepLines',NS)
        if keep is None:keep=E.SubElement(pr,tag('keepLines'))
        keep.set(tag('val'),'1')
    # Keep the source note with the final row of the spatial-zone table.
    for p in body.findall('w:p',NS):
        if text(p)=='Tabla 3.2. Zonas de localización espacial y descriptores asociados.':
            table=p.getnext();rows=table.findall('w:tr',NS)
            for cellp in rows[-1].findall('.//w:p',NS):
                pr=cellp.find('w:pPr',NS)
                if pr is None:pr=E.Element(tag('pPr'));cellp.insert(0,pr)
                keep=pr.find('w:keepNext',NS)
                if keep is None:keep=E.SubElement(pr,tag('keepNext'))
                keep.set(tag('val'),'1')
    parts['word/document.xml']=E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
    with ZipFile(path,'w',ZIP_DEFLATED) as z:
        for n,data in parts.items():z.writestr(n,data)
    mapping={str(old):new for old,new in numbering.items()}
    (HERE/'citation_number_map.json').write_text(json.dumps(mapping,indent=2)+'\n')
    print(f'Applied{len(revision["edits"])} paragraph corrections;{len(refs)} references ordered by first citation.')

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('docx',type=Path);apply_revision(p.parse_args().docx)
