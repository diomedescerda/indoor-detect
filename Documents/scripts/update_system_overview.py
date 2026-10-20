"""Keep the final summary, abstract and interpretation centered on the integrated system."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from difflib import SequenceMatcher
import json
from lxml import etree as E
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
def apply_system_overview(path):
 path=Path(path)
 with ZipFile(path) as z:parts={n:z.read(n) for n in z.namelist()}
 root=E.fromstring(parts['word/document.xml']);paragraphs=root.findall('.//w:body/w:p',NS)
 text=lambda p:''.join(p.xpath('.//w:t/text()',namespaces=NS))
 edits=json.loads((Path(__file__).parent/'system_overview_revision.json').read_text())['edits'];changed=False
 for edit in edits:
  if any(text(p)==edit['new'] for p in paragraphs):continue
  found=[p for p in paragraphs if text(p)==edit['old']];assert len(found)==1,edit['old'][:100]
  p=found[0]
  for action,a,b,c,d in reversed(SequenceMatcher(None,edit['old'],edit['new'],autojunk=False).get_opcodes()):
   if action=='equal':continue
   value=edit['new'][c:d];offset=0;started=False
   for node in p.findall('.//w:t',NS):
    chunk=node.text or '';lo=offset;hi=offset+len(chunk);offset=hi
    if a==b:
     if not started and lo<=a<=hi:
      pos=a-lo;node.text=chunk[:pos]+value+chunk[pos:];started=True
     continue
    if hi<=a or lo>=b:continue
    node.text=chunk[:max(0,a-lo)]+(value if not started else '')+chunk[max(0,b-lo):];started=True
    node.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
   assert started
  assert text(p)==edit['new'];changed=True
 if not changed:return
 parts['word/document.xml']=E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
 with ZipFile(path,'w',ZIP_DEFLATED) as z:
  for n,v in parts.items():z.writestr(n,v)
if __name__=='__main__':apply_system_overview(Path(__file__).resolve().parents[1]/'Informe_Final_Trabajo_de_Grado_AssistiveVision.docx')
