"""Populate the revised DOCX page-index caches using its rendered PDF.

The DOCX is patched as a ZIP; it is never saved through a layout engine.
Render once more and rerun to verify that all displayed page labels are stable.
"""
import argparse
import json
import re
import unicodedata
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree as E
import pypdfium2 as pdfium

REPO=Path(__file__).resolve().parents[3]
OUT=REPO/'development/editorial/revision'
DOCX=REPO/'Documents/Informe_Final_AssistiveVision.docx'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W=NS['w']
def q(s):return '{'+W+'}'+s
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKD',s).lower() if c.isalnum())
def roman(n):
    result=''
    for v,s in [(1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),(100,'C'),(90,'XC'),(50,'L'),(40,'XL'),(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]:
        while n>=v:result+=s;n-=v
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('pdf',type=Path);a=p.parse_args()
    pdf=pdfium.PdfDocument(str(a.pdf))
    pages=[pdf[i].get_textpage().get_text_range() for i in range(len(pdf))]
    body_start=next(i for i,t in enumerate(pages) if 'identificarelmobiliarioylosobjetos' in norm(t))
    nav=json.loads((OUT/'navegacion.json').read_text())
    # Header labels are the authority: odd section breaks may insert unnumbered physical pages.
    labels={}
    for i,t in enumerate(pages):
        if i<body_start:labels[i]=roman(i+1);continue
        top=' '.join(t.splitlines()[:3])
        m=re.search(r'^(\d+)\s+AssistiveVision|^AssistiveVision\s+(\d+)',top)
        if m:labels[i]=str(int(m[1] or m[2]))
    for i in range(body_start,len(pages)):
        if i not in labels:
            # A first section page can have its first-page header suppressed.
            later=next((j for j in range(i+1,len(pages)) if j in labels),None)
            earlier=next((j for j in range(i-1,body_start-1,-1) if j in labels),None)
            if later is not None:labels[i]=str(int(labels[later])-(later-i))
            elif earlier is not None:labels[i]=str(int(labels[earlier])+(i-earlier))
            else:raise ValueError('Cannot identify page label '+str(i+1))
    mapping={}
    for entry in nav:
        candidates=[i for i in range(body_start,len(pages)) if norm(entry['text']) in norm(pages[i])]
        if entry['text']=='Referencias':
            candidates=[i for i in candidates if any(norm(line)==norm('Referencias') for line in pages[i].splitlines())]
        if not candidates:raise ValueError('Heading/caption not found: '+entry['text'])
        i=candidates[0]
        mapping[entry['name']]=dict(text=entry['text'],physical_page=i+1,label=labels[i])
    with ZipFile(DOCX) as z:parts={n:z.read(n) for n in z.namelist()}
    root=E.fromstring(parts['word/document.xml'])
    for field in root.xpath('//w:fldSimple',namespaces=NS):
        m=re.search(r'PAGEREF\s+(\w+)',field.get(q('instr'),''))
        if m and m[1] in mapping:
            texts=field.xpath('.//w:t',namespaces=NS)
            if len(texts)!=1:raise ValueError('Unexpected page-field structure')
            texts[0].text=mapping[m[1]]['label']
    prelim={}
    for title in ['Resumen','Abstract','Contenido','Lista de figuras','Lista de tablas','Lista de símbolos']:
        indexes=[i for i in range(body_start) if any(norm(line)==norm(title) for line in pages[i].splitlines())]
        if not indexes:raise ValueError('Preliminary title not found: '+title)
        prelim[title]=roman(indexes[0]+1)
    for pnode in root.findall('.//w:body/w:p',NS):
        text=''.join(pnode.xpath('.//w:t/text()',namespaces=NS))
        for title,label in prelim.items():
            if text.startswith(title) and pnode.find('.//'+q('tab')) is not None and pnode.find('.//'+q('fldSimple')) is None:
                runs=pnode.findall(q('r'))
                texts=runs[-1].xpath('.//w:t',namespaces=NS) if runs else []
                if texts:texts[-1].text=label
    parts['word/document.xml']=E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
    with ZipFile(DOCX,'w',ZIP_DEFLATED) as z:
        for n,data in parts.items():z.writestr(n,data)
    result=dict(pages=len(pages),body_physical_page=body_start+1,prelim=prelim,entries=mapping)
    (OUT/'paginacion_verificada.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('Updated',len(mapping),'page-reference caches from',len(pages),'rendered pages.')

if __name__=='__main__':main()
