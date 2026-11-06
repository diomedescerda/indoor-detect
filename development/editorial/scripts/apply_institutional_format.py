"""Apply the approved institutional layout and bind the saved Zotero library.

Works on a copy of the tutor-reviewed manuscript. Bibliography display text comes
from Zotero's saved APA export, never from a separately maintained reference list.
Word ADDIN fields embed the verified collection item URIs and CSL snapshots.
The desktop Zotero plugin is needed for subsequent interactive refreshes.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import uuid
from zipfile import ZipFile, ZIP_DEFLATED

from lxml import etree as E

ROOT = Path(__file__).resolve().parents[3]
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
NS = {'w': W, 'r': R}
q = lambda s: '{'+W+'}'+s
text = lambda p: ''.join(p.xpath('.//w:t/text()', namespaces=NS))
norm = lambda s: ''.join(c for c in unicodedata.normalize('NFKD', s).lower() if c.isalnum())
digest = lambda b: hashlib.sha256(b).hexdigest()


def child(p, tag, **attrs):
    found = p.find(q(tag))
    if found is None:
        found = E.SubElement(p, q(tag))
    for k, v in attrs.items():
        found.set(q(k), str(v))
    return found


def ppr(p):
    pr = p.find(q('pPr'))
    if pr is None:
        pr = E.Element(q('pPr')); p.insert(0, pr)
    return pr


def run(parent, value, *, italic=False, bold=False, size=None, font=None):
    r = E.SubElement(parent, q('r')); rp = E.SubElement(r, q('rPr'))
    if italic: child(rp, 'i')
    if bold: child(rp, 'b')
    if size: child(rp, 'sz', val=round(size*2))
    if font: child(rp, 'rFonts', ascii=font, hAnsi=font, cs=font)
    child(rp, 'color', val='000000')
    t = E.SubElement(r, q('t')); t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve'); t.text=value
    return r


def field_start(p, instruction):
    r = E.SubElement(p, q('r')); E.SubElement(r, q('fldChar')).set(q('fldCharType'), 'begin')
    # Short instruction runs avoid renderer/word-processor string limits.
    for pos in range(0, len(instruction), 240):
        r = E.SubElement(p, q('r')); t = E.SubElement(r, q('instrText'))
        t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve'); t.text=instruction[pos:pos+240]
    r = E.SubElement(p, q('r')); E.SubElement(r, q('fldChar')).set(q('fldCharType'), 'separate')


def field_end(p):
    r = E.SubElement(p, q('r')); E.SubElement(r, q('fldChar')).set(q('fldCharType'), 'end')


class FormatRevision:
    def __init__(self, source):
        self.source = source
        with ZipFile(source) as z: self.parts={n:z.read(n) for n in z.namelist()}
        self.original_parts=dict(self.parts)
        self.root=E.fromstring(self.parts['word/document.xml']); self.body=self.root.find(q('body'))
        self.styles=E.fromstring(self.parts['word/styles.xml'])
        self.rels=E.fromstring(self.parts['word/_rels/document.xml.rels'])
        self.logs=[]; self.fields=[]; self.used=set()
        self.original_tables=[text(t) for t in self.body.findall(q('tbl'))]
        self.mapping=json.loads((ROOT/'development/editorial/revision/Zotero/verificacion_importacion.json').read_text())['mapping']
        rows=json.loads((ROOT/'Documents/Referencias/biblioteca_sincronizada.csl.json').read_text())['items']
        by_key={r['id'].split('/')[-1]:r for r in rows}
        assert len(by_key)==49 and set(self.mapping.values())==set(by_key)
        self.items={int(k):dict(by_key[v]) for k,v in self.mapping.items()}
        assert all(i.get('author') for i in self.items.values()), 'Fix missing Zotero authors before generating the document.'
        self.uri={int(k):'http://zotero.org/users/19721030/items/'+v for k,v in self.mapping.items()}
        self.refinfo=json.loads((ROOT/'development/editorial/revision/referencias_apa.json').read_text())
        for k, item in self.items.items(): item['id']=self.uri[k]

    def paragraph(self, prefix):
        return next(p for p in self.body.findall(q('p'))
                    if p.find('.//'+q('fldSimple')) is None and text(p).startswith(prefix))

    def replace(self, p, old, new):
        before=text(p); assert old in before, old
        # These scoped layout/cross-reference edits are applied only to paragraphs
        # without citations or other inline fields.
        assert p.find('.//'+q('hyperlink')) is None and p.find('.//'+q('fldChar')) is None
        for c in list(p):
            if c.tag not in [q('pPr'), q('bookmarkStart'), q('bookmarkEnd')]: p.remove(c)
        run(p, before.replace(old,new))
        self.logs.append({'before':before,'after':text(p)})

    def add_reference(self, caption, sentence):
        cap=self.paragraph(caption); p=E.Element(q('p'))
        pr=ppr(p); child(pr,'spacing',after=120,line=360,lineRule='auto'); child(pr,'jc',val='both');child(pr,'keepNext')
        run(p,sentence)
        anchor=cap
        previous=cap.getprevious()
        if previous is not None and previous.find('.//'+q('drawing')) is not None:
            # Older plot captions follow their images; the prose reference belongs
            # before the image, so the image and its caption remain adjacent.
            anchor=previous;child(ppr(previous),'keepNext')
        anchor.addprevious(p)
        self.logs.append({'before':'','after':sentence})

    def layout(self):
        # Chapter 3 previously shared its section with chapter 2 and used a manual
        # page break; give it the same section system as the other chapters.
        h3=self.paragraph('3. Diseño e implementación')
        following_section=next(n.find('.//'+q('sectPr')) for n in list(self.body)[self.body.index(h3)+1:]
                               if n.find('.//'+q('sectPr')) is not None)
        sep=E.Element(q('p')); ppr(sep).append(deepcopy(following_section));h3.addprevious(sep)
        sections=self.root.xpath('//w:sectPr',namespaces=NS)
        assert len(sections)==12
        for i, s in enumerate(sections):
            mar=child(s,'pgMar',top=1440,bottom=1440,left=2041,right=1440)
            child(s,'pgSz',w=12240,h=15840)
            child(s,'type',val='oddPage' if i>=4 else 'nextPage')
            for tag in ['titlePg','headerReference','footerReference']:
                for n in s.findall(q(tag)):s.remove(n)
            pg=child(s,'pgNumType',fmt='upperRoman' if i<4 else 'decimal')
            pg.attrib.pop(q('start'),None)
            if i==4:pg.set(q('start'),'1')
        # Uniform running headers: page fields inherit Roman/Arabic numbering from
        # the section. Keep the original report's branding and bottom header rule.
        for name, even, empty in [('odd',False,False),('even',True,False),('empty',False,True)]:
            h=E.Element(q('hdr'),nsmap={'w':W});p=E.SubElement(h,q('p'))
            if not empty:
                pr=ppr(p);child(pr,'spacing',after=0,line=240,lineRule='auto')
                tabs=child(pr,'tabs');E.SubElement(tabs,q('tab'),{q('val'):'right',q('pos'):'8759'})
                borders=child(pr,'pBdr');E.SubElement(borders,q('bottom'),{q('val'):'single',q('sz'):'4',q('space'):'5',q('color'):'777777'})
                def page_number():
                    field_start(p,' PAGE ');run(p,'1',size=11,font='Arial');field_end(p)
                if even:page_number()
                else:run(p,'AssistiveVision',size=11,font='Arial')
                E.SubElement(E.SubElement(p,q('r')),q('tab'))
                if even:run(p,'AssistiveVision',size=11,font='Arial')
                else:page_number()
            self.new_part('word/header_institucional_'+name+'.xml',h,'header','application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml')
        footer=E.Element(q('ftr'),nsmap={'w':W});E.SubElement(footer,q('p'))
        self.new_part('word/footer_institucional_vacio.xml',footer,'footer','application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml')
        for i,s in enumerate(sections):
            for typ,name in [('default','odd'),('even','even')]:
                target='header_institucional_'+('empty' if i==0 else name)+'.xml'
                rid=self.rel_id(target)
                s.insert(0,E.Element(q('headerReference'),{q('type'):typ,'{'+R+'}id':rid}))
            s.insert(0,E.Element(q('footerReference'),{q('type'):'default','{'+R+'}id':self.rel_id('footer_institucional_vacio.xml')}))
            s.insert(0,E.Element(q('footerReference'),{q('type'):'even','{'+R+'}id':self.rel_id('footer_institucional_vacio.xml')}))
        for p in self.body.findall(q('p')):
            pr=ppr(p);style=pr.find(q('pStyle'));sid=style.get(q('val')) if style is not None else 'Normal';t=text(p)
            if not t and pr.find(q('sectPr')) is not None:
                # Section-marker scaffolding must not subtract inherited paragraph
                # spacing from the next chapter's 100-point title offset.
                child(pr,'spacing',before=0,after=0,line=20,lineRule='exact')
                for mark_props in pr.findall(q('rPr')):pr.remove(mark_props)
            if sid in ['Ttulo1','Ttulo2','Ttulo3']:
                spacing=child(pr,'spacing',line=240,lineRule='auto')
                if sid=='Ttulo1':
                    spacing.set(q('before'),'2000');spacing.set(q('after'),'480')
                    for n in pr.findall(q('pageBreakBefore')):pr.remove(n)
                else:
                    spacing.set(q('before'),'400');spacing.set(q('after'),'200')
                child(pr,'jc',val='left')
                child(pr,'ind',left=0,right=0,firstLine=0).attrib.pop(q('hanging'),None)
                for heading_run in p.xpath('.//w:r[.//w:t]',namespaces=NS):
                    rp=child(heading_run,'rPr')
                    child(rp,'rFonts',ascii='Arial',hAnsi='Arial',cs='Arial')
                    child(rp,'sz',val={'Ttulo1':40,'Ttulo2':32,'Ttulo3':28}[sid])
                    child(rp,'b')
            elif sid=='Normal' and t:
                sp=pr.find(q('spacing'));align=pr.find(q('jc'))
                # Only ordinary 1.5-spaced prose. Preserve code, figures, source
                # notes, tabbed panel labels, and bibliography paragraph rules.
                if sp is not None and sp.get(q('line'))=='360' and align is not None and align.get(q('val'))=='both':
                    sp.set(q('after'),'330')
        self.replace(self.paragraph('4 Evaluación técnica'),'4 Evaluación','4. Evaluación')
        self.replace(self.paragraph('Anexo Repositorio'),'Anexo Repositorio','Anexo A. Repositorio')
        # Repair figure references at the point of use, without relocating the
        # scientific discussion or adding claims about the images.
        p=self.paragraph('Las fotografías muestran dormitorios')
        old='; la Figura 4.1 muestra fotografías de ejemplo de estos espacios y la Figura 4.2 ilustra los arneses de cabeza y pecho y el palo de selfie con trípode'
        self.replace(p,old,'')
        self.add_reference('Figura 4.1.','La Figura 4.1 presenta ejemplos del conjunto fotográfico.')
        self.add_reference('Figura 4.2.','La Figura 4.2 ilustra los tres soportes utilizados.')
        p=self.paragraph('Cada posición reúne 66 fotografías')
        self.replace(p,'después de la Figura 4.3','al final de esta sección')
        p=self.paragraph('El palo de selfie supera significativamente')
        self.replace(p,'La figura siguiente muestra la dispersión de los conteos.','La Figura 4.3 muestra la dispersión de los conteos.')
        child(ppr(p),'keepNext');child(ppr(p),'keepLines')
        self.add_reference('Figura 4.4.','La Figura 4.4 muestra la distribución de conteos en las seis configuraciones.')
        self.add_reference('Figura 4.5.','La Figura 4.5 representa el recall por banda de distancia estimada y su intervalo bootstrap.')
        ref=self.paragraph('Referencias');pr=ppr(ref)
        child(pr,'spacing',before=0,after=200,line=360,lineRule='auto');child(pr,'jc',val='left')
        for r in ref.findall(q('r')):
            rp=child(r,'rPr');child(rp,'sz',val=28);child(rp,'b')
        # Headings retain their bookmarks. Update the corresponding TOC text too.
        for p in self.body.findall(q('p')):
            if p.find('.//'+q('fldSimple')) is None:continue
            for t in p.xpath('.//w:t',namespaces=NS):
                if t.text:
                    t.text=t.text.replace('4 Evaluación técnica','4. Evaluación técnica').replace('Anexo Repositorio','Anexo A. Repositorio')
        # The notation table fits on one full page; keep its caption and rows
        # together so it does not need a separate continuation heading.
        notation=self.body.findall(q('tbl'))[0]
        rows=notation.findall(q('tr'))
        for row_index,row in enumerate(rows):
            child(child(row,'trPr'),'cantSplit')
            for paragraph in row.xpath('.//w:p',namespaces=NS):
                if row_index<len(rows)-1:child(ppr(paragraph),'keepNext')

    def new_part(self,name,node,kind,content_type):
        self.parts[name]=E.tostring(node,xml_declaration=True,encoding='UTF-8',standalone=True)
        rid='rIdInstitutional'+str(len(self.rels)+1)
        E.SubElement(self.rels,'{'+REL+'}Relationship',Id=rid,Type=R+'/'+kind,Target=name.removeprefix('word/'))
        types=E.fromstring(self.parts['[Content_Types].xml'])
        E.SubElement(types,'{http://schemas.openxmlformats.org/package/2006/content-types}Override',PartName='/'+name,ContentType=content_type)
        self.parts['[Content_Types].xml']=E.tostring(types,xml_declaration=True,encoding='UTF-8',standalone=True)

    def rel_id(self,target):
        return next(r.get('Id') for r in self.rels if r.get('Target')==target)

    def item(self,rid,suppress=False):
        item={'id':self.uri[rid],'uris':[self.uri[rid]],'itemData':self.items[rid]}
        if suppress:item['suppress-author']=True
        return item

    def citation(self,p,visible,ids,suppress=False):
        # The OpenCL source has a dated Zotero record (2013), not an undated one.
        if 32 in ids:visible=visible.replace('Khronos Group, s. f.','Khronos Group, 2013')
        code={'citationID':uuid.uuid4().hex[:10], 'properties':{'formattedCitation':visible,'plainCitation':visible,'noteIndex':0},
              'citationItems':[self.item(i,suppress) for i in ids],
              'schema':'https://github.com/citation-style-language/schema/raw/master/csl-citation.json'}
        field_start(p,' ADDIN ZOTERO_ITEM CSL_CITATION '+json.dumps(code,ensure_ascii=False,separators=(',',':'))+' ')
        run(p,visible);field_end(p)
        self.fields.append({'text':visible,'reference_ids':ids,'suppress_author':suppress});self.used.update(ids)

    def citations(self):
        bib=self.paragraph('Referencias');index=self.body.index(bib)
        for p in self.body.xpath('.//w:p',namespaces=NS):
            # Bibliography paragraphs are replaced separately from Zotero's HTML.
            top=p
            while top.getparent() is not self.body and top.getparent() is not None:top=top.getparent()
            if top.getparent() is not self.body or self.body.index(top)>=index:continue
            t=text(p);ranges=[];linkspans=[];position=0
            for n in p:
                s=text(n)
                if n.tag==q('hyperlink') and n.get(q('anchor'),'').startswith('tutor_ref_'):
                    linkspans.append((position,position+len(s),int(n.get(q('anchor')).split('_')[-1])))
                position+=len(s)
            for m in re.finditer(r'\([^()\n]{1,800}\)',t):
                ids=[rid for a,b,rid in linkspans if m.start()<=a and b<=m.end()]
                if ids:ranges.append((m.start(),m.end(),ids,False))
            for a,b,rid in linkspans:
                assert any(x<=a and b<=y for x,y,*_ in ranges),('Unpaired citation',t[a:b])
            for rid,meta in self.refinfo.items():
                for author in set([meta['author'],meta['author'].replace(' & ',' y ')]):
                    pat=re.escape(author)+r' (\('+re.escape(meta['year'])+r'\))'
                    for m in re.finditer(pat,t):
                        a,b=m.span(1)
                        if not any(a<y and x<b for x,y,*_ in ranges):ranges.append((a,b,[int(rid)],True))
            if not ranges:continue
            # Split only the affected runs/hyperlinks. Preserve prose formatting,
            # external links and bookmarks outside the exact citation spans.
            original=list(p);offsets=[];pos=0
            for n in original:
                s=text(n);offsets.append((pos,pos+len(s),n));pos+=len(s)
            for n in original:
                if n.tag!=q('pPr'):p.remove(n)
            def fragment(a,b):
                for x,y,n in offsets:
                    if n.tag==q('pPr'):continue
                    if x==y:
                        if a<=x<b:p.append(deepcopy(n))
                        continue
                    lo,hi=max(x,a),min(y,b)
                    if lo>=hi:continue
                    if lo==x and hi==y:p.append(deepcopy(n));continue
                    part=deepcopy(n);start=0
                    for node in part.xpath('.//w:t',namespaces=NS):
                        s=node.text or '';end=start+len(s)
                        node.text=s[max(0,lo-x-start):max(0,min(len(s),hi-x-start))] if start<hi-x and end>lo-x else ''
                        node.set('{http://www.w3.org/XML/1998/namespace}space','preserve');start=end
                    p.append(part)
            pos=0
            for a,b,ids,suppress in sorted(ranges):
                assert a>=pos
                fragment(pos,a);self.citation(p,t[a:b],ids,suppress);pos=b
            fragment(pos,len(t)+1)
        assert self.used==set(range(1,50)), sorted(set(range(1,50))-self.used)

    def bibliography(self):
        data=(ROOT/'Documents/Referencias/Bibliografia_APA_Zotero.html').read_bytes()
        dom=E.fromstring(data);entries=dom.findall(".//*[@class='csl-entry']")
        assert len(entries)==49
        # Match entries to actual collection keys using title and URL; generic
        # titles such as Text-to-speech need their URL to distinguish them.
        matched={}
        for rid,item in self.items.items():
            hits=[e for e in entries if norm(item['title']) in norm(''.join(e.itertext()))]
            if len(hits)>1:
                urls=[item.get('URL',''), 'https://doi.org/'+item['DOI'] if item.get('DOI') else '']
                hits=[e for e in hits if any(norm(u)==norm(a.get('href','')) for u in urls if u for a in e.findall('.//a'))]
            assert len(hits)==1,(rid,item['title'],len(hits))
            assert id(hits[0]) not in matched
            matched[id(hits[0])]=rid
        title=self.paragraph('Referencias');old=list(self.body)[self.body.index(title)+1:]
        for n in old:
            if n.tag!=q('sectPr'):self.body.remove(n)
        last=title;new=[]
        for e in entries:
            p=E.Element(q('p'));pr=ppr(p)
            child(pr,'pStyle',val='Normal');child(pr,'spacing',after=0,line=480,lineRule='auto');child(pr,'jc',val='left')
            child(pr,'ind',left=720,hanging=720);child(pr,'keepLines')
            rid=matched[id(e)]
            bm=E.SubElement(p,q('bookmarkStart'));bm.set(q('id'),str(5000+rid));bm.set(q('name'),'tutor_ref_'+str(rid))
            def html_runs(node,parent,italic=False,bold=False):
                if node.text:run(parent,node.text,italic=italic,bold=bold)
                for c in node:
                    target=parent
                    if c.tag=='a' and c.get('href'):
                        target=E.SubElement(parent,q('hyperlink'));target.set('{'+R+'}id',self.url(c.get('href')))
                    html_runs(c,target,italic or c.tag in ['i','em'],bold or c.tag in ['b','strong'])
                    if c.tail:run(parent,c.tail,italic=italic,bold=bold)
            html_runs(e,p)
            E.SubElement(p,q('bookmarkEnd')).set(q('id'),str(5000+rid))
            last.addnext(p);last=p;new.append(p)
        # One bibliography field spans all generated paragraphs; no static,
        # individually maintained bibliography sits outside this field.
        first=new[0];prefix=E.Element(q('p'))
        field_start(prefix,' ADDIN ZOTERO_BIBL {"uncited":[],"omitted":[],"custom":[]} CSL_BIBLIOGRAPHY ')
        for i,n in enumerate(list(prefix)):first.insert(i+1,n)
        field_end(new[-1])
        assert [text(p) for p in new]==[''.join(e.itertext()) for e in entries]
        self.bib_entries=[{'reference_id':matched[id(e)],'text':''.join(e.itertext())} for e in entries]
        self.bib_hash=digest(data)

    def url(self,url):
        found=next((r.get('Id') for r in self.rels if r.get('Type')==R+'/hyperlink' and r.get('Target')==url),None)
        if found:return found
        rid='rIdZoteroLink'+str(len(self.rels)+1)
        E.SubElement(self.rels,'{'+REL+'}Relationship',Id=rid,Type=R+'/hyperlink',Target=url,TargetMode='External')
        return rid

    def preferences(self):
        data={'style':{'styleID':'http://www.zotero.org/styles/apa','locale':'es-ES','hasBibliography':True,'bibliographyStyleHasBeenSet':True},
              'prefs':{'fieldType':'Field','noteType':0,'automaticJournalAbbreviations':False,'delayCitationUpdates':False},
              'sessionID':uuid.uuid4().hex,'zoteroVersion':'7.0','dataVersion':4}
        serialized=json.dumps(data,separators=(',',':'))
        CP='http://schemas.openxmlformats.org/officeDocument/2006/custom-properties';VT='http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes'
        custom=E.fromstring(self.parts['docProps/custom.xml']) if 'docProps/custom.xml' in self.parts else E.Element('{'+CP+'}Properties',nsmap={None:CP,'vt':VT})
        for p in list(custom):
            if p.get('name','').startswith('ZOTERO_PREF_'):custom.remove(p)
        pid=max([int(p.get('pid')) for p in custom]+[1])+1
        for i,pos in enumerate(range(0,len(serialized),255),1):
            prop=E.SubElement(custom,'{'+CP+'}property',fmtid='{D5CDD505-2E9C-101B-9397-08002B2CF9AE}',pid=str(pid+i-1),name='ZOTERO_PREF_'+str(i))
            E.SubElement(prop,'{'+VT+'}lpwstr').text=serialized[pos:pos+255]
        self.parts['docProps/custom.xml']=E.tostring(custom,xml_declaration=True,encoding='UTF-8',standalone=True)
        rels=E.fromstring(self.parts['_rels/.rels'])
        if not any(r.get('Type')==R+'/custom-properties' for r in rels):
            E.SubElement(rels,'{'+REL+'}Relationship',Id='rIdZoteroPreferences',Type=R+'/custom-properties',Target='docProps/custom.xml')
        self.parts['_rels/.rels']=E.tostring(rels,xml_declaration=True,encoding='UTF-8',standalone=True)
        types=E.fromstring(self.parts['[Content_Types].xml'])
        if not any(r.get('PartName')=='/docProps/custom.xml' for r in types):
            E.SubElement(types,'{http://schemas.openxmlformats.org/package/2006/content-types}Override',PartName='/docProps/custom.xml',ContentType='application/vnd.openxmlformats-officedocument.custom-properties+xml')
        self.parts['[Content_Types].xml']=E.tostring(types,xml_declaration=True,encoding='UTF-8',standalone=True)

    def save(self,output,evidence):
        self.parts['word/document.xml']=E.tostring(self.root,xml_declaration=True,encoding='UTF-8',standalone=True)
        self.parts['word/_rels/document.xml.rels']=E.tostring(self.rels,xml_declaration=True,encoding='UTF-8',standalone=True)
        nums=lambda rows:[re.findall(r'-?\d+(?:[.,]\d+)?',s) for s in rows]
        assert nums(self.original_tables)==nums([text(t) for t in self.body.findall(q('tbl'))])
        assert all(self.parts[k]==v for k,v in self.original_parts.items() if k.startswith('word/media/'))
        bookmarks={b.get(q('name')) for b in self.root.xpath('//w:bookmarkStart',namespaces=NS)}
        assert all(h.get(q('anchor')) in bookmarks for h in self.root.xpath('//w:hyperlink[@w:anchor]',namespaces=NS))
        nav=[]
        for p in self.body.findall(q('p')):
            for b in p.findall(q('bookmarkStart')):
                if b.get(q('name'),'').startswith('tutor_nav_'):nav.append({'name':b.get(q('name')),'text':text(p)})
        with ZipFile(output,'w',ZIP_DEFLATED) as z:
            for n,data in self.parts.items():z.writestr(n,data)
        evidence.mkdir(parents=True,exist_ok=True)
        (evidence/'navegacion.json').write_text(json.dumps(nav,ensure_ascii=False,indent=2)+'\n')
        result={'input_sha256':digest(self.source.read_bytes()),'output_sha256':digest(output.read_bytes()),'sections':12,
                'citation_fields':len(self.fields),'cited_zotero_items':len(self.used),'bibliography_entries':49,'bibliography_source_sha256':self.bib_hash,
                'library_export_sha256':digest((ROOT/'Documents/Referencias/biblioteca_sincronizada.csl.json').read_bytes()),
                'zotero_collection':'https://www.zotero.org/diomedescerda/collections/X2VAUMZ3',
                'zotero_source':'Verified collection export and APA bibliography from Zotero Web API; see Zotero/actualizacion_formato_2026-11-06.json for the authenticated refresh and author correction.',
                'integration_verification':'Word fields, embedded item snapshots/URIs, document preferences and bibliography text checked structurally. Desktop Zotero Refresh not available in this Linux session.',
                'all_22_tables_numeric_values_preserved':True,'all_embedded_media_bytes_preserved':True,
                'prose_changes':self.logs,'citations':self.fields,'bibliography':self.bib_entries}
        (evidence/'validacion_formato_zotero.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k not in ['prose_changes','citations','bibliography']},ensure_ascii=False,indent=2))


def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--evidence-dir',required=True,type=Path)
    a=p.parse_args();assert a.source.resolve()!=a.output.resolve(),'Use a separate output path.'
    r=FormatRevision(a.source);r.layout();r.citations();r.bibliography();r.preferences();r.save(a.output,a.evidence_dir)


if __name__=='__main__':main()
