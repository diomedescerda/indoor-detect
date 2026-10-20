"""Close editorial placeholders for the submission copy without inventing approval."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree as E
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
LINE='Inteligencia artificial y visión por computador aplicadas a tecnologías de asistencia'
PREVIOUS_THANKS='Agradezco a la Universidad del Magdalena y al Programa de Ingeniería de Sistemas por el marco académico en el que se desarrolló este trabajo. A Idanis Beatriz Diaz Bolaño, directora, y a Aquiles Alfonso Cohen Llanes, codirector, les expreso mi agradecimiento por la orientación académica del proyecto.'
THANKS='A mi abuela, por su cariño y por el lugar tan importante que ocupa en mi vida. A mi padre, por su apoyo y por acompañarme en este camino. A mis amigos, por su compañía, sus palabras de ánimo y los momentos compartidos durante esta etapa. A toda mi familia, por estar presente y ser parte de este logro. Mi agradecimiento principal es para ustedes: este trabajo también representa lo que significa contar con las personas que quiero. Agradezco, además, a Idanis Beatriz Diaz Bolaño, directora, y a Aquiles Alfonso Cohen Llanes, codirector, por la orientación académica del proyecto, y a la Universidad del Magdalena por el espacio de formación.'
def finalize(path):
 p=Path(path)
 with ZipFile(p) as z:parts={n:z.read(n) for n in z.namelist()}
 x=E.fromstring(parts['word/document.xml']);body=x.find('w:body',NS)
 text=lambda n:''.join(n.xpath('.//w:t/text()',namespaces=NS))
 def replace(old,new):
  found=[v for v in body.findall('.//w:p',NS) if text(v)==old]
  if not found:return
  assert len(found)==1
  nodes=found[0].findall('.//w:t',NS);nodes[0].text=new
  for t in nodes[1:]:t.text=''
 replace('[PENDIENTE: línea de investigación]',LINE)
 replace('[PENDIENTE: agradecimientos (opcional)]',THANKS)
 replace(PREVIOUS_THANKS,THANKS)
 children=list(body);starts=[i for i,c in enumerate(children) if text(c)=='Nota de aceptación:']
 if starts:
  start=starts[0];end=next(i for i in range(start+1,len(children)) if text(children[i])=='Agradecimientos')
  for v in children[start:end]:
   assert not v.findall('.//w:sectPr',NS),'Retain section geometry'
   body.remove(v)
 # Express scientific scope as completed-study limitations, not an editorial TODO.
 replace('Estos antecedentes justifican una arquitectura que ejecute la inferencia localmente, limite la información anunciada y traduzca la caja detectada a una zona espacial comprensible. AssistiveVision adopta un modo manual bajo demanda y una localización bidimensional por zonas. El capítulo 4 explora la relación entre detección y distancia estimada; la validación con distancias medidas permanece pendiente.','Estos antecedentes justifican una arquitectura que ejecute la inferencia localmente, limite la información anunciada y traduzca la caja detectada a una zona espacial comprensible. AssistiveVision adopta un modo manual bajo demanda y una localización bidimensional por zonas. El capítulo 4 explora la relación entre detección y distancia estimada; el estudio no incluyó validación con distancias medidas.')
 replace('SpeechFormatter, AudioModule y catálogo de voces; claridad auditiva pendiente.','SpeechFormatter, AudioModule y catálogo de voces; claridad auditiva no evaluada.')
 # Avoid implicit blank pages after removing the approval sheet.
 for section in x.findall('.//w:sectPr',NS)[:3]:
  kind=section.find('w:type',NS)
  if kind is not None:kind.set('{'+NS['w']+'}val','nextPage')
 # Preliminary Roman labels are literal for LibreOffice compatibility.
 prelim={'Resumen':'IV','Abstract':'V','Contenido':'VI','Lista de figuras':'VIII','Lista de tablas':'IX','Lista de símbolos':'X'}
 for par in body.findall('w:p',NS):
  s=text(par)
  for title,label in prelim.items():
   if s.startswith(title) and s[len(title):] and __import__('re').fullmatch('[IVXLCDM]+',s[len(title):]):
    ts=par.findall('.//w:t',NS)
    for t in reversed(ts):
     if __import__('re').fullmatch('[IVXLCDM]+',t.text or ''):t.text=label;break
 parts['word/document.xml']=E.tostring(x,xml_declaration=True,encoding='UTF-8',standalone=True)
 with ZipFile(p,'w',ZIP_DEFLATED) as z:
  for n,v in parts.items():z.writestr(n,v)
if __name__=='__main__':finalize(Path(__file__).resolve().parents[1]/'Informe_Final_Trabajo_de_Grado_AssistiveVision.docx')
