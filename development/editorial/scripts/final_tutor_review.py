"""Apply only the final tutor requests to the retained, field-preserving report.

The annotated attachment differs from the base only by reviewer instructions
and page-reference caches. Patch the base to preserve Zotero fields and layout.
Personal delivery letters are written outside the public Git repository.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree as E

ROOT=Path(__file__).resolve().parents[3]
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
NS={'w':W,'r':R}
q=lambda s:'{'+W+'}'+s
text=lambda p:''.join(p.xpath('.//w:t/text()',namespaces=NS))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
TITLE='Sistema de identificación y localización espacial de objetos basado en visión por computador para asistencia a personas con discapacidad visual'

def load(p):
    with ZipFile(p) as z:return {n:z.read(n) for n in z.namelist()}

def save(parts,p):
    p.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(p,'w',ZIP_DEFLATED) as z:
        for n,b in parts.items():z.writestr(n,b)

def xml(r):return E.tostring(r,xml_declaration=True,encoding='UTF-8',standalone=True)

def child(p,n,**attrs):
    e=p.find(q(n))
    if e is None:e=E.SubElement(p,q(n))
    for k,v in attrs.items():e.set(q(k),str(v))
    return e

def replace(p,s,bold=None):
    assert not p.xpath('.//w:fldChar|.//w:fldSimple|.//w:hyperlink|.//w:drawing',namespaces=NS),'Preserve fields and images'
    rp=p.find('w:r/w:rPr',NS);rp=deepcopy(rp) if rp is not None else E.Element(q('rPr'))
    for c in list(p):
        if c.tag not in [q('pPr'),q('bookmarkStart'),q('bookmarkEnd')]:p.remove(c)
    child(rp,'color',val='000000')
    for n in rp.findall(q('highlight'))+rp.findall(q('shd')):rp.remove(n)
    if bold is not None:
        for b in rp.findall(q('b')):rp.remove(b)
        if bold:child(rp,'b')
    r=E.SubElement(p,q('r'));r.append(rp)
    t=E.SubElement(r,q('t'));t.text=s;t.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
    for end in list(p.findall(q('bookmarkEnd'))):p.remove(end);p.append(end)

def paragraph(s):
    p=E.Element(q('p'));pr=E.SubElement(p,q('pPr'))
    child(pr,'pStyle',val='Normal');child(pr,'spacing',after=330,line=360,lineRule='auto')
    child(pr,'jc',val='both');child(pr,'keepLines');replace(p,s)
    return p

def report(source,output,evidence):
    parts=load(source);original=dict(parts);root=E.fromstring(parts['word/document.xml']);body=root.find(q('body'));changes=[]
    def find(prefix):
        hits=[p for p in body.findall(q('p')) if text(p).startswith(prefix) and not p.xpath('.//w:fldSimple',namespaces=NS)]
        assert len(hits)==1,(prefix,len(hits));return hits[0]
    def after(anchor,s,reason):
        p=paragraph(s);anchor.addnext(p);changes.append({'request':reason,'before':'','after':s});return p
    def edit(prefix,s,reason):
        p=find(prefix);before=text(p);replace(p,s);changes.append({'request':reason,'before':before,'after':s});return p
    # The two red instructions follow the desktop and GPU result tables.
    for cap,s in [
      ('Tabla 2.2.','Las Tablas 2.1 y 2.2 permiten distinguir el desempeño agregado de las diferencias por clase. EfficientDet-Lite2 obtuvo la mayor mAP50 (0,648), mientras que YOLOv8s alcanzó la mayor mAP50-95 (0,514) y F1 (0,702). EfficientDet-Lite2 destacó en persona, sofá y cama, pero YOLOv8s obtuvo mejores resultados en mesa de comedor y computador portátil. Por tanto, la ventaja agregada de un detector no implica que sea el mejor en todas las categorías; esta comparación se complementa con su costo de ejecución en Android.'),
      ('Tabla 2.4.','Las Tablas 2.3 y 2.4 muestran que el delegado GPU no redujo la latencia de ninguno de los modelos probados. En EfficientDet-Lite2, el promedio pasó de 124,9 ms en CPU a 357,9 ms con GPU; en YOLOv8s Float32 pasó de 620,8 a 743,8 ms. El menor tiempo en CPU correspondió a SSD MobileNetV1 (23,4 ms), aunque sus métricas de detección fueron inferiores en la Tabla 2.1. Estos resultados motivan el análisis conjunto de exactitud, latencia y memoria de la sección 2.7 y la selección final de la sección 2.8.')]:
        anchor=find(cap)
        while anchor.getnext() is not None and not (anchor.tag==q('p') and text(anchor).startswith('Fuente:')):anchor=anchor.getnext()
        after(anchor,s,'Interpretar las tablas de resultados del capítulo 2')
    p=find('Se compararon arnés de cabeza,')
    edit('Se compararon arnés de cabeza,',text(p)+' La Figura 3.2 presenta los tres tipos de soporte utilizados; la Figura 4.2 ilustra su colocación para la captura.','Relacionar el posicionamiento con las imágenes de los soportes')
    anchor=find('3.12 Verificación')
    p=paragraph('La interacción para personas ciegas se apoya en la salida de voz y en los mecanismos de accesibilidad de Android. Los controles Capturar y Ajustes son enfocables y exponen el rol de botón al lector de pantalla TalkBack; los iconos decorativos se excluyen de su recorrido, y los controles de volver y de pantalla completa tienen descripciones de contenido. El estado textual se configura como una región de actualización cortés para que el lector de pantalla pueda anunciar sus cambios. Así, la información esencial de la captura no depende exclusivamente de las cajas y etiquetas dibujadas sobre la vista previa.')
    anchor.addprevious(p);changes.append({'request':'Explicar la adaptación de la interfaz','before':'','after':text(p)})
    p=paragraph('Además del control táctil, una tecla física compatible o un disparador Bluetooth puede solicitar la captura desde la pantalla de cámara. La descripción sintetizada comunica los objetos seleccionados y su región relativa, mientras que los ajustes permiten cambiar idioma, velocidad de voz y número máximo de objetos. La interacción se apoya así en la voz, los controles identificables y la captura física. Como continuación del trabajo se propone evaluar la usabilidad con personas ciegas y el recorrido completo de la interfaz con TalkBack.')
    anchor.addprevious(p);changes.append({'request':'Describir positivamente los recursos de accesibilidad y su evaluación posterior','before':'','after':text(p)})
    after(find('Finalmente, en la dimensión de síntesis'),
      'El anuncio describe la escena mediante una oración y no incluye un saludo inicial. Por ejemplo, si se seleccionan una silla en la región inferior izquierda y un televisor en la superior derecha, SpeechFormatter construye: «Hay una silla abajo a la izquierda de donde estás apuntando y un televisor arriba a la derecha de donde estás apuntando». Este ejemplo ilustra la composición prevista por el código, no una nueva observación experimental. Las regiones se refieren al encuadre de la cámara y el mensaje no expresa una distancia física. Cuando no hay detecciones seleccionadas, la implementación muestra el estado «sin detecciones» y libera la captura; no genera una descripción de objetos. Las pruebas técnicas de formato y síntesis no miden por sí solas la comprensión del mensaje por parte de un oyente.',
      'Dar un ejemplo del audio e indicar si existe saludo')
    h=find('5. Conclusiones')
    after(h,'En este trabajo se desarrolló un prototipo móvil para identificar objetos de entornos interiores y comunicar su ubicación relativa mediante voz, como apoyo a la percepción del entorno de personas con discapacidad visual. El desarrollo se organizó alrededor de la selección del detector, la integración del sistema Android y su evaluación técnica. Los hallazgos de estas etapas permiten valorar los objetivos y precisar el alcance de la solución.', 'Introducir las conclusiones y conectarlas con los objetivos')
    p=find('El primer objetivo se atendió')
    edit('El primer objetivo se atendió',text(p)+' La comparación mostró que la arquitectura debe elegirse según el uso previsto: YOLOv8s ajustó mejor las cajas en umbrales exigentes, SSD MobileNetV1 procesó más rápido pero recuperó menos objetos y EfficientDet-Lite2 ofreció el compromiso seleccionado entre recuperación, tiempo y memoria. Reducir la espera antes del anuncio auditivo justificó priorizar este último equilibrio.', 'Explicitar el conocimiento obtenido al comparar arquitecturas')
    p=find('A partir de esta integración, para el tercer objetivo')
    edit('A partir de esta integración, para el tercer objetivo',text(p)+' La diferencia entre cobertura visual y desempeño del detector es decisiva para interpretar esa elección: el palo de selfie 0,5x incluyó 174 instancias y recuperó 82, mientras pecho 1x incluyó 124 y recuperó 65. El primero aportó más detecciones en términos absolutos; el segundo recuperó una mayor proporción de lo visible y obtuvo mayor F1. Un objeto fuera del encuadre reduce la información adquirida, pero no constituye un falso negativo del detector.', 'Distinguir cobertura visual y desempeño del detector en las conclusiones')
    p=find('Los conteos por grupo mostraron')
    edit('Los conteos por grupo mostraron',text(p).replace('confirma la claridad informativa, sintáctica y operativa de los mensajes generados','respalda la selección del contenido, la construcción de las frases y la ejecución local de la voz, sin medir su inteligibilidad con participantes'), 'Delimitar la conclusión sobre la retroalimentación auditiva')
    after(find('Respecto a las fases propuestas,'),'Las principales dificultades fueron la variación de encuadre entre montajes, las discrepancias entre algunas etiquetas de lente y los metadatos, y la separación entre las mediciones históricas del teléfono y la reproducción en emulador. A ello se añaden la distancia estimada sin calibración, las etiquetas de oclusión parcialmente asistidas por IA y la ausencia de una evaluación de comprensión con usuarios. Estas limitaciones impiden atribuir los cambios únicamente al soporte, fijar un alcance físico o extrapolar los tiempos y la utilidad a cualquier dispositivo o entorno.', 'Reunir las dificultades y limitaciones principales')
    after(find('Como aprendizaje metodológico,'),'Para el propósito de asistencia planteado, el prototipo demuestra la viabilidad técnica de transformar una captura solicitada por el usuario en información verbal sobre objetos y regiones del encuadre, sin conexión a internet. Esa función puede servir como apoyo puntual para explorar lo que hay frente a la cámara. Su utilidad práctica para personas con discapacidad visual debe confirmarse mediante pruebas de comprensión y uso en condiciones reales; los resultados actuales no demuestran una mejora de autonomía ni validan una ayuda de navegación segura.', 'Concluir sobre la utilidad del prototipo dentro de la evidencia disponible')
    # Replace the commercial photographs with the requested illustration slot.
    # A supplied illustration can be placed here later without inventing a photo.
    cap=find('Figura 4.2. Montajes usados para orientar la cámara.')
    # Move the existing, natively cropped product images to the introduction of
    # device positioning. Reuse their media relationships without re-encoding.
    model_caption=deepcopy(cap)
    for b in model_caption.findall(q('bookmarkStart'))+model_caption.findall(q('bookmarkEnd')):model_caption.remove(b)
    replace(model_caption,'Figura 3.2. Tipos de soporte utilizados para posicionar el dispositivo.')
    bookmark_id=str(max(int(b.get(q('id'))) for b in root.xpath('//w:bookmarkStart',namespaces=NS))+1)
    start=E.Element(q('bookmarkStart'),{q('id'):bookmark_id,q('name'):'tutor_nav_mounts'})
    model_caption.insert(1,start)
    E.SubElement(model_caption,q('bookmarkEnd'),{q('id'):bookmark_id})
    model_images=deepcopy(cap.getnext())
    model_labels=deepcopy(cap.getnext().getnext())
    for t in model_labels.xpath('.//w:t',namespaces=NS):
        if t.text=='(b) Pecho Innovo+':t.text='(b) Pecho'
    model_source=deepcopy(cap.getnext().getnext().getnext())
    assert text(model_source).startswith('Fuente: ilustraciones comerciales')
    # Retain clickable provenance using concise source labels below the panel.
    texts=model_source.xpath('./w:r/w:t',namespaces=NS)
    assert len(texts)==4
    for t,value in zip(texts,['Fuente: fichas de los soportes de ','; ','; ','.']):t.text=value
    for link,value in zip(model_source.findall(q('hyperlink')),['cabeza','pecho','palo de selfie (diseño de referencia)']):
        nodes=link.xpath('.//w:t',namespaces=NS);assert len(nodes)==1;nodes[0].text=value
    child(child(model_source,'pPr'),'spacing',after=200,line=240,lineRule='auto')
    child(child(model_source,'pPr'),'jc',val='center')
    for run in model_source.xpath('.//w:r',namespaces=NS):child(child(run,'rPr'),'sz',val=20)
    index=next(p for p in body.findall(q('p')) if text(p).startswith('Figura 3.2.') and p.find(q('fldSimple')) is not None)
    model_index=deepcopy(index)
    model_index.find(q('hyperlink')).set(q('anchor'),'tutor_nav_mounts')
    model_index.find('w:hyperlink/w:r/w:t',NS).text=text(model_caption)
    model_index.find(q('fldSimple')).set(q('instr'),' PAGEREF tutor_nav_mounts \\h ')
    # Shift subsequent chapter-3 figures in one pass, including prose and index.
    def shift(match):return 'Figura 3.'+str(int(match[1])+1)
    for t in root.xpath('//w:t',namespaces=NS):
        if t.text:t.text=re.sub(r'Figura 3\.([234])(?!\d)',shift,t.text)
    index.addprevious(model_index)
    anchor=find('Se compararon arnés de cabeza,')
    # The new reference was introduced before the renumbering pass.
    for t in anchor.xpath('.//w:t',namespaces=NS):t.text=t.text.replace('La Figura 3.3 presenta los tres tipos','La Figura 3.2 presenta los tres tipos')
    for node in [model_caption,model_images,model_labels,model_source]:anchor.addnext(node);anchor=node
    edit('La Figura 4.2 ilustra los tres soportes utilizados.',
         'La Figura 4.2 ilustra la colocación de los tres soportes para la captura; sus tipos se presentan en la Figura 3.2.',
         'Distinguir las imágenes de los soportes de su colocación')
    changes.append({'request':'Mostrar los soportes en Posicionamiento del dispositivo y actualizar las figuras del capítulo 3','before':'Imágenes de referencia en la Figura 4.2','after':'Nueva Figura 3.2 con tres paneles; regiones 3.3, secuencia 3.4 e interfaz 3.5; pies, menciones e índice actualizados'})
    edit('Figura 4.2. Montajes usados para orientar la cámara.',
         'Figura 4.2. Ilustración de la colocación de los soportes.',
         'Usar un pie breve que identifique la ilustración')
    for p in body.findall(q('p')):
        for n in p.xpath('.//w:t',namespaces=NS):
            if n.text and n.text.startswith('Figura 4.2. Montajes usados para orientar la cámara.'):
                n.text=n.text.replace('Figura 4.2. Montajes usados para orientar la cámara.','Figura 4.2. Ilustración de la colocación de los soportes.')
    images=cap.getnext();drawings=images.xpath('.//w:drawing',namespaces=NS);assert len(drawings)==3
    rels=E.fromstring(parts['word/_rels/document.xml.rels'])
    REL='http://schemas.openxmlformats.org/package/2006/relationships'
    placement_specs=[
        ('rIdReportImage6','media/report_colocacion_cabeza.jpeg',ROOT/'Documents/Figures/sources/mounts/colocacion_cabeza.jpeg','Colocación del soporte de cabeza.',1508760,2011680,4005),
        ('rIdReportImage7','media/report_colocacion_pecho.jpeg',ROOT/'Documents/Figures/sources/mounts/colocacion_pecho.jpeg','Colocación del arnés de pecho.',1508760,2011680,4006),
        ('rIdReportImage8','media/report_colocacion_palo_selfie.jpeg',ROOT/'Documents/Figures/sources/mounts/colocacion_palo_selfie.jpeg','Colocación del palo de selfie.',1507188,2011680,4007),
    ]
    for dnode,(rid,target,img_path,descr,cx,cy,doc_id) in zip(drawings,placement_specs):
        parts['word/'+target]=img_path.read_bytes()
        rel=E.SubElement(rels,'{'+REL+'}Relationship')
        rel.set('Id',rid);rel.set('Type',R+'/image');rel.set('Target',target)
        for ext in dnode.xpath('.//*[local-name()="extent" or (local-name()="ext" and @cx)]'):
            ext.set('cx',str(cx));ext.set('cy',str(cy))
        docPr=dnode.xpath('.//*[local-name()="docPr"]')[0]
        docPr.set('id',str(doc_id));docPr.set('name',Path(target).name);docPr.set('descr',descr)
        cNvPr=dnode.xpath('.//*[local-name()="cNvPr"]')[0]
        cNvPr.set('name',Path(target).name)
        blip=dnode.xpath('.//*[local-name()="blip"]')[0]
        blip.set('{'+R+'}embed',rid)
        for sr in dnode.xpath('.//*[local-name()="srcRect"]'):sr.getparent().remove(sr)
    parts['word/_rels/document.xml.rels']=xml(rels)
    labels=images.getnext();assert text(labels).startswith('(a) Cabeza')
    for t in labels.xpath('.//w:t',namespaces=NS):
        if t.text=='(b) Pecho Innovo+':t.text='(b) Pecho'
    source_note=labels.getnext();assert text(source_note).startswith('Fuente: ilustraciones comerciales')
    for hlink in list(source_note.findall(q('hyperlink'))):source_note.remove(hlink)
    replace(source_note,'Fuente: fotografías del autor.')
    child(child(source_note,'pPr'),'spacing',after=200,line=240,lineRule='auto')
    child(child(source_note,'pPr'),'jc',val='center')
    for run in source_note.xpath('.//w:r',namespaces=NS):child(child(run,'rPr'),'sz',val=20)
    changes.append({'request':'Incorporar fotografías de la colocación de los soportes en la Figura 4.2','before':'Tres fotografías comerciales','after':'Tres fotografías del autor mostrando la colocación en cabeza, pecho y palo de selfie'})
    # A few long table headings previously split in the middle of words.
    for caption,cell_indices in [('Tabla 2.2.',[6]),('Tabla 4.5.',[2]),('Tabla 4.8.',[1,2])]:
        table=find(caption).getnext();assert table.tag==q('tbl')
        cells=table.find(q('tr')).findall(q('tc'))
        for index in cell_indices:
            for rr in cells[index].xpath('.//w:r',namespaces=NS):child(child(rr,'rPr'),'sz',val=16)
    table=find('Tabla 2.3.').getnext();assert table.tag==q('tbl')
    head=table.find(q('tr')).findall(q('tc'))[4].find(q('p'))
    assert text(head)=='Lat. promedio';replace(head,'Lat. media')
    table=find('Tabla 4.8.').getnext()
    shifts=[0,200,200,0,0,0,-400]
    for col,delta in zip(table.find(q('tblGrid')),shifts):col.set(q('w'),str(int(col.get(q('w')))+delta))
    for row in table.findall(q('tr')):
        for cell,delta in zip(row.findall(q('tc')),shifts):
            width=cell.find('w:tcPr/w:tcW',NS);width.set(q('w'),str(int(width.get(q('w')))+delta))
    changes.append({'request':'Revisar la presentación de las tablas','before':'Encabezados largos divididos dentro de palabras','after':'Ajuste puntual de cuatro encabezados; Lat. promedio se abrevia como Lat. media'})
    # The retained source contains two orphaned ends from deleted front-matter
    # bookmarks. They have no target or visible content; remove those residues.
    bookmark_ids={b.get(q('id')) for b in root.xpath('//w:bookmarkStart',namespaces=NS)}
    orphan_ends=[b for b in root.xpath('//w:bookmarkEnd',namespaces=NS) if b.get(q('id')) not in bookmark_ids]
    for end in orphan_ends:end.getparent().remove(end)
    if orphan_ends:changes.append({'request':'Comprobar la integridad de marcadores','before':f'{len(orphan_ends)} cierres sin inicio heredados de la base','after':'Se eliminan los cierres huérfanos sin modificar texto ni destinos de navegación'})
    # Keep all numerical values and the original chapter/section system intact.
    before_tables=root.xpath('//w:body/w:tbl',namespaces=NS)
    oldroot=E.fromstring(original['word/document.xml'])
    numbers=lambda ts:[re.findall(r'-?\d+(?:[.,]\d+)?',text(t)) for t in ts]
    assert numbers(before_tables)==numbers(oldroot.xpath('//w:body/w:tbl',namespaces=NS))
    # Every figure/table caption has exactly one linked index entry, and every
    # numbered mention resolves after inserting and renumbering chapter 3.
    captions={}
    for p in body.findall(q('p')):
        match=re.match(r'^(Figura|Tabla) (\d+)\.(\d+)\. ',text(p))
        if match and p.find(q('fldSimple')) is None:
            key=f'{match[1]} {match[2]}.{match[3]}'
            assert key not in captions,key
            marks=p.findall(q('bookmarkStart'))
            name=next(b.get(q('name')) for b in marks if b.get(q('name'),'').startswith('tutor_nav_'))
            captions[key]=(text(p),name)
    assert sum(k.startswith('Figura') for k in captions)==11
    assert sum(k.startswith('Tabla') for k in captions)==22
    for key,(caption,name) in captions.items():
        entries=[p for p in body.findall(q('p')) if p.find(q('fldSimple')) is not None and text(p).startswith(caption)]
        assert len(entries)==1,(key,len(entries))
        assert entries[0].find(q('hyperlink')).get(q('anchor'))==name,key
        assert re.search(r'PAGEREF\s+'+re.escape(name)+r'\s',entries[0].find(q('fldSimple')).get(q('instr'))),key
    for p in body.findall(q('p')):
        for kind,chapter,num in re.findall(r'\b(Figura|Tabla) (\d+)\.(\d+)',text(p)):
            assert f'{kind} {chapter}.{num}' in captions,(kind,chapter,num)
    assert root.xpath('//w:instrText/text()',namespaces=NS)==oldroot.xpath('//w:instrText/text()',namespaces=NS),'Preserve native Zotero fields'
    pag_file=evidence/'paginacion_verificada.json'
    if pag_file.exists():
        mapping=json.loads(pag_file.read_text()).get('entries',{})
        for field in root.xpath('//w:fldSimple',namespaces=NS):
            m=re.search(r'PAGEREF\s+(\w+)',field.get(q('instr'),''))
            if m and m[1] in mapping:
                texts=field.xpath('.//w:t',namespaces=NS)
                if len(texts)==1:texts[0].text=mapping[m[1]]['label']
    parts['word/document.xml']=xml(root);save(parts,output)
    assert all(parts[k]==v for k,v in original.items() if k not in ('word/document.xml','word/_rels/document.xml.rels'))
    evidence.mkdir(parents=True,exist_ok=True)
    (evidence/'cambios_contenido.json').write_text(json.dumps({'source_sha256':sha(source),'output_sha256':sha(output),'changes':changes},ensure_ascii=False,indent=2)+'\n')
    nav=[]
    for p in body.findall(q('p')):
        for b in p.findall(q('bookmarkStart')):
            if b.get(q('name'),'').startswith('tutor_nav_'):nav.append({'name':b.get(q('name')),'text':text(p)})
    (evidence/'navegacion.json').write_text(json.dumps(nav,ensure_ascii=False,indent=2)+'\n')
    print('Report content changes:',len(changes))

def letters(templates,out,identity):
    # Source-derived bodies, unchanged page geometry, logo and headers.
    for kind in ['entrega','aval']:
        source=templates/('formato_entrega_original.docx' if kind=='entrega' else 'carta_aval_original.docx')
        parts=load(source);root=E.fromstring(parts['word/document.xml']);body=root.find(q('body'));ps=body.findall(q('p'));tables=body.findall(q('tbl'))
        def rep(i,s,bold=None):replace(ps[i],s,bold)
        if kind=='entrega':
            rep(2,'Santa Marta, ____________________')
            rep(5,'Consejo de Programa de Ingeniería de Sistemas',True)
            rep(13,'Yo, Diomedes Farid Cerda Leon, estudiante del Programa de Ingeniería de Sistemas, presento para su evaluación el informe final del trabajo de grado titulado «'+TITLE+'», en la modalidad de Pasantía de investigación, bajo la dirección de Idanis Beatriz Diaz Bolaño y la codirección de Aquiles Alfonso Cohen Llanes.')
            for i in [17,20,23]:body.remove(ps[i])
            # The institutional modality matrix stays intact; mark one option.
            replace(tables[0].findall(q('tr'))[1].findall(q('tc'))[3].find(q('p')),'X',True)
            rows=tables[1].findall(q('tr'))
            for c,s in zip(rows[1].findall(q('tc')),['2021114064','Diomedes Farid Cerda Leon','Ingeniería de Sistemas']):replace(c.find(q('p')),s)
            for row in rows[2:]:tables[1].remove(row)
            # The code has ten digits; widen its source column rather than wrap it.
            grid=tables[1].find(q('tblGrid'))
            if grid is not None:
                cols=grid.findall(q('gridCol'))
                for c,delta in zip(cols,[400,-400,0]):c.set(q('w'),str(int(c.get(q('w')))+delta))
            for row in tables[1].findall(q('tr')):
                for c,delta in zip(row.findall(q('tc')),[400,-400,0]):
                    width=c.find('w:tcPr/w:tcW',NS)
                    if width is not None:width.set(q('w'),str(int(width.get(q('w')))+delta))
            rows=tables[2].findall(q('tr'))
            for row,values in zip(rows[2:4],[['Idanis Beatriz Diaz Bolaño','X',''],['Aquiles Alfonso Cohen Llanes','','X']]):
                for c,s in zip(row.findall(q('tc')),values):replace(c.find(q('p')),s)
            for row in rows[4:]:tables[2].remove(row)
            rep(26,'Documentos adjuntos: informe final y carta de aval de la dirección del trabajo. Los datos, resultados y código de la aplicación se encuentran enlazados en el anexo del informe.')
            rep(29,'Agradezco la atención prestada y la continuidad del trámite de evaluación de esta modalidad de grado.')
            rep(32,'______________________________\t______________________________')
            rep(33,'Idanis Beatriz Diaz Bolaño\tAquiles Alfonso Cohen Llanes')
            rep(34,'Directora\tCodirector')
            rep(37,'______________________________')
            rep(38,'Diomedes Farid Cerda Leon\nEstudiante · Código 2021114064')
            target=out/'Carta_Entrega_Consejo_Programa.docx'
        else:
            rep(1,'Santa Marta, ____________________')
            rep(6,'Consejo de Programa de Ingeniería de Sistemas',True)
            rep(10,'Asunto: Aval del informe final de Pasantía de investigación',True)
            rep(15,'En calidad de directora del trabajo de grado, presento para su evaluación el aval del informe final titulado «'+TITLE+'», desarrollado en la modalidad de Pasantía de investigación por el estudiante relacionado a continuación.')
            rep(17,'Considero que el informe final reúne la calidad y rigurosidad académica e investigativa, la pertinencia y el alcance esperados para esta modalidad de grado, y refleja los conocimientos y competencias desarrollados por el estudiante. En consecuencia, doy mi aval para que el Consejo de Programa continúe el trámite de evaluación correspondiente.')
            rows=tables[0].findall(q('tr'))
            for c,s in zip(rows[1].findall(q('tc')),['Diomedes Farid Cerda Leon','2021114064',identity]):replace(c.find(q('p')),s)
            for row in rows[2:]:tables[0].remove(row)
            rep(23,'______________________________\t______________________________')
            rep(24,'Idanis Beatriz Diaz Bolaño\tAquiles Alfonso Cohen Llanes')
            rep(25,'Directora\tCodirector\nC. C. ____________________\tC. C. ____________________')
            target=out/'Carta_Aval_Informe_Final_PARA_FIRMA.docx'
        # Signature names use the source's two-column tab layout, not spaces.
        for i in ([32,33,34,38] if kind=='entrega' else [23,24,25]):
            pr=ps[i].find(q('pPr'))
            if pr is None:pr=E.Element(q('pPr'));ps[i].insert(0,pr)
            tabs=child(pr,'tabs')
            for t in list(tabs):tabs.remove(t)
            for pos in ['4252','8504']:E.SubElement(tabs,q('tab'),{q('val'):'clear',q('pos'):pos})
            E.SubElement(tabs,q('tab'),{q('val'):'left',q('pos'):'4800' if kind=='entrega' else '4200'})
            for rp in ps[i].xpath('.//w:rPr',namespaces=NS):
                child(rp,'rFonts',ascii='Arial',hAnsi='Arial',cs='Arial');child(rp,'sz',val=22)
                for n in rp.findall(q('i'))+rp.findall(q('b')):rp.remove(n)
            # A new line is encoded as a break and a tab as a real tab.
            for t in ps[i].xpath('.//w:t',namespaces=NS):
                value=t.text or '';parent=t.getparent();idx=parent.index(t);parent.remove(t)
                for chunk in re.split('(\t|\n)',value):
                    if chunk=='\t':n=E.Element(q('tab'))
                    elif chunk=='\n':n=E.Element(q('br'))
                    else:n=E.Element(q('t'));n.text=chunk
                    parent.insert(idx,n);idx+=1
        data_rows=(tables[1].findall(q('tr'))[1:]+tables[2].findall(q('tr'))[2:]) if kind=='entrega' else tables[0].findall(q('tr'))[1:]
        for row in data_rows:
                for rp in row.xpath('.//w:rPr',namespaces=NS):
                    child(rp,'rFonts',ascii='Arial',hAnsi='Arial',cs='Arial');child(rp,'sz',val=22)
                    for n in rp.findall(q('i')):rp.remove(n)
        parts['word/document.xml']=xml(root);save(parts,target)
        # Every image and all header/footer parts must retain their source bytes.
        srcparts=load(source)
        assert all(parts[n]==b for n,b in srcparts.items() if n.startswith(('word/media/','word/header','word/footer')))
        print('Prepared letter:',target.name)

def main():
    p=argparse.ArgumentParser();p.add_argument('--report-source',type=Path,required=True);p.add_argument('--report-output',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--templates',type=Path);p.add_argument('--letters-output',type=Path);p.add_argument('--identity-file',type=Path)
    a=p.parse_args()
    if any([a.templates,a.letters_output,a.identity_file]) and not all([a.templates,a.letters_output,a.identity_file]):p.error('For letters, provide --templates, --letters-output and --identity-file together.')
    report(a.report_source,a.report_output,a.evidence)
    if a.letters_output:letters(a.templates,a.letters_output,a.identity_file.read_text().strip())
if __name__=='__main__':main()
