"""Document the author's Roboflow provenance clarification without guessing a dataset URL."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree as E

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
OLD = 'La evaluación de precisión se realizó sobre un conjunto de imágenes propias capturadas en entornos interiores reales, complementadas con imágenes obtenidas de fuentes externas. Las imágenes fueron anotadas manualmente mediante la plataforma Roboflow '
NEW = 'El conjunto inicial reúne imágenes propias de interiores e imágenes externas obtenidas de Roboflow. La exportación del 5 de junio de 2026 declara licencia CC BY 4.0 y se conserva con las imágenes y anotaciones en el repositorio del proyecto. La anotación manual se realizó en Roboflow '

def apply_provenance(path):
    path = Path(path)
    with ZipFile(path) as archive:
        parts = {name: archive.read(name) for name in archive.namelist()}
    root = E.fromstring(parts['word/document.xml'])
    paragraphs = root.findall('.//w:body/w:p', NS)
    text = lambda p: ''.join(p.xpath('.//w:t/text()', namespaces=NS))
    if any(text(p).startswith(NEW) for p in paragraphs):
        return
    matches = [p for p in paragraphs if text(p).startswith(OLD)]
    assert len(matches) == 1, 'Expected one original dataset paragraph.'
    paragraph = matches[0]
    before = text(paragraph)
    remaining = len(OLD)
    inserted = False
    for node in paragraph.findall('.//w:t', NS):
        value = node.text or ''
        if not remaining:
            break
        take = min(remaining, len(value))
        node.text = (NEW if not inserted else '') + value[take:]
        node.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        inserted = True
        remaining -= take
    assert text(paragraph) == before.replace(OLD, NEW, 1)
    parts['word/document.xml'] = E.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
    with ZipFile(path, 'w', ZIP_DEFLATED) as archive:
        for name, value in parts.items():
            archive.writestr(name, value)

if __name__ == '__main__':
    apply_provenance(Path(__file__).resolve().parents[1] / 'Informe_Final_Trabajo_de_Grado_AssistiveVision.docx')
