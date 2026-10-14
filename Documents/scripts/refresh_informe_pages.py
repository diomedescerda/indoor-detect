"""Populate PAGEREF caches from a verified PDF without re-saving through LibreOffice."""
import argparse
import json
import re
import unicodedata
import zipfile
from pathlib import Path
from lxml import etree as E
import pypdfium2 as pdfium

REPO=Path(__file__).resolve().parents[2]
DOCX=REPO/'Documents/Informe_Final_Trabajo_de_Grado_AssistiveVision.docx'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

def norm(s):return ''.join(c for c in unicodedata.normalize('NFKD',s).lower() if c.isalnum())

def roman(n):
    out=''
    for value,text in [(1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),(100,'C'),(90,'XC'),(50,'L'),(40,'XL'),(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]:
        while n>=value:out+=text;n-=value
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('pdf',type=Path);a=p.parse_args()
    pdf=pdfium.PdfDocument(str(a.pdf));pages=[page.get_textpage().get_text_range() for page in pdf]
    body_start=next(i for i,t in enumerate(pages) if norm('Introducción La discapacidad visual') in norm(t))
    labels={}
    for i,t in enumerate(pages):
        if i<body_start:labels[i]=roman(i+1);continue
        head=' '.join(t.splitlines()[:3])
        m=re.search(r'^(\d+)\s+AssistiveVision|^AssistiveVision\s+(\d+)',head)
        if m:labels[i]=str(int(m.group(1) or m.group(2)))
    for i in range(body_start,len(pages)):
        if i not in labels:
            j=next((j for j in range(i+1,len(pages)) if j in labels),None)
            if j is None:raise ValueError(f'No page label for physical page {i+1}')
            labels[i]=str(int(labels[j])-(j-i))
    bookmarks=json.loads((REPO/'Documents/scripts/informe_bookmarks.json').read_text())
    mapping={}
    prelim={'Resumen','Abstract','Contenido','Lista de figuras','Lista de tablas','Lista de símbolos'}
    for b in bookmarks:
        search=range(body_start) if b['text'] in prelim else range(body_start,len(pages))
        candidates=[i for i in search if norm(b['text']) in norm(pages[i])]
        if b['text']=='Bibliografía':
            candidates=[i for i in search if any(norm(line)==norm('Bibliografía') for line in pages[i].splitlines())]
        if b['text'] in prelim:
            exact=[i for i in candidates if any(norm(line)==norm(b['text']) for line in pages[i].splitlines())]
            if exact:candidates=exact
        if not candidates:raise ValueError('Heading/caption not found: '+b['text'])
        index=candidates[0];mapping[b['name']]=dict(text=b['text'],physical_page=index+1,label=labels[index])
    with zipfile.ZipFile(DOCX) as z:parts={n:z.read(n) for n in z.namelist()}
    root=E.fromstring(parts['word/document.xml'])
    for field in root.xpath('//w:fldSimple',namespaces=NS):
        instr=field.get('{'+NS['w']+'}instr','');m=re.search(r'PAGEREF\s+(\w+)',instr)
        if m:
            nodes=field.xpath('.//w:t',namespaces=NS)
            assert len(nodes)==1
            nodes[0].text=mapping[m.group(1)]['label']
            if re.fullmatch(r'[IVXLCDM]+',mapping[m.group(1)]['label']):
                # LibreOffice renders PAGEREF with Arabic numbers despite the ROMAN
                # switch. Keep these six stable preliminary labels literal for portability.
                parent=field.getparent();index=parent.index(field)
                for run in list(field):parent.insert(index,run);index+=1
                parent.remove(field)
    parts['word/document.xml']=E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
    with zipfile.ZipFile(DOCX,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in parts.items():z.writestr(name,data)
    (REPO/'Documents/scripts/informe_page_map.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n')
    print('Populated',len(mapping),'page-reference caches.')

if __name__=='__main__':main()
