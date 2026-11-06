"""Revise the annotated tutor attachment while preserving untouched DOCX parts.

Usage: python development/editorial/scripts/revise_tutor_feedback.py SOURCE.docx
The historical manuscript and experimental data are never overwritten.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from difflib import SequenceMatcher
import hashlib
import html
import json
from pathlib import Path
from os.path import relpath
import re
import unicodedata
from zipfile import ZipFile, ZIP_DEFLATED

from lxml import etree as E
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT

from tutor_revision_content import (
    TITLE, REPLACEMENTS, REFERENCES, NOTATION_ROWS, SCENE_ROWS, CONFIG_ROWS,
    PHYSICAL_FIELD, PAIRED_CAPTURE, FOV, MATCHING, COVERAGE, AUDIO, ANNEX,
    scoped_replacements, INTRO_OBJECTIVES, MODEL_SELECTION_CRITERION, CONCLUSION_MODEL,
)

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / 'development/editorial/revision'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
NS = {'w': W, 'r': R}
def q(tag): return '{'+W+'}'+tag
def txt(node): return ''.join(node.xpath('.//w:t/text()', namespaces=NS))
def norm(s): return ''.join(c for c in unicodedata.normalize('NFKD',s).lower() if c.isalnum())
def sha(b): return hashlib.sha256(b).hexdigest()

class Revision:
    def __init__(self, source):
        self.source = Path(source)
        with ZipFile(source) as z:
            self.parts = {n:z.read(n) for n in z.namelist()}
        self.root = E.fromstring(self.parts['word/document.xml'])
        self.body = self.root.find(q('body'))
        self.original = deepcopy(self.root)
        self.ps = self.body.findall(q('p'))
        if len(self.ps) != 542 or txt(self.ps[476]) != 'Anexo A: Scripts de evaluación de modelos':
            raise ValueError('Use the annotated attachment supplied on 2026-11-05, not a rebuilt manuscript.')
        self.orig_text = {i:txt(p) for i,p in enumerate(self.ps)}
        self.node_ids = {id(p):i for i,p in enumerate(self.ps)}
        self.styles = E.fromstring(self.parts['word/styles.xml'])
        self.style_ids = {s.find(q('name')).get(q('val')).lower():s.get(q('styleId'))
                          for s in self.styles.findall(q('style')) if s.find(q('name')) is not None}
        self.logs = []
        self.additions = []
        self.cited = set()
        self.refs = self.prepare_refs()
        self.bookmark_id = 2000
        self.rels = E.fromstring(self.parts['word/_rels/document.xml.rels'])
        self.rel_id = 2000
        self.url_ids = {}
        self.report_images = []

    def prepare_refs(self):
        refs = {k:dict(author=a, year=y, entry=e) for k,(a,y,e) in REFERENCES.items()}
        grouped = defaultdict(list)
        for k,v in refs.items():
            grouped[v['author'],v['year']].append(k)
        for (author,year),ids in grouped.items():
            if len(ids)>1:
                for index,k in enumerate(sorted(ids,key=lambda k:norm(refs[k]['entry'].split('*')[1]))):
                    suffix=chr(97+index)
                    refs[k]['year']=year+'-'+suffix if year=='s. f.' else year+suffix
                    refs[k]['entry']=refs[k]['entry'].replace('('+year+')','('+refs[k]['year']+')',1)
        return refs

    def ppr(self,p):
        pr=p.find(q('pPr'))
        if pr is None: pr=E.Element(q('pPr'));p.insert(0,pr)
        return pr

    def setstyle(self,p,name):
        pr=self.ppr(p); s=pr.find(q('pStyle'))
        if s is None:s=E.SubElement(pr,q('pStyle'))
        s.set(q('val'),self.style_ids.get(name.lower(),name))

    def run(self,p,text,italic=False,bold=False,font=None,size=None,highlight=False,link=None):
        parent=p
        if link:
            parent=E.SubElement(p,q('hyperlink'))
            if link.startswith('#'):parent.set(q('anchor'),link[1:])
            else:
                if link not in self.url_ids:
                    rid='rIdTutor'+str(self.rel_id);self.rel_id+=1
                    rel=E.SubElement(self.rels,'{http://schemas.openxmlformats.org/package/2006/relationships}Relationship')
                    rel.set('Id',rid);rel.set('Type',R+'/hyperlink');rel.set('Target',link);rel.set('TargetMode','External')
                    self.url_ids[link]=rid
                parent.set('{'+R+'}id',self.url_ids[link])
        r=E.SubElement(parent,q('r'))
        props=E.SubElement(r,q('rPr'))
        for name,flag in [('i',italic),('b',bold)]:
            if flag:E.SubElement(props,q(name))
        if font:
            f=E.SubElement(props,q('rFonts'));f.set(q('ascii'),font);f.set(q('hAnsi'),font)
        if size:E.SubElement(props,q('sz')).set(q('val'),str(int(size*2)))
        if highlight:E.SubElement(props,q('highlight')).set(q('val'),'yellow')
        color=E.SubElement(props,q('color'));color.set(q('val'),'000000')
        t=E.SubElement(r,q('t'));t.set('{http://www.w3.org/XML/1998/namespace}space','preserve');t.text=text
        return r

    def rich(self,p,s):
        italic=False
        for chunk in re.split(r'(\*)',s):
            if chunk=='*':italic=not italic;continue
            for item in re.split(r'(https?://[^\s]+)',chunk):
                if not item:continue
                self.run(p,item,italic=italic,link=item if item.startswith('http') else None)

    def settext(self,p,s,style=None):
        for child in list(p):
            if child.tag not in (q('pPr'),q('bookmarkStart'),q('bookmarkEnd')):p.remove(child)
        if style:self.setstyle(p,style)
        self.run(p,s)

    def edit(self,index,s):
        p=self.ps[index];before=txt(p)
        if before==s:return
        self.settext(p,s)
        self.logs.append(dict(source_paragraph=index,before=before,after=s))

    def para(self,s,style='Normal',kind='p'):
        p=E.Element(q('p'));self.setstyle(p,style)
        pr=self.ppr(p)
        spacing=E.SubElement(pr,q('spacing'));spacing.set(q('after'),'200');spacing.set(q('line'),'360');spacing.set(q('lineRule'),'auto')
        if style=='Normal':E.SubElement(pr,q('jc')).set(q('val'),'both')
        if kind=='code':
            spacing.set(q('line'),'240');spacing.set(q('after'),'60')
            self.run(p,s,font='Liberation Mono',size=9)
        elif kind=='download':
            links={'Descargar APK':'https://github.com/diomedescerda/AssistiveVision/releases/latest/download/AssistiveVision-1.0-debug.apk',
                   'Versiones y comprobantes':'https://github.com/diomedescerda/AssistiveVision/releases/latest'}
            for chunk in re.split(r'(Descargar APK|Versiones y comprobantes)',s):
                if chunk:
                    run=self.run(p,chunk,link=links.get(chunk))
                    if chunk in links:E.SubElement(run.find(q('rPr')),q('u')).set(q('val'),'single')
        else:self.run(p,s)
        self.additions.append(s)
        return p

    def h(self,s,level=2):return self.para(s,'Heading '+str(level))

    def caption(self,s):
        p=self.para(s,'Caption')
        pr=self.ppr(p);E.SubElement(pr,q('keepNext'))
        return p

    def placeholder(self,s):
        p=self.para('[INSERTAR IMAGEN DEL AUTOR: '+s+']')
        p.find(q('r')).find(q('rPr')).append(E.Element(q('i')))
        return p

    def picture(self, name, width, description, crop=None):
        """Embed a new inline figure without rewriting existing package media."""
        path=REPO/'Documents/Figures'/name
        scratch=Document()
        paragraph=scratch.add_paragraph()
        shape=paragraph.add_run().add_picture(str(path),width=Inches(width))
        p=E.fromstring(E.tostring(paragraph._p))
        self.setstyle(p,'Normal')
        pr=self.ppr(p)
        E.SubElement(pr,q('jc')).set(q('val'),'center')
        spacing=E.SubElement(pr,q('spacing'));spacing.set(q('after'),'80')
        E.SubElement(pr,q('keepNext'))
        E.SubElement(pr,q('keepLines'))
        blip=p.xpath('.//*[local-name()="blip"]')[0]
        source_id=blip.get('{'+R+'}embed')
        media=scratch.part.related_parts[source_id]
        if crop:
            # Native Word crop: retain the complete, unmodified source screenshot.
            left,top,right,bottom=crop
            iw,ih=media.image.px_width,media.image.px_height
            if not (0 <= left < right <= iw and 0 <= top < bottom <= ih):
                raise ValueError('Crop rectangle falls outside the source image.')
            crop_node=E.Element('{http://schemas.openxmlformats.org/drawingml/2006/main}srcRect')
            for side,value,total in [('l',left,iw),('t',top,ih),('r',iw-right,iw),('b',ih-bottom,ih)]:
                crop_node.set(side,str(round(value/total*100000)))
            blip.addnext(crop_node)
            height=round(Inches(width)*(bottom-top)/(right-left))
            for extent in p.xpath('.//*[local-name()="extent" or (local-name()="ext" and @cx)]'):
                extent.set('cy',str(height))
        target='media/report_'+Path(name).name
        self.parts['word/'+target]=media.blob
        rid='rIdReportImage'+str(len(self.report_images)+1)
        relationship=E.SubElement(self.rels,'{http://schemas.openxmlformats.org/package/2006/relationships}Relationship')
        relationship.set('Id',rid);relationship.set('Type',R+'/image');relationship.set('Target',target)
        blip.set('{'+R+'}embed',rid)
        properties=p.xpath('.//*[local-name()="docPr"]')[0]
        properties.set('id',str(4000+len(self.report_images)))
        properties.set('name',name);properties.set('descr',description)
        types=E.fromstring(self.parts['[Content_Types].xml'])
        content_ns='http://schemas.openxmlformats.org/package/2006/content-types'
        extension=path.suffix[1:].lower()
        if not any(n.get('Extension')==extension for n in types):
            element=E.SubElement(types,'{'+content_ns+'}Default')
            element.set('Extension',extension);element.set('ContentType','image/jpeg' if extension in ('jpg','jpeg') else 'image/png')
        self.parts['[Content_Types].xml']=E.tostring(types,xml_declaration=True,encoding='UTF-8',standalone=True)
        self.report_images.append(dict(file=str(path.relative_to(REPO)),sha256=sha(media.blob),relationship=rid,description=description,word_crop_box_pixels=crop))
        return p

    def harness_figure(self):
        ledger=json.loads((REPO/'Documents/Figures/fuentes_fotograficas.json').read_text())
        sources=ledger['harnesses']['sources']
        stick=ledger['selfie_stick']
        panels=[]
        for entry,width in [(sources[0],1.8),(sources[1],1.8),(stick,1.1)]:
            if sha((REPO/entry['source']).read_bytes()) != entry['sha256']:
                raise ValueError('Harness source screenshot changed: '+entry['source'])
            name=str(Path(entry['source']).relative_to('Documents/Figures'))
            panels.append(self.picture(name,width,entry['title']+'; ilustración comercial de referencia.',entry['word_crop_box_pixels']))
        # Explicit centered tab stops keep every image and its label in its column.
        def columns(p):
            pr=self.ppr(p)
            ind=E.SubElement(pr,q('ind'))
            for key in ('left','right','firstLine'):ind.set(q(key),'0')
            pr.find(q('jc')).set(q('val'),'left')
            tabs=E.SubElement(pr,q('tabs'))
            for position in (1440,4320,7200):
                tab=E.SubElement(tabs,q('tab'));tab.set(q('val'),'center');tab.set(q('pos'),str(position))
        columns(panels[0])
        first_tab=E.Element(q('r'));E.SubElement(first_tab,q('tab'))
        panels[0].insert(1,first_tab)
        for panel in panels[1:]:
            E.SubElement(E.SubElement(panels[0],q('r')),q('tab'))
            for run in list(panel):
                if run.tag==q('r'):panels[0].append(run)
        labels=self.para('')
        columns(labels)
        for text in ('(a) Cabeza','(b) Pecho Innovo+','(c) Palo de selfie'):
            E.SubElement(E.SubElement(labels,q('r')),q('tab'))
            self.run(labels,text,size=10)
        E.SubElement(self.ppr(labels),q('keepNext'))
        source=self.para('Fuente: ilustraciones comerciales de Mercado Libre: ')
        self.run(source,'Soporte de cabeza + accesorio para celular',link=sources[0]['url'])
        self.run(source,' y ')
        self.run(source,'Arnés Pecho Innovo+ para GoPro y celulares',link=sources[1]['url'])
        self.run(source,'; eMAG: ')
        self.run(source,'palo de selfie con trípode de diseño L01',link=stick['url'])
        self.run(source,'. El diseño del panel (c) fue identificado por semejanza con el utilizado. Las imágenes no documentan la colocación experimental ni acreditan la marca exacta del palo de selfie.')
        return [panels[0],labels,source]

    def correct_mount_terminology(self):
        """Correct presentation labels; archived keys and source media stay intact."""
        for p in self.body.xpath('.//w:p',namespaces=NS):
            before=txt(p)
            if not re.search('gorillapod',before,re.I):continue
            english=before.startswith('AssistiveVision was designed')
            after=before.replace('soporte flexible Gorillapod','palo de selfie extensible con patas plegables de trípode')
            if not english:
                for old,new in [('Para Gorillapod','Para el palo de selfie'),('de Gorillapod','del palo de selfie'),('con Gorillapod','con el palo de selfie'),('favorece provisionalmente Gorillapod','favorece provisionalmente el palo de selfie')]:
                    after=after.replace(old,new)
            after=re.sub('gorillapod','the selfie stick with tripod' if english else 'palo de selfie',after,flags=re.I)
            if after.startswith('palo de selfie'):after='P'+after[1:]
            after=re.sub(r'([.!?] )palo de selfie',r'\1El palo de selfie',after)
            if 'patas plegables de trípode' in after:
                after+=' En las tablas y figuras se abrevia como «palo de selfie».'
            self.settext(p,after)
        # Relabel from the same saved inputs; preserve the historical embedded media.
        corrected={'rId40':'montajes_cajas.png','rId41':'configuraciones_cajas.png','rId43':'seleccion_metricas.png'}
        for rel in self.rels:
            if rel.get('Id') in corrected:
                name=corrected[rel.get('Id')]
                rel.set('Target','media/corrected_'+name)
                self.parts['word/media/corrected_'+name]=(REPO/'Documents/Figures'/name).read_bytes()

    def table(self,rows,widths):
        # Build only the new table, then transplant its OOXML into the source package.
        d=Document();t=d.add_table(rows=0,cols=len(rows[0]));t.autofit=False
        t.alignment=WD_TABLE_ALIGNMENT.CENTER
        for i,w in enumerate(widths):t.columns[i].width=Inches(w)
        for i,row in enumerate(rows):
            cells=t.add_row().cells
            for j,s in enumerate(row):
                cells[j].width=Inches(widths[j]);cells[j].vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                p=cells[j].paragraphs[0];p.paragraph_format.space_after=Pt(4);p.paragraph_format.space_before=Pt(4);p.paragraph_format.line_spacing=1.05
                r=p.add_run(s);r.font.name='Arial';r.font.size=Pt(9);r.bold=i==0
                if i==0:
                    sh=E.SubElement(cells[j]._tc.get_or_add_tcPr(),q('shd'));sh.set(q('fill'),'E7E6E6')
            pr=E.SubElement(t.rows[-1]._tr,q('trPr'));E.SubElement(pr,q('cantSplit'))
            if i==0:E.SubElement(pr,q('tblHeader'))
        props=t._tbl.tblPr
        borders=E.SubElement(props,q('tblBorders'))
        for edge in ['top','left','bottom','right','insideH','insideV']:
            e=E.SubElement(borders,q(edge));e.set(q('val'),'single');e.set(q('sz'),'4');e.set(q('color'),'D9D9D9')
        margins=E.SubElement(props,q('tblCellMar'))
        for edge in ['top','left','bottom','right']:
            e=E.SubElement(margins,q(edge));e.set(q('w'),'70');e.set(q('type'),'dxa')
        return deepcopy(t._tbl)

    def segment(self,a,b):
        children=list(self.body)
        return children[children.index(self.ps[a]):children.index(self.ps[b])]

    def comments(self):
        result=[]
        root=E.fromstring(self.parts.get('word/comments.xml',b'<x/>'))
        for c in root.findall(q('comment')):
            cid=c.get(q('id'))
            anchored=self.original.xpath('//w:p[.//w:commentRangeStart[@w:id="'+cid+'"]]',namespaces=NS)
            result.append(dict(id=cid,author=c.get(q('author')),comment=txt(c),anchor=' | '.join(txt(p) for p in anchored)))
        return result

    def assemble(self):
        replacements=scoped_replacements(self.orig_text)
        for i,s in replacements.items():self.edit(i,s)
        self.edit(3,TITLE);self.edit(25,TITLE)
        self.edit(382,REPLACEMENTS[383])
        self.edit(383,self.orig_text[383])
        E.SubElement(self.ppr(self.ps[25]),q('pageBreakBefore'))
        E.SubElement(self.ppr(self.ps[476]),q('pageBreakBefore'))
        # Metric labels are uniform for aggregate results; per-class AP50 stays AP50.
        for p in self.body.findall(q('p'))[178:493]:
            s=txt(p);new=s
            if not re.search(r'(Desglose de AP50|AP50 por cada clase)',s):
                new=re.sub(r'(?<![A-Za-z])AP50', 'mAP50',new)
            new=new.replace('MS COCO','COCO').replace('F1 score','F1').replace('F1 Score','F1')
            if p in self.ps[362:463]:
                new=new.replace('por escena','por grupo').replace('33 escenas','33 grupos').replace('29 escenas','29 grupos').replace('Escenas +','Grupos +').replace('Escenas +','Grupos +')
            new=new.replace('escenario 1','análisis de montajes').replace('escenario 2','análisis de montaje y lente').replace('escenario 3','análisis de distancia')
            new=new.replace('Escenario 1','Montajes').replace('Escenario 2','Montaje y lente').replace('Escenario 3','Distancia estimada')
            new=new.replace('de las secciones 2.1','de las secciones 2.2').replace('sección 2.1','sección 2.2')
            new=new.replace('en las secciones 2.1','en las secciones 2.2')
            if p not in self.ps[442:447]:
                new=re.sub(r'(Tabla|tabla) 4\.(10|[1-9])(?!\d)',lambda m:m[1]+' 4.'+str(int(m[2])+2),new)
            if p in self.ps[442:447] and 'Tabla 4.8' in new:new=new.replace('Tabla 4.8','Tabla 4.10')
            # Two new photos precede the four existing chapter-4 plots.
            new=re.sub(r'(Figura|figura) 4\.([1-4])(?!\d)',lambda m:m[1]+' 4.'+str(int(m[2])+2),new)
            if new!=s:self.settext(p,new)
        self.settext(self.ps[244],REPLACEMENTS[244])
        # These rewritten paragraphs already cite the new numbers, whereas the
        # surrounding source paragraphs still needed their old numbers shifted.
        self.settext(self.ps[366],replacements[366])
        self.settext(self.ps[393],REPLACEMENTS[393])
        self.setstyle(self.ps[251],'Heading 2')
        tables=self.body.findall(q('tbl'))
        for ti,t in enumerate(tables):
            for p in t.xpath('.//w:p',namespaces=NS):
                s=txt(p);new=s
                if ti!=1:new=re.sub(r'(?<![A-Za-z])AP50','mAP50',new)
                if ti==9:
                    new=new.replace('Escenario','Análisis').replace('4.2 Posiciones del arnés','4.2 Montajes').replace('4.3 Arnés y lente','4.3 Montaje y lente').replace('4.4 Profundidad de detección','4.4 Distancia estimada').replace('t pareada por escena','t pareada por grupo').replace('bootstrap de grupos','bootstrap de grupos')
                if ti>=9:new=new.replace('escena','grupo').replace('Escenas','Grupos')
                if new!=s:self.settext(p,new)
        # Domain-specific acronym introductions at their first narrative occurrence.
        self.edit(317,self.orig_text[317].replace('RGBA_8888','RGBA_8888 (rojo, verde, azul y alfa, con ocho bits por canal)'))
        self.edit(337,self.orig_text[337].replace('VITS/Piper','Variational Inference with adversarial learning for end-to-end Text-to-Speech (VITS) y Piper'))
        self.edit(261,txt(self.ps[261]).replace('8 GB','8 gigabytes (GB)'))
        self.edit(263,txt(self.ps[263]).replace('RAM LPDDR4X','RAM de bajo consumo de cuarta generación extendida (LPDDR4X, low power double data rate 4X)'))
        self.edit(445,txt(self.ps[445]).replace('JPEG reproducidos','archivos del estándar Joint Photographic Experts Group (JPEG) reproducidos'))
        self.edit(454,'El etiquetado suplementario se apoyó en inteligencia artificial (IA). '+txt(self.ps[454]))
        self.edit(408,txt(self.ps[408]).replace('del EXIF','de los metadatos EXIF').replace('—calculada del campo','—calculada del campo'))
        # Reassemble existing nodes. Tables and figures travel with their paragraphs.
        front=self.segment(0,178)
        intro=[self.ps[178],*self.ps[179:182],self.ps[183],self.para(INTRO_OBJECTIVES),
               self.ps[192],self.ps[194],self.ps[199],self.ps[201],self.ps[202]]
        # Introductory prose uses the original body rhythm, without subheadings.
        for p in intro:
            if p is self.ps[178] or p is self.ps[202]:continue
            self.setstyle(p,'Normal')
        ch1=[self.ps[203],self.ps[204],self.h('1.1 Detección de objetos y métricas de evaluación'),
             self.para('Una red neuronal profunda (DNN, deep neural network) aprende representaciones para asignar clases y localizar objetos en una imagen. La detección produce cajas, clases y puntuaciones; esas puntuaciones ordenan la confianza del modelo y no se interpretan como probabilidades calibradas de acierto. La evaluación compara predicciones con una referencia anotada mediante las reglas siguientes.'),
             *self.ps[243:251],self.caption('Tabla 1.1. Notación y unidades de lectura.'),self.table(NOTATION_ROWS,[1.35,4.45]),
             self.para('Nota. El punto decimal de los archivos equivale a la coma decimal del texto. Los intervalos de confianza y los grados de libertad se explican al presentar el método estadístico.'),
             *self.ps[205:224],self.ps[233],self.ps[251],self.ps[252],self.ps[253],self.ps[254],self.ps[258],self.ps[234],self.ps[235]]
        # DETR belongs with the architectural comparison, not an isolated final subsection.
        ch1.remove(self.ps[233]);ch1.insert(ch1.index(self.ps[217]),self.ps[233])
        ch2=[self.ps[236],self.ps[237],*self.ps[195:198],*self.ps[238:241],*self.ps[224:232],
             *self.ps[259:268],self.ps[255],self.ps[256],self.ps[257],*self.segment(268,307)]
        criterion=self.para(MODEL_SELECTION_CRITERION)
        E.SubElement(self.ppr(criterion),q('keepLines'))
        ch2.insert(ch2.index(self.ps[290]),criterion)
        ch3=self.segment(307,362)
        loc=self.para('Las cajas del modelo usan coordenadas normalizadas [ymin, xmin, ymax, xmax] sobre la imagen con relleno. Esa representación se convierte al fotograma original antes de aplicar las reglas anteriores; no debe confundirse con [x, y, w, h] de la anotación. El descriptor «frente a ti» corresponde a la región inferior central y no acredita ausencia de obstáculos o distancia segura. Los límites descritos corresponden a LocalizationModule en la revisión evaluada [34].')
        ch3.insert(ch3.index(self.ps[328]),loc)
        at=ch3.index(self.ps[353])
        ch3[at:at]=[self.caption('Figura 3.4. Pantallas de captura y configuración de AssistiveVision.'),
                     self.picture('interfaz_app.png',5.55,'Dos capturas reales de AssistiveVision: vista previa con captura manual y configuración de audio, confianza, número de objetos y vista previa.'),
                     self.para('Fuente: capturas del autor de AssistiveVision en un emulador Android, en español, con confianza 0,30 y hasta dos objetos. La escena virtual de la vista previa ilustra la interfaz y no pertenece al conjunto experimental.')]
        # Correct the source figure-caption paragraph, independent of split-run text.
        for p in ch3:
            if p.tag==q('p') and txt(p).startswith('Figura 3.2'):
                self.settext(p,'Figura 3.2. Regiones de la imagen para la localización relativa.')
        ch4=[self.ps[362],self.ps[363],self.ps[364],self.ps[365],self.ps[366],
             self.para(PHYSICAL_FIELD),self.caption('Tabla 4.1. Tipologías observables y ejemplos de grupos.'),
             self.table(SCENE_ROWS,[1.2,1.25,3.35]),
             self.para('Nota. G01 significa grupo de captura 1. Las categorías provienen de labels.json para las seis fotografías de cada grupo citado; una clase puede estar visible solo en algunas vistas. Los ejemplos no cuentan recintos físicos únicos ni prueban que las seis fotografías tengan un encuadre idéntico.'),
             self.caption('Figura 4.1. Ejemplos de espacios y condiciones de captura.'),
             self.picture('escenas_ejemplo.png',5.8,'Seis fotografías originales de dormitorio, sala y comedor, cocina, baño, espacio de trabajo y terraza; cada panel identifica el grupo y el archivo.'),
             self.para('Fuente: fotografías del autor conservadas en Build/Testing/data/. Se muestran ejemplos de los grupos G01, G03, G04, G06, G27 y G28, con la imagen completa y sin superponer detecciones. Las etiquetas identifican el grupo y el archivo; no cuentan recintos físicos únicos.'),
             self.ps[367],self.ps[368],self.caption('Tabla 4.2. Orden y tamaño de las configuraciones de captura.'),
             self.table(CONFIG_ROWS,[1.0,2.6,1.05,1.15]),self.para(PAIRED_CAPTURE),self.para(FOV),
             self.caption('Figura 4.2. Montajes usados para orientar la cámara.'),
             *self.harness_figure(),
             self.ps[369],self.ps[370],self.para(MATCHING),self.ps[371],self.ps[372],self.para(COVERAGE),
             self.ps[373],self.ps[374],*self.segment(375,462)]
        # Define EXIF before its use in distance and validity analyses.
        for p in ch4:
            if p.tag==q('p') and txt(p)==FOV:
                self.settext(p,FOV.replace('los metadatos','los metadatos del formato intercambiable de archivos de imagen (EXIF, exchangeable image file format)',1))
        for kind,s in AUDIO:ch4.append(self.h(s) if kind=='h2' else self.para(s))
        # The original section break belongs after all of chapter 4, including
        # its requested audio clarification, so chapter 5 starts on its own page.
        ch4.append(self.ps[462])
        concl=[self.ps[463],self.para(CONCLUSION_MODEL),*self.ps[465:470],self.ps[471],self.ps[473],self.ps[474],self.ps[475]]
        annex=[self.ps[476]]
        self.setstyle(self.ps[476],'Heading 1')
        for kind,s in ANNEX:
            if kind=='h2':annex.append(self.h(s))
            elif kind=='code':
                lines=s.splitlines()
                for index,line in enumerate(lines):
                    p=self.para(line.removeprefix('+'),kind='code')
                    if index+1<len(lines):E.SubElement(self.ppr(p),q('keepNext'))
                    annex.append(p)
            else:annex.append(self.para(s,kind=kind))
        # Preserve the original final section break before the bibliography.
        annex.append(self.ps[491])
        bib=[self.ps[492]]
        self.setstyle(self.ps[492],'Heading 1')
        refpr=self.ppr(self.ps[492])
        spacing=refpr.find(q('spacing'))
        if spacing is None:spacing=E.SubElement(refpr,q('spacing'))
        spacing.set(q('before'),'0');spacing.set(q('after'),'240')
        align=refpr.find(q('jc'))
        if align is None:align=E.SubElement(refpr,q('jc'))
        align.set(q('val'),'center')
        for run in self.ps[492].findall(q('r')):
            rp=run.find(q('rPr'))
            if rp is None:rp=E.SubElement(run,q('rPr'))
            E.SubElement(rp,q('sz')).set(q('val'),'24')
            E.SubElement(rp,q('b'))
        for k in sorted(self.refs,key=lambda k:norm(self.refs[k]['entry'])):
            p=self.para('');self.rich(p,self.refs[k]['entry'])
            pr=self.ppr(p);ind=E.SubElement(pr,q('ind'));ind.set(q('left'),'720');ind.set(q('hanging'),'720')
            pr.find(q('jc')).set(q('val'),'left')
            spacing=pr.find(q('spacing'));spacing.set(q('line'),'480');spacing.set(q('after'),'0')
            E.SubElement(pr,q('keepLines'))
            self.add_bookmark(p,'tutor_ref_'+str(k))
            self.node_ids[id(p)]=492+k
            bib.append(p)
        final_section=self.body.find(q('sectPr'))
        for child in list(self.body):self.body.remove(child)
        for child in [*front,*intro,*ch1,*ch2,*ch3,*ch4,*concl,*annex,*bib,final_section]:
            if child is not None:self.body.append(child)
        self.scope_text={i:txt(p) for i,p in enumerate(self.ps) if p.getparent() is self.body}
        self.original_comments=self.comments()
        self.cleanup()
        self.correct_mount_terminology()
        self.convert_citations()
        self.update_navigation()
        self.parts['word/_rels/document.xml.rels']=E.tostring(self.rels,xml_declaration=True,encoding='UTF-8',standalone=True)

    def cleanup(self):
        # Reviewer comments are preserved in the comparison, removed from the clean copy.
        for node in self.root.xpath('//w:commentRangeStart|//w:commentRangeEnd|//w:commentReference|//w:lastRenderedPageBreak|//w:highlight',namespaces=NS):
            node.getparent().remove(node)
        for p in self.body.findall(q('p')):
            s=txt(p)
            if 'JPEG' in s and 'Joint Photographic Experts Group' not in s:
                self.settext(p,s.replace('JPEG','archivos del estándar Joint Photographic Experts Group (JPEG)',1));s=txt(p)
            if s=='Tabla 4.7. Comparación de conteos con Gorillapod 0,5x.':
                spacing=self.ppr(p).find(q('spacing'))
                if spacing is not None:spacing.set(q('before'),'0');spacing.set(q('after'),'80')
            # First expansion of IA in running text (software brand GPT is a model name).
            if 'etiquetas suplementarias asistidas por IA' in s:
                self.settext(p,s.replace('asistidas por IA','asistidas por inteligencia artificial (IA)',1))
            # References to the three old annexes must not survive consolidation.
            s=txt(p).replace('los anexos','el anexo').replace('Los anexos','El anexo')
            if s!=txt(p):self.settext(p,s)
        # Keep the original page system and normalize black headings without theme overrides.
        for s in self.styles.findall(q('style')):
            name=s.find(q('name'))
            if name is None:continue
            if name.get(q('val'),'').lower() in ['heading 1','heading 2','heading 3','title','subtitle','caption','títulos posteriores']:
                rp=s.find(q('rPr'))
                if rp is None:rp=E.SubElement(s,q('rPr'))
                color=rp.find(q('color'))
                if color is None:color=E.SubElement(rp,q('color'))
                color.attrib.clear();color.set(q('val'),'000000')
        for p in self.body.findall(q('p')):
            pr=p.find(q('pPr'));style=pr.find(q('pStyle')) if pr is not None else None
            if style is not None and style.get(q('val')) in [self.style_ids.get('heading 1'),self.style_ids.get('heading 2'),self.style_ids.get('heading 3')]:
                for c in p.xpath('.//w:color',namespaces=NS):c.attrib.clear();c.set(q('val'),'000000')
        # Use consecutive page numbering; odd-page section starts introduced invisible
        # parity pages and jumps in the source's rendered folios.
        for section in self.root.xpath('//w:sectPr',namespaces=NS):
            typ=section.find(q('type'))
            if typ is not None and typ.get(q('val'))=='oddPage':typ.set(q('val'),'nextPage')
        # The original comments are retained in their JSON ledger and comparison, rather
        # than orphaned in the clean Word package.
        comment_parts=[k for k in self.parts if re.match(r'word/comments[^/]*\.xml$',k)]
        for k in comment_parts:del self.parts[k]
        for rel in list(self.rels):
            if 'comment' in rel.get('Type','').lower():self.rels.remove(rel)
        types=E.fromstring(self.parts['[Content_Types].xml'])
        for item in list(types):
            if item.get('PartName','').lstrip('/') in comment_parts:types.remove(item)
        self.parts['[Content_Types].xml']=E.tostring(types,xml_declaration=True,encoding='UTF-8',standalone=True)
        settings=E.fromstring(self.parts['word/settings.xml'])
        update=settings.find(q('updateFields'))
        if update is None:update=E.SubElement(settings,q('updateFields'))
        update.set(q('val'),'true')
        self.parts['word/settings.xml']=E.tostring(settings,xml_declaration=True,encoding='UTF-8',standalone=True)
        self.parts['word/styles.xml']=E.tostring(self.styles,xml_declaration=True,encoding='UTF-8',standalone=True)

    def convert_citations(self):
        # Convert every numeric citation to an author–date hyperlink, including table notes.
        for p in self.body.xpath('.//w:p',namespaces=NS):
            s=txt(p)
            if not re.search(r'\[\d{1,2}\]',s):continue
            if s.startswith('[1, 448') or s.startswith('[') and 'INSERTAR' in s:continue
            # Preserve source sentences while adding the dates required by APA.
            narrative_names={2:'More et al.',3:'Meenakshi et al.',4:'Guravaiah et al.',
                             13:'Pawar',14:'Figura, Kuźmiczuk y Badurowicz',15:'Howard et al.',
                             16:'Sandler et al.',17:'Dai',18:'Magdy et al.'}
            for k,name in narrative_names.items():
                if f'[{k}]' not in s:continue
                pattern=r'(?<!\w)'+re.escape(name)+r'(?!\w| \(\d{4}\))'
                narrative=self.refs[k]['author'].replace(' & ',' y ')+' ('+self.refs[k]['year']+')'
                s=re.sub(pattern,lambda m:narrative,s,count=1)
            # Adjacent numeric references become one alphabetized parenthetical citation.
            pattern=r'\[\d{1,2}\](?:(?:\s*,\s*|\s+y\s+|\s*;\s*)\[\d{1,2}\])*'
            chunks=[];pos=0
            for m in re.finditer(pattern,s):
                ids=[int(x) for x in re.findall(r'\d+',m[0])]
                if any(k not in self.refs for k in ids):continue
                chunks.append(('text',s[pos:m.start()]))
                # Avoid duplicate dates when the paragraph already has a narrative citation.
                active=[]
                for k in ids:
                    self.cited.add(k)
                    author=self.refs[k]['author'];year=self.refs[k]['year']
                    narrative=author.replace(' & ',' y ')+' ('+year+')'
                    if narrative not in s[:m.start()]:active.append(k)
                if active:chunks.append(('cite',sorted(set(active),key=lambda k:norm(self.refs[k]['author'])+self.refs[k]['year'])))
                pos=m.end()
            chunks.append(('text',s[pos:]))
            merged=[]
            for kind,value in chunks:
                if kind=='text' and merged and merged[-1][0]=='text':
                    merged[-1]=('text',merged[-1][1]+value)
                else:merged.append((kind,value))
            chunks=merged
            for child in list(p):
                if child.tag not in (q('pPr'),q('bookmarkStart'),q('bookmarkEnd')):p.remove(child)
            for kind,value in chunks:
                if kind=='text':self.run(p,value)
                else:
                    self.run(p,'(')
                    for j,k in enumerate(value):
                        if j:self.run(p,'; ')
                        self.run(p,self.refs[k]['author']+', '+self.refs[k]['year'],link='#tutor_ref_'+str(k))
                    self.run(p,')')
            # Remove spaces before punctuation left after a duplicate narrative citation.
            for t in p.xpath('.//w:t',namespaces=NS):
                if t.text:t.text=re.sub(r' +([.,;])(?=\s|$)',r'\1',t.text)

    def add_bookmark(self,p,name):
        start=E.Element(q('bookmarkStart'));start.set(q('id'),str(self.bookmark_id));start.set(q('name'),name)
        end=E.Element(q('bookmarkEnd'));end.set(q('id'),str(self.bookmark_id));self.bookmark_id+=1
        index=1 if p.find(q('pPr')) is not None else 0
        p.insert(index,start);p.append(end)

    def update_navigation(self):
        # Replace the hand-written TOCs, retaining their paragraph styles and tab leaders.
        # Physical pagination is populated only from a verified rendering by the refresh helper.
        pstyles={k:self.style_ids.get(k.lower(),k) for k in ['Heading 1','Heading 2','Heading 3']}
        nav=[]
        intro_index=list(self.body).index(self.ps[178])
        for index,p in enumerate(self.body.findall(q('p'))):
            s=txt(p);pr=p.find(q('pPr'));style=pr.find(q('pStyle')) if pr is not None else None
            sid=style.get(q('val')) if style is not None else ''
            level=next((i for i in [1,2] if sid==pstyles['Heading '+str(i)]),None)
            iscaption=re.match(r'^(Figura|Tabla) \d+\.\d+\.',s)
            if (level or iscaption) and list(self.body).index(p)>=intro_index:
                name='tutor_nav_'+str(len(nav)+1);self.add_bookmark(p,name)
                nav.append(dict(text=s,name=name,kind='heading' if level else iscaption[1],level=level or 0))
        sections=[('Contenido','Lista de figuras','heading'),('Lista de figuras','Lista de tablas','Figura'),('Lista de tablas','Lista de símbolos','Tabla')]
        for title,nexttitle,kind in sections:
            ps=self.body.findall(q('p'))
            start=next(p for p in ps if txt(p).strip()==title and self.body.index(p)<intro_index)
            end=next(p for p in ps if txt(p).strip()==nexttitle and self.body.index(p)>self.body.index(start))
            nodes=list(self.body)[self.body.index(start)+1:self.body.index(end)]
            # Preserve the section break at the end of each preliminary section.
            sep=[n for n in nodes if n.find('.//'+q('sectPr')) is not None]
            sample=next((n for n in nodes if n.tag==q('p') and n.find(q('pPr')) is not None and n not in sep),None)
            if sample is None:sample=self.para('')
            ppr=deepcopy(sample.find(q('pPr')))
            for n in nodes:
                if n not in sep:self.body.remove(n)
            entries=[n for n in nav if n['kind']==kind]
            if kind=='heading':
                entries=[dict(text=t,name='',kind='prelim',level=1) for t in ['Resumen','Abstract','Contenido','Lista de figuras','Lista de tablas','Lista de símbolos']]+entries
            anchor=start
            # Retain a visible page-column heading from the source convention.
            lead=self.para('Pág.');lead.find(q('pPr')).append(E.Element(q('keepNext')))
            start.addnext(lead);anchor=lead
            for entry in entries:
                p=E.Element(q('p'))
                if ppr is not None:p.append(deepcopy(ppr))
                pr=self.ppr(p)
                for k in ['sectPr','pageBreakBefore','keepNext','numPr']:
                    for n in pr.findall(q(k)):pr.remove(n)
                sp=pr.find(q('spacing'))
                if sp is None:sp=E.SubElement(pr,q('spacing'))
                sp.set(q('before'),'0');sp.set(q('after'),'45');sp.set(q('line'),'240')
                ind=pr.find(q('ind'))
                if ind is None:ind=E.SubElement(pr,q('ind'))
                ind.set(q('left'),'180' if entry.get('level')==2 else '0')
                self.run(p,entry['text'],size=9,bold=entry.get('level')==1,link='#'+entry['name'] if entry['name'] else None)
                r=E.SubElement(p,q('r'));E.SubElement(r,q('tab'))
                if entry['name']:
                    field=E.SubElement(p,q('fldSimple'));field.set(q('instr'),' PAGEREF '+entry['name']+' \\h ')
                    self.run(field,'1',size=9)
                else:self.run(p,'I',size=9)
                anchor.addnext(p);anchor=p
        self.navigation=nav

    def save(self,path):
        self.parts['word/document.xml']=E.tostring(self.root,xml_declaration=True,encoding='UTF-8',standalone=True)
        with ZipFile(path,'w',ZIP_DEFLATED) as z:
            for n,data in self.parts.items():z.writestr(n,data)

    def validate(self):
        text='\n'.join(txt(p) for p in self.body.findall(q('p')))
        checks={
            'approved_title_on_both_covers':txt(self.ps[3])==TITLE and txt(self.ps[25])==TITLE,
            'no_numeric_body_citations':not bool(re.search(r'(?<!\d)\[\d{1,2}\]',text)),
            'all_49_references_used':self.cited==set(range(1,50)),
            'one_annex':len([p for p in self.body.findall(q('p')) if txt(p).startswith('Anexo ')])==2, # TOC + body
            'no_conclusion_subheadings':not bool(re.search(r'5\.[123] (Conclusiones|Recomendaciones|Trabajo)',text)),
            'no_separate_conceptual_framework':'Marco conceptual' not in text,
            'audio_limit_explicit':'No se evaluaron pronunciación inglesa, tasa de comprensión o claridad con participantes' in text,
            'physical_space_author_field_explicit':PHYSICAL_FIELD in text,
            'no_image_placeholders':not any(txt(p).startswith('[INSERTAR IMAGEN') for p in self.body.findall(q('p'))),
            'ui_scenes_and_three_mounts_embedded':{Path(i['file']).name for i in self.report_images}=={'interfaz_app.png','escenas_ejemplo.png','arnes_cabeza_fuente.png','arnes_pecho_fuente.png','palo_selfie_L01_referencia.jpg'},
            'no_obsolete_mount_name_in_report':not re.search('gorillapod',text,re.I),
            'clean_copy_has_no_comment_anchors':not self.root.xpath('//w:commentRangeStart|//w:commentReference',namespaces=NS),
            'original_7_figures_preserved':all(E.tostring(n) in {E.tostring(d) for d in self.root.xpath('//w:drawing',namespaces=NS)} for n in self.original.xpath('//w:drawing',namespaces=NS)),
            'objectives_integrated_in_introductory_prose':INTRO_OBJECTIVES in text and all(self.ps[i].getparent() is None for i in [186,188,189,190]),
            'unrequested_paragraph_rewrites_removed':all(self.scope_text[i]==self.orig_text[i] for i in [179,181,192,196,197,199,207,210,211,216,225,246,250,254,255,257,305,307,314,318,355,469,471,473,474]),
            'source_file_extension_spacing_preserved':all(' .tflite' in txt(self.ps[i]) for i in [231,254]),
        }
        # All original data values must survive; only metric labels and design prose may change.
        old_tables=self.original.xpath('//w:body/w:tbl',namespaces=NS)
        new_tables=self.body.findall(q('tbl'))
        def values(t):return re.findall(r'-?\d+(?:[.,]\d+)?',txt(t))
        remaining=list(new_tables)
        preserved=[]
        for i,t in enumerate(old_tables):
            match=next((x for x in remaining if values(x)==values(t)),None)
            # The source design table changes language only, keeping its numeric units.
            preserved.append(match is not None)
            if match is not None:remaining.remove(match)
        checks['all_19_source_tables_numeric_values_unchanged']=all(preserved)
        bookmark_names=set(self.root.xpath('//w:bookmarkStart/@w:name',namespaces=NS))
        anchors=self.root.xpath('//w:hyperlink/@w:anchor',namespaces=NS)
        checks['internal_links_resolve']=all(a in bookmark_names for a in anchors)
        with ZipFile(self.source) as source:
            checks['image_parts_byte_identical']=all(self.parts[k]==source.read(k) for k in source.namelist() if k.startswith('word/media/'))
            checks['headers_and_footers_byte_identical']=all(self.parts[k]==source.read(k) for k in source.namelist() if re.match(r'word/(header|footer)\d+\.xml$',k))
        return dict(checks=checks,source_sha256=sha(self.source.read_bytes()),
                    report_images=self.report_images,
                    references=len(self.refs),cited_reference_ids=sorted(self.cited),
                    paragraphs=len(self.body.findall(q('p'))),tables=len(new_tables),
                    sections=len(self.root.xpath('//w:sectPr',namespaces=NS)),
                    comments_addressed=len(self.original_comments),
                    failed=[k for k,v in checks.items() if not v])

    def comparison(self,path,output=None):
        newps=self.body.findall(q('p'));newtext=[txt(p) for p in newps]
        used_source={id(p) for p in newps}
        source_order={id(p):i for i,p in enumerate(newps)}
        cases=[];heading='Preliminares'
        skip_before=178
        for p in newps:
            s=txt(p)
            pr=p.find(q('pPr'));style=pr.find(q('pStyle')) if pr is not None else None
            if style is not None and style.get(q('val'))==self.style_ids['heading 1']:heading=s
            idx=self.node_ids.get(id(p))
            if self.body.index(p)<self.body.index(self.ps[178]) and idx not in [3,25,60,63]:continue
            if idx is not None and idx<skip_before and idx not in [3,25,60,63]:continue
            before=self.orig_text.get(idx,'')
            if s==before or not s.strip():continue
            cases.append((heading,'Reescrito' if idx is not None else 'Agregado',before,s))
        used_indexes={self.node_ids.get(id(p)) for p in newps}
        deleted=[(i,t) for i,t in self.orig_text.items() if i>=178 and t.strip() and i not in used_indexes]
        comments=self.original_comments
        disposition={
            '0':'Título de ambas portadas tomado literalmente de la propuesta; métricas uniformes e índices regenerados.',
            '7':'Aporte integrado en prosa de la introducción y vinculado a los hallazgos de las conclusiones.',
            '6':'Introducción sin subtítulos; objetivos, alcance y límites se conectan en párrafos.',
            '19':'Párrafo introductorio de antecedentes ampliado; se conserva la redacción original de los estudios del capítulo 1.',
            '21':'Los objetivos se integran en un párrafo de propósito; el alcance de la evaluación auditiva se explica en el capítulo 4, sin añadir una justificación en la introducción.',
            '25':'Metodología trasladada al inicio del capítulo 2.',
            '33':'Candidatos trasladados a la sección 2.3 y distinguidos de los seis modelos ejecutados.',
            '35':'DETR integrado en la comparación de arquitecturas, sin apartado aislado.',
            '41':'Métricas y notación integradas con antecedentes en la sección 1.1.',
            '42':'IoU, AP y mAP explicadas antes de usarse en los resultados.',
            '43':'mAP50-95 explica promedio entre clases y entre diez umbrales; AP50 se conserva por clase.',
            '44':'Secuencia de cajas, conteos, precisión, recall y F1 con ejemplo numérico explícitamente ilustrativo.',
            '45':'Precisión explicada con pregunta, fórmula, denominador y ejemplo de TP/FP/FN.',
            '54':'Se explica por qué la latencia es decisiva para la espera previa al mensaje de voz; la comparación y la selección explicitan el compromiso aceptado de mAP50-95 frente a los candidatos YOLO.',
            '75':'Capturas reales de las pantallas de captura y configuración insertadas en Figura 3.4; se identifica la escena virtual del emulador como ilustración de interfaz.',
            '83':'Capítulo 4 reorganizado; dos emparejamientos diferenciados y sección 4.9 para el alcance auditivo.',
            '85':'Emparejar capturas y emparejar cajas se explican como operaciones diferentes.',
            '86':'Diseño explicado como 33 grupos × 6 fotografías = 198, con cautela sobre agrupación provisional.',
            '87':'Cobertura, desempeño del detector y selección para voz separados explícitamente.',
            '90':'Tipologías y ejemplos derivados de imágenes y etiquetas; campo editable para el inventario físico que completará el autor.',
            '119':'Conclusiones en prosa, organizadas por los tres objetivos y el objetivo general.',
            '121':'Transiciones explícitas entre selección, integración y evaluación.',
            '122':'Cantidad especificada como número de instancias correctamente detectadas.',
            '127':'Un único anexo con contenido, versiones y comandos de reproducción.',
            '131':'Instrucciones de instalación y uso situadas en README; desaparecen los manuales separados.',
        }
        def esc(x):return html.escape(str(x))
        def diff(a,b):
            aa=re.findall(r'\s+|\S+',a);bb=re.findall(r'\s+|\S+',b);left=[];right=[]
            for op,i,j,k,l in SequenceMatcher(None,aa,bb,autojunk=False).get_opcodes():
                sa=esc(''.join(aa[i:j]));sb=esc(''.join(bb[k:l]))
                left.append('<del>'+sa+'</del>' if op in ['delete','replace'] else sa)
                right.append('<ins>'+sb+'</ins>' if op in ['insert','replace'] else sb)
            return ''.join(left),''.join(right)
        cards=[]
        for index,(section,kind,before,after) in enumerate(cases,1):
            a,b=diff(before,after)
            cards.append(f'<details class="change" data-search="{esc(section+" "+before+" "+after).lower()}"><summary><span>{kind}</span> {esc(section)} · {index}</summary><div class="cols"><div><h4>Antes</h4><p>{a or "—"}</p></div><div><h4>Después</h4><p>{b}</p></div></div></details>')
        ledger=''.join(f'<details><summary>Comentario {esc(c["id"])} · {esc(c["comment"][:105])}</summary><p><b>Tutora:</b> {esc(c["comment"])}</p><p><b>Aplicación:</b> {esc(disposition.get(c["id"],"Revisado en el documento."))}</p></details>' for c in comments)
        removed=''.join(f'<details><summary>Párrafo original {i} · {esc(t[:100])}</summary><p>{esc(t)}</p><p>Eliminado de su ubicación original o sustituido por una explicación integrada. Los subtítulos y anexos retirados no se conservan como secciones independientes.</p></details>' for i,t in deleted)
        movements=[('Introducción','Párrafos conectados, sin subtítulos'),('Métricas y notación','Capítulo 1, sección 1.1'),('DETR','Sección 1.3, comparación de arquitecturas'),('Metodología general','Inicio del capítulo 2'),('Modelos candidatos','Sección 2.3'),('Evaluación de audio','Sección 4.9 con alcance real de la evidencia'),('Tres anexos','Un anexo único de repositorios y reproducción')]
        outline=''.join('<tr><td>'+esc(a)+'</td><td>'+esc(b)+'</td></tr>' for a,b in movements)
        page='''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Revisión del tutor AssistiveVision</title><style>
body{font:16px/1.6 system-ui,sans-serif;color:#182b37;background:#f6f7f8;margin:0}main{max-width:1120px;margin:auto;padding:32px 22px 70px}h1{font-size:30px;line-height:1.2}h2{font-size:23px;margin-top:32px}p{max-width:90ch}.intro{font-size:18px}details{background:white;border:1px solid #cbd5dc;border-radius:5px;margin:10px 0;padding:13px 17px}summary{cursor:pointer;font-weight:600}summary span{font-size:12px;background:#e5eef5;padding:3px 6px;margin-right:7px}table{border-collapse:collapse;width:100%;background:white}td,th{border:1px solid #ccd5dd;padding:10px;text-align:left}.cols{display:grid;grid-template-columns:1fr 1fr;gap:20px}.cols>div{min-width:0}h4{margin-bottom:5px}del{background:#ffe4e1;color:#80342d}ins{background:#dff1e5;color:#194d30;text-decoration:none}input{padding:12px;width:min(500px,90%);font-size:16px;border:1px solid #8c9da9;border-radius:4px}button{margin:5px;padding:10px 12px;background:white;border:1px solid #8c9da9;border-radius:4px;cursor:pointer}.notice{border-left:4px solid #ac6c14;padding:8px 18px;background:#fff6e4}.muted{color:#506570;font-size:14px}a{color:#125e91}.change[hidden]{display:none}@media(max-width:720px){.cols{grid-template-columns:1fr}main{padding:22px 14px}}
</style><main><p class="muted">AssistiveVision · revisión del 5 de noviembre de 2026</p><h1>Qué cambió y por qué</h1><p class="intro">Comparación editorial con el archivo comentado por la tutora. El documento revisado conserva resultados y figuras, reorganiza la exposición y explicita el alcance de la evidencia.</p>
<p><a href="../../../Documents/Informe_Final_AssistiveVision.docx">Abrir el Word revisado</a> · <a href="README.md">Leer instrucciones de reproducción y uso</a></p>
<div class="notice"><b>Campos que completará el autor.</b> Identificación exacta de recintos y criterio de captura. La interfaz, seis fotografías originales de ejemplo y las ilustraciones comerciales de los arneses de cabeza y pecho ya están insertadas. No se inventan participantes ni ensayos de audio. La ausencia de una medición de claridad se integra como límite del tercer objetivo, no como un resultado positivo.</div>
<h2>Cambios de estructura</h2><table><thead><tr><th>Contenido</th><th>Ubicación revisada</th></tr></thead><tbody>'''+outline+'''</tbody></table>
<h2>Los 25 comentarios de la tutora</h2>'''+ledger+f'''<h2>Comparación del texto</h2><p>Se muestran {len(cases)} párrafos nuevos o modificados; el rojo marca lo retirado y el verde lo añadido. Los movimientos se resumen arriba. Los cambios de índices y paginación no se mezclan con el contenido científico.</p><input id="filter" placeholder="Buscar por capítulo o palabra" aria-label="Filtrar cambios"><button id="open">Expandir visibles</button><button id="close">Cerrar todos</button>'''+''.join(cards)+'''<h2>Elementos retirados de su ubicación original</h2>'''+removed+'''<h2>Revisión bibliográfica</h2><p>Las 49 referencias se presentan en orden alfabético, con autor y año, sangría francesa, títulos y publicaciones en cursiva y DOI como URL. Las citas numéricas se convierten al sistema autor–fecha y enlazan con su entrada. Se completan autores de trabajos abreviados y se distinguen documentos sin fecha. La presentación institucional de las páginas se conserva.</p><p>Se contrastó metadata editorial disponible con los PDF de literatura y registros DOI. El borrador CIPA y el preprint de Pawar se mantienen como tales. La normalización editorial no autentica las licencias de modelos o voces ni recupera los archivos ausentes del benchmark histórico.</p><p><a href="https://apastyle.apa.org/style-grammar-guidelines/citations/basic-principles/author-date">APA autor–fecha</a> · <a href="https://apastyle.apa.org/style-grammar-guidelines/references/examples/journal-article-references">APA referencias de artículos</a></p>
<h2>Integridad de la revisión</h2><p>Se conserva el archivo recibido. La revisión se construye con un script independiente y no sobrescribe los datos de evaluación ni el manuscrito histórico. Las cifras de las 19 tablas originales permanecen iguales. La validación estructural se conserva junto a los scripts y el informe.</p></main><script>
const changes=[...document.querySelectorAll('.change')];document.querySelector('#filter').addEventListener('input',e=>{const q=e.target.value.toLowerCase();changes.forEach(d=>d.hidden=!d.dataset.search.includes(q))});document.querySelector('#open').onclick=()=>changes.filter(d=>!d.hidden).forEach(d=>d.open=true);document.querySelector('#close').onclick=()=>document.querySelectorAll('details').forEach(d=>d.open=false);
</script></html>'''
        page=page.replace('body{font:', 'html{color-scheme:light}button,input{color:#182b37!important;background:white!important}input::placeholder{color:#536874}body{font:')
        page=page.replace('<h2>Los 25 comentarios de la tutora</h2>', '<details><summary>Aplicación de los 25 comentarios de la tutora</summary>')
        page=page.replace('<h2>Comparación del texto</h2>', '</details><h2>Comparación del texto</h2>')
        page=page.replace('<h2>Elementos retirados de su ubicación original</h2>', '<details><summary>Elementos retirados de su ubicación original</summary>')
        page=page.replace('<h2>Revisión bibliográfica</h2>', '</details><h2>Revisión bibliográfica</h2>')
        page=page.replace('<button id="open">', '<button id="previous">Anteriores</button><button id="next">Siguientes</button><span id="count" aria-live="polite"></span><button id="open">')
        page=page.replace("const changes=[...document.querySelectorAll('.change')];document.querySelector('#filter').addEventListener('input',e=>{const q=e.target.value.toLowerCase();changes.forEach(d=>d.hidden=!d.dataset.search.includes(q))});", "const changes=[...document.querySelectorAll('.change')];let offset=0;function show(){const q=document.querySelector('#filter').value.toLowerCase();const filtered=changes.filter(d=>d.dataset.search.includes(q));changes.forEach(d=>d.hidden=true);filtered.slice(offset,offset+12).forEach(d=>d.hidden=false);document.querySelector('#count').textContent=filtered.length?`${offset+1}–${Math.min(offset+12,filtered.length)} de ${filtered.length}`:'Sin coincidencias';}document.querySelector('#filter').addEventListener('input',()=>{offset=0;show()});document.querySelector('#previous').onclick=()=>{offset=Math.max(0,offset-12);show()};document.querySelector('#next').onclick=()=>{const n=changes.filter(d=>d.dataset.search.includes(document.querySelector('#filter').value.toLowerCase())).length;if(offset+12<n)offset+=12;show()};show();changes[4].open=true;")
        output=output or REPO/'Documents/Informe_Final_AssistiveVision.docx'
        page=page.replace('../../../Documents/Informe_Final_AssistiveVision.docx',Path(relpath(output,path.parent)).as_posix())
        path.write_text(page)
        return len(cases)

def main():
    global OUT
    a=argparse.ArgumentParser();a.add_argument('source',type=Path)
    a.add_argument('--output',type=Path,default=REPO/'Documents/Informe_Final_AssistiveVision.docx')
    a.add_argument('--evidence-dir',type=Path,default=OUT)
    args=a.parse_args();OUT=args.evidence_dir
    OUT.mkdir(parents=True,exist_ok=True)
    r=Revision(args.source);r.assemble()
    output=args.output
    if output.resolve()==args.source.resolve():raise ValueError('The annotated source must remain unchanged.')
    output.parent.mkdir(parents=True,exist_ok=True);r.save(output)
    validation=r.validate();validation['output_sha256']=sha(output.read_bytes())
    validation['comparison_paragraphs']=r.comparison(OUT/'Cambios_tutor_AssistiveVision.html',output)
    (OUT/'validacion_revision.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n')
    (OUT/'navegacion.json').write_text(json.dumps(r.navigation,ensure_ascii=False,indent=2)+'\n')
    (OUT/'referencias_apa.json').write_text(json.dumps(r.refs,ensure_ascii=False,indent=2)+'\n')
    (OUT/'comentarios_tutora.json').write_text(json.dumps(r.original_comments,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(validation,ensure_ascii=False,indent=2))
    if validation['failed']:raise SystemExit('Editorial validation failed; inspect before delivery.')

if __name__=='__main__':main()
