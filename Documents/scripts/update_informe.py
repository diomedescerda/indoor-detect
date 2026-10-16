"""Update the university-format manuscript from its retained original and verified data.

Run with Python 3.12, python-docx and Pillow. Saved benchmark outputs must exist.
The original template is preserved; opaque package parts are copied byte for byte.
"""
import csv
import hashlib
import io
import json
import re
import zipfile
from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from lxml import etree as E
from PIL import Image, ImageDraw, ImageFont

REPO=Path(__file__).resolve().parents[2]
BASE=REPO/'Documents/Templates/Informe_Final_Base_2026-09-25.docx'
OUT=REPO/'Documents/Informe_Final_Trabajo_de_Grado_AssistiveVision.docx'
TEST=REPO/'Build/Testing'
RESULTS=TEST/'benchmark/results/android'
ASSETS=REPO/'Documents/Figures'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
H1='Ttulo1';H2='Ttulo2';H3='Ttulo3';CAP='Descripcin'


def read_csv(rel):return list(csv.DictReader((RESULTS/rel).open()))


def diagrams():
    ASSETS.mkdir(exist_ok=True)
    font=ImageFont.truetype('/usr/share/fonts/liberation/LiberationSans-Regular.ttf',30)
    def centered(d,box,text):
        x1,y1,x2,y2=box
        d.multiline_text(((x1+x2)/2,(y1+y2)/2),text,font=font,fill='black',anchor='mm',align='center',spacing=10)
    im=Image.new('RGB',(1700,690),'white');d=ImageDraw.Draw(im)
    labels=['Captura\nCameraX','Preprocesamiento\nLetterbox RGB','Detección\nEfficientDet-Lite2','Selección\nConfianza y top 2','Localización\nSeis zonas','Descripción de voz\nsherpa-onnx']
    for i,label in enumerate(labels):
        row,col=divmod(i,3);x=30+col*560;y=45+row*350
        d.rectangle((x,y,x+510,y+210),outline='#333333',width=3);centered(d,(x,y,x+510,y+210),label)
        if col<2:d.line((x+510,y+105,x+552,y+105),fill='black',width=4);d.polygon([(x+550,y+105),(x+534,y+96),(x+534,y+114)],fill='black')
    d.line((1410,255,1410,305,285,305,285,395),fill='black',width=4);d.polygon([(285,395),(276,378),(294,378)],fill='black')
    im.save(ASSETS/'arquitectura.png')
    im=Image.new('RGB',(1600,930),'white');d=ImageDraw.Draw(im)
    x0,y0,w,h=90,80,1400,760
    d.rectangle((x0,y0,x0+w,y0+h),outline='black',width=3)
    for x in (x0+.35*w,x0+.65*w):d.line((x,y0,x,y0+h),fill='black',width=3)
    d.line((x0,y0+h/2,x0+w,y0+h/2),fill='black',width=3)
    for row,vertical in enumerate(('superior','inferior')):
        for col,horizontal in enumerate(('Izquierda','Centro','Derecha')):
            xs=[x0,x0+.35*w,x0+.65*w,x0+w]
            centered(d,(xs[col],y0+row*h/2,xs[col+1],y0+(row+1)*h/2),horizontal+'\n'+vertical)
    d.text((x0+.35*w,y0-35),'0,35 W',font=font,fill='black',anchor='mm');d.text((x0+.65*w,y0-35),'0,65 W',font=font,fill='black',anchor='mm')
    d.text((x0+w/2,y0+h+40),'La zona se asigna al centro de la caja detectada',font=font,fill='black',anchor='mm')
    im.save(ASSETS/'zonas.png')
    im=Image.new('RGB',(1700,430),'white');d=ImageDraw.Draw(im)
    for i,label in enumerate(('Vista previa\ncontinua','Capturar\ny congelar','Detectar, localizar\ny hablar','Fin o error\nvolver a vista previa')):
        x=20+i*425;d.rectangle((x,60,x+380,300),outline='black',width=3);centered(d,(x,60,x+380,300),label)
        if i<3:d.line((x+380,180,x+417,180),fill='black',width=4);d.polygon([(x+415,180),(x+400,171),(x+400,189)],fill='black')
    im.save(ASSETS/'interaccion.png')


def main():
    diagrams();doc=Document(BASE);original=list(doc.paragraphs)
    def change(index,text):
        p=original[index];p.clear();p.add_run(text);return p
    def remove(el):el.getparent().remove(el)
    def add_before(anchor,text,style='Normal'):
        p=doc.add_paragraph(text,doc.styles[style]);anchor.addprevious(p._p)
        if style=='Normal':p.paragraph_format.line_spacing=1.5;p.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
        return p
    def image_at(index,name,caption,capindex,width=5.7):
        p=original[index];p.clear();p.add_run().add_picture(str(ASSETS/name),width=Inches(width));p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        change(capindex,caption)
    def selection_figure(name,caption):
        p=add_before(end,'');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.line_spacing=1;p.paragraph_format.keep_with_next=True
        p.add_run().add_picture(str(ASSETS/name),width=Inches(5.65))
        p=add_before(end,caption,CAP);p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.line_spacing=1;p.paragraph_format.space_after=Pt(8)

    # Preserve the template geometry, logos and cover hierarchy, while allowing the long title to fit.
    for p in original[:51]:
        if not p.text.strip() and not p._p.xpath('.//w:drawing') and (p._p.pPr is None or p._p.pPr.sectPr is None):
            p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(0)
            p.paragraph_format.line_spacing=Pt(3)
            for r in p.runs:r.font.size=Pt(3)
    for p in [original[3],original[24]]:
        p.paragraph_format.space_before=Pt(10);p.paragraph_format.space_after=Pt(10)
    original[3].paragraph_format.space_before=Pt(20)
    change(89,'Se desarrolló AssistiveVision, una aplicación Android que identifica diez clases de objetos y comunica su posición relativa mediante voz local en español e inglés. La selección inicial comparó seis configuraciones de detectores sobre 80 imágenes y 257 anotaciones; EfficientDet-Lite2 obtuvo AP50 de 0,648 y una latencia aislada de 124,9 ms en CPU de un Redmi Note 13. Para evaluar el montaje y el lente se construyó un segundo conjunto de 198 fotografías de iPhone, organizadas en 33 grupos de seis capturas sucesivas y corregidas manualmente hasta obtener 889 anotaciones. Las imágenes se reprodujeron con los módulos de producción de Android en un emulador Pixel 8, con confianza 0,30 e IoU mínimo 0,50. Gorillapod 0,5x produjo el mayor número de detecciones correctas (82), mientras el arnés de pecho 1x obtuvo la mayor F1 (61,9 %). La ventaja del Gorillapod sobre pecho 1x fue de 0,515 detecciones por escena, con IC bootstrap del 95 % de 0,121 a 0,939; frente a pecho 0,5x no quedó establecida. La profundidad se exploró mediante estimaciones geométricas, sin validar un rango operativo. Los resultados sustentan una selección provisional por cobertura y requieren confirmación con escenas nuevas, distancias medidas, el teléfono de destino y usuarios finales.')
    change(92,'AssistiveVision was developed as an Android application that identifies ten object classes and describes their relative position through offline speech in Spanish and English. An initial comparison of six detector configurations used 80 images and 257 annotations; EfficientDet-Lite2 achieved AP50 of 0.648 and isolated CPU latency of 124.9 ms on a Redmi Note 13. Mount and lens evaluation used a separate set of 198 iPhone photographs arranged in 33 successive six-capture groups, with 889 manually corrected annotations. Production Android preprocessing and detection modules replayed all photographs on a Pixel 8 emulator, using confidence 0.30 and minimum IoU 0.50. Gorillapod 0.5x produced the most correct detections (82), whereas chest harness 1x achieved the highest F1 (61.9%). Gorillapod exceeded chest 1x by 0.515 correct detections per scene, with a paired 95% bootstrap interval of 0.121 to 0.939; its advantage over chest 0.5x was not established. Geometric distance estimates supported an exploratory depth analysis rather than a validated operating range. The findings support a provisional coverage-based choice, subject to validation on new scenes, measured distances, the target phone and end users.')
    change(93,'Keywords: object detection; assistive technology; Android; EfficientDet; object coverage; offline speech.')
    original[92].style=doc.styles['Normal'];original[92].paragraph_format.line_spacing=1.5;original[92].alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
    original[91].paragraph_format.page_break_before=True
    for index in (151,169,189):original[index].paragraph_format.page_break_before=True
    for index in (363,453,457):original[index].paragraph_format.page_break_before=True
    change(90,'Palabras clave: detección de objetos; tecnología de asistencia; Android; EfficientDet; cobertura de objetos; voz local.')
    change(256,'El desempeño depende del dispositivo, el encuadre, la iluminación y las oclusiones. La localización describe regiones bidimensionales del campo visual y no estima distancias ni garantiza movilidad segura. El capítulo 4 analiza fotografías reproducidas en Android y distancias aproximadas, por lo que sus resultados no equivalen a una evaluación de navegación, comprensión del habla o desempeño con usuarios finales.')
    change(258,'El trabajo se desarrolló en tres fases: revisión de literatura y definición del sistema; comparación de modelos y construcción del prototipo; y evaluación de las configuraciones de captura. La selección inicial empleó 80 imágenes y un benchmark aislado en Redmi Note 13. La evaluación posterior utilizó 198 fotografías, anotaciones corregidas y reproducción de los módulos Android en un emulador Pixel 8. Ambos conjuntos y entornos se analizan por separado. La profundidad se estudió de forma exploratoria con geometría y EXIF; la validación con distancias medidas y usuarios permanece como trabajo posterior.')
    change(262,'El capítulo 1 presenta la literatura y las arquitecturas de detección. El capítulo 2 documenta la selección inicial del modelo y sus mediciones en escritorio y Redmi Note 13. El capítulo 3 describe la implementación actual del prototipo. El capítulo 4 analiza las 198 fotografías por montaje, lente y banda de distancia estimada. El capítulo 5 reúne conclusiones, recomendaciones y trabajo futuro; los anexos permiten localizar el código, reproducir la evaluación y utilizar la aplicación.')
    change(273,'Estos antecedentes justifican una arquitectura que ejecute la inferencia localmente, limite la información anunciada y traduzca la caja detectada a una zona espacial comprensible. AssistiveVision adopta un modo manual bajo demanda y una localización bidimensional por zonas. El capítulo 4 explora la relación entre detección y distancia estimada; la validación con distancias medidas permanece pendiente.')
    change(304,'AP50 es la precisión promedio de detección al exigir IoU mínimo de 0,50 y coincidencia de clase. IoU es el área de intersección de las cajas dividida entre su área de unión; no equivale a cubrir simplemente la mitad del objeto. COCO calcula AP a partir de la curva precisión-recall y promedia las categorías evaluables. Un error de clase produce una predicción falsa y deja sin recuperar la anotación de la clase correcta [13].')
    change(307,'Recall, o exhaustividad, es la proporción de instancias anotadas visibles que el detector recupera: TP/(TP+FN). Los falsos negativos describen objetos presentes en la imagen y no detectados; un objeto fuera del encuadre no entra en el denominador. Por ello, este trabajo acompaña recall con los conteos de objetos visibles y detecciones correctas. Estas métricas no miden directamente riesgo de colisión ni seguridad de navegación.')
    change(313,'La reducción de precisión numérica, por ejemplo de pesos Float32 a Float16, puede disminuir el tamaño del archivo. Su efecto sobre la latencia y la exactitud depende del modelo, del backend y del hardware; requiere medición. La cuantización entera, como INT8, introduce además escalas y desplazamientos que deben respetarse durante la inferencia. El formato de los pesos y el tipo del tensor de entrada son propiedades distintas [3].')
    change(316,'En escritorio se calculó AP mediante pycocotools y precisión, recall y F1 mediante emparejamiento por clase e IoU. El protocolo COCO y el cálculo de métricas a un umbral fijo se documentan por separado para distinguir la evaluación de la curva de puntuaciones de la operación del prototipo [13].')
    change(348,'SSD MobileNetV1 obtuvo la menor latencia aislada (23,4 ms, 42,75 inferencias/s) y el menor AP50-95 (0,336) del conjunto inicial. Estos resultados describen un compromiso entre velocidad y ajuste de las cajas; su efecto sobre descriptores espaciales requiere una evaluación específica de la localización.')
    change(351,'En el conjunto inicial, YOLOv8s y EfficientDet-Lite2 alcanzaron F1 de 0,702 y 0,695. SSD MobileNetV1 obtuvo precisión de 0,343 y recall de 0,545, lo que implica abundantes predicciones falsas y objetos sin recuperar a ese umbral. YOLO11n Float32 obtuvo precisión de 0,723 y recall de 0,619. Estas cifras corresponden a detecciones en imágenes; no representan la tasa de anuncios de voz, que también depende del filtrado y la selección de objetos.')
    change(353,'Float16 no ofreció una mejora apreciable de velocidad en las mediciones del Redmi Note 13: las diferencias de YOLO11n entre variantes fueron inferiores a 10 ms. Las métricas de exactitud también fueron próximas. Se observó una reducción del tamaño de archivo, pero el experimento no permite atribuir las diferencias a una limitación específica de las unidades aritméticas del procesador o de la GPU.')
    change(355,'La CPU obtuvo mayor velocidad que GPU Delegate en los modelos medidos en el Redmi Note 13: YOLO11n Float32 pasó de 5,30 a 3,85 inferencias/s; EfficientDet-Lite2, de 8,00 a 2,79; y YOLOv8s Float32, de 1,61 a 1,34. Esta observación sustenta el uso de CPU para esa configuración. El mecanismo causal exacto de la pérdida de rendimiento no se aisló y no debe generalizarse a otras GPU o teléfonos.')
    change(362,'EfficientDet-Lite2 en CPU fue seleccionado por su AP50 de 0,648, recall de 0,677 y latencia aislada de 124,9 ms en Redmi Note 13. Frente a YOLO11n Float32 (AP50 0,615 y 188,6 ms), ofreció mayor AP50, menor latencia y menor consumo de RAM (65,8 frente a 80,5 MB). YOLO11n obtuvo mayor AP50-95 (0,498 frente a 0,486). La elección responde al conjunto y al dispositivo evaluados; la capacidad para recuperar objetos y los tiempos del sistema completo se verifican de forma independiente.')
    change(366,'El flujo actual comprende captura, preprocesamiento, detección, selección por confianza y número máximo de objetos, localización en la imagen y generación de voz. La Figura 3.1 representa el orden ejecutado por MainViewModel. La inversión del letterbox devuelve las cajas al fotograma original antes de asignar las zonas. Los módulos de inferencia y audio se inicializan una vez y se liberan al finalizar su ciclo de vida.')
    image_at(367,'arquitectura.png','Figura 3.1. Flujo de procesamiento de la implementación actual.',368)
    change(370,'Se compararon arnés de cabeza, arnés de pecho y soporte flexible Gorillapod. Las capturas de evaluación son verticales y combinan dos campos visuales nominales, 1x y 0,5x. La altura y la inclinación no se registraron como mediciones experimentales, por lo que no se prescribe un ángulo o una altura óptima. El capítulo 4 compara su cobertura y detecciones a partir de los grupos de fotografías disponibles.')
    change(372,'CameraX 1.6.1 gestiona la cámara y su ciclo de vida [29]. Preview mantiene la vista de la escena e ImageAnalysis entrega fotogramas RGBA_8888 con STRATEGY_KEEP_ONLY_LATEST. FrameStore conserva una copia utilizable del fotograma más reciente. La política de selección de cámara distingue la cámara trasera principal de alternativas de campo amplio, sujetas a las capacidades del dispositivo; el 0,5x del conjunto iPhone no demuestra una focal equivalente en Android.')
    change(373,'La inferencia se ejecuta bajo demanda. Al pulsar Capturar fotograma, la aplicación copia el último fotograma disponible y congela la vista mientras procesa la escena y reproduce la voz. No vuelve a aceptar una captura mientras la anterior está activa. El fin del audio o un error desbloquean la vista; un temporizador de respaldo de 20 s evita que quede congelada indefinidamente.')
    change(377,'DetectionModule utiliza la API Interpreter del paquete LiteRT 1.4.2 y el archivo efficientdet-lite2-detection-metadata.tflite, cargado mediante un MappedByteBuffer [32]. La inferencia se ejecuta en CPU. Se leen cajas normalizadas, clases, puntuaciones y número de detecciones; el intérprete valida la forma del tensor de cajas al inicializarse.')
    change(381,'LocalizationModule asigna la zona según el centro de la caja en coordenadas del fotograma original. Los límites horizontales son 0,35 y 0,65 del ancho; el límite vertical es la mitad de la altura. Estas divisiones producen seis zonas y no constituyen tercios exactos ni posiciones métricas en el espacio. La Tabla 3.2 y la Figura 3.2 muestran esta partición.')
    image_at(383,'zonas.png','Figura 3.2. Partición del campo visual para la localización relativa.',384,5.3)
    change(386,'La implementación actual filtra por confianza, ordena las detecciones y limita la lista a uno, dos o tres objetos, con dos por defecto. La captura manual regula cuándo se procesa y se anuncia la escena. El antiguo filtro por período de enfriamiento no participa en este flujo; describirlo como una función activa introduciría una diferencia entre el informe y el código evaluado.')
    change(388,'AudioModule utiliza sherpa-onnx v1.13.6 para sintetizar voz local a partir de modelos VITS/Piper empaquetados con la aplicación [31]. El catálogo incluye es_MX-claude-high-int8 para español y en_US-amy-low-int8 para inglés, junto con los datos de fonemización necesarios. La implementación actual no depende del servicio TextToSpeech de Android ni de una solicitud de síntesis por red.')
    change(389,'SpeechFormatter construye una oración con artículos y conectores localizados. Por ejemplo: «Hay una persona donde estás apuntando y una silla abajo a la izquierda de donde estás apuntando». Las voces y la velocidad se seleccionan según las preferencias. La reproducción se realiza mediante AudioTrack; la terminación y los errores se comunican al flujo de captura para liberar el fotograma congelado. El experimento de detección no mide inteligibilidad, naturalidad ni tiempo total de síntesis.')
    change(391,'El modo evaluado es manual: el usuario activa Capturar fotograma y recibe una descripción de los objetos seleccionados. La Figura 3.3 muestra los estados principales de la interacción. La evaluación de imágenes reproduce el procesamiento de detección, pero no mide la interacción completa ni el consumo energético.')
    change(392,'La exploración continua por voz se plantea como ampliación futura. El código y los resultados de este informe no sustentan una frecuencia de análisis automático ni una evaluación de usabilidad de ese modo.')
    change(396,'La opción de mostrar la vista previa controla la presentación de la imagen. No se midió su efecto sobre consumo energético o privacidad percibida, por lo que esos beneficios no se presentan como resultados experimentales.')
    change(398,'La interfaz incluye vista previa, captura manual y acceso a configuración, con textos localizados. Durante el procesamiento conserva el fotograma seleccionado y muestra las detecciones y su información espacial. La secuencia de estados se resume en la Figura 3.3; los controles y textos concretos se encuentran en los recursos del proyecto Android.')
    image_at(399,'interaccion.png','Figura 3.3. Secuencia de interacción manual y liberación de la captura.',400)
    change(402,'La revisión actual se verificó mediante 34 pruebas JVM sin fallos: localización (6), geometría letterbox (6), formato de descriptores (7), política de lentes (5), catálogo de voces (7), tecla de captura (2) y una prueba básica (1). Además, la reproducción de las 198 imágenes completó una prueba de instrumentación Android. Ocho pruebas del evaluador y de la estadística verifican emparejamiento, casos vacíos, bootstrap y cálculo de p-valores.')
    change(403,'El benchmark aislado de EfficientDet-Lite2 en el Redmi Note 13 registró 124,9 ms (capítulo 2). La reproducción posterior en emulador obtuvo una mediana de 246,3 ms para el método de detección y 104,0 ms para decodificación y preprocesamiento. Estos alcances son distintos y no se suman sus medianas para estimar una mediana total. La cifra histórica de 137,8 ms incluida en el README de la aplicación no dispone aquí de un registro comparable del flujo completo; no se usa como medición validada del sistema actual ni se equipara a 8,55 FPS.')

    # Correct the source configuration table to the actual application.
    config=doc.tables[9]
    for row in list(config.rows):
        if any(k in row.cells[0].text.lower() for k in ('enfriamiento','cooldown','anuncios')):remove(row._tr)
    matrix=doc.tables[3]
    values=[[c.text for c in row.cells] for row in matrix.rows]
    transposed=doc.add_table(rows=1,cols=7)
    for c,v in zip(transposed.rows[0].cells,['Clase','YOLOv8s\nF32','YOLOv8s\nF16','YOLO11n\nF32','YOLO11n\nF16','SSD\nMobileNetV1','EfficientDet\nLite2']):c.text=v
    for j in range(1,len(values[0])):
        for c,v in zip(transposed.add_row().cells,[values[0][j]]+[row[j] for row in values[1:]]):c.text=v
    matrix._tbl.addprevious(transposed._tbl);remove(matrix._tbl)
    # Replace Chapter 4, preserving its section break and the original chapter title.
    start=original[406]._p;end=original[430]._p
    node=start
    while node is not end:
        nxt=node.getnext();remove(node);node=nxt
    chapter=Document(REPO/'Documents/Fragments/Capitulo 4 - Diseño experimental.docx')
    table_number=0
    table_titles=['Diseño y unidades de análisis','Resultados agrupados por montaje','Pruebas t pareadas por montaje','Resultados por configuración','Comparación de conteos con Gorillapod 0,5x','Recall por banda de distancia estimada','Resultados por clase en el conjunto completo']
    # Build relationship-backed images with the destination document rather than copying rIds.
    picture_paths=iter([RESULTS/'scenario1/boxplot_mount.png',RESULTS/'scenario1/boxplot_configuration.png',RESULTS/'depth/depth_recall.png'])
    for el in chapter.element.body:
        if el.tag==qn('w:sectPr'):continue
        if el.tag==qn('w:p'):
            txt=''.join(el.xpath('.//w:t/text()'))
            if el.xpath('.//w:drawing'):
                p=add_before(end,'');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.line_spacing=1
                p.add_run().add_picture(str(next(picture_paths)),width=Inches(5.65));continue
            if not txt.strip():continue
            sid=el.xpath('./w:pPr/w:pStyle/@w:val')
            style=H2 if sid and sid[0]=='Heading1' else H3 if sid and sid[0]=='Heading2' else CAP if sid and sid[0]=='Caption' else 'Normal'
            if 'En el rango' in txt:pass
            if style==CAP and txt.startswith('Figura 4.'):
                number=int(txt.split('.')[1])
                txt={1:'Figura 4.1. Objetos correctos por fotografía y montaje.',2:'Figura 4.2. Objetos correctos por fotografía en las seis configuraciones.',3:'Figura 4.3. Recall por distancia estimada e intervalo bootstrap del 95 %.'}[number]
            if table_number==7 and txt.startswith('Dos observaciones'):
                add_before(end,'Los resultados por clase de la Tabla 4.7 describen qué objetos resultan más difíciles; la Figura 4.4 complementa ese desglose comparando precisión, recall y F1 de las seis configuraciones. En cada panel se distinguen el detector y la lista de hasta dos objetos por fotografía. Ambos se evalúan con confianza 0,30, coincidencia de clase e IoU mínimo de 0,50, y el recall conserva como denominador todas las instancias anotadas visibles. Cada configuración reúne 33 fotografías; la escala común de 0 a 100 % permite comparar las magnitudes sin alterar sus definiciones.')
                selection_figure('seleccion_metricas.png','Figura 4.4. Precisión, recall y F1 del detector y de la lista de hasta dos objetos.')
                add_before(end,'La Figura 4.4 permite interpretar el costo de limitar la información anunciada. Para Gorillapod 0,5x, la precisión pasa de 72,6 % en el detector a 90,7 % en la lista, mientras el recall baja de 47,1 % a 28,2 %: se conservan 49 selecciones correctas frente a las 82 detecciones correctas previas al límite. Pecho 1x mantiene la mayor F1 del detector (61,9 %), aunque recupera menos objetos correctos en total. La lista prioriza las puntuaciones más altas y reduce la cantidad recuperada; su mayor precisión no demuestra por sí sola mejor comprensión o utilidad del mensaje. Por ello, la elección combina esta figura con los conteos de la sección 4.3 y conserva la selección de Gorillapod 0,5x como provisional cuando se prioriza cantidad.')
                txt='La Tabla 4.4 aporta una dimensión adicional: AP50-95 promedia umbrales de IoU más exigentes que AP50. En pecho 1x se obtienen 60,5 % y 42,2 %, respectivamente; la diferencia describe la sensibilidad de la evaluación al ajuste de las cajas y no aísla su causa. La Figura 4.4 utiliza un IoU fijo de 0,50, por lo que complementa ese resultado sin sustituirlo. El efecto de las imprecisiones de las cajas sobre la zona espacial anunciada requiere una evaluación específica.'
            if table_number==7 and txt.startswith('Finalmente, el límite de dos objetos'):
                continue  # The discussion following Figure 4.5 now develops this tradeoff.
            if table_number==2 and txt.startswith('Cada posición suma'):
                txt='Cada posición reúne 66 fotografías (33 grupos × 2 lentes). La tabla presenta conteos y métricas del detector; el análisis de la lista de dos objetos se describe después de la Figura 4.1.'
            if table_number==7 and txt.startswith('"Correctas/foto"'):
                txt='Resultados por clase agrupados sobre las 198 fotografías, con confianza 0,30 e IoU mínimo 0,50. Las diferencias entre clases impiden interpretar el total como utilidad uniforme para todos los objetos.'
            if 'sigue siendo confiable' in txt:txt=txt.replace('sigue siendo confiable','presenta mayor recall observado')
            if 'El conteo por escena alcanza el mejor resultado con detección no nula' in txt:txt=txt.replace('El conteo por escena alcanza el mejor resultado con detección no nula','Se obtiene al menos una detección correcta')
            p=add_before(end,txt,style)
            if style==CAP:p.paragraph_format.line_spacing=1;p.paragraph_format.space_after=Pt(8);p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        elif el.tag==qn('w:tbl'):
            table_number+=1
            add_before(end,f'Tabla 4.{table_number}. {table_titles[table_number-1]}.',CAP)
            clone=deepcopy(el)
            if table_number==2:
                # Keep comparable detection metrics in a readable portrait table.
                for tr in clone.findall(qn('w:tr')):
                    cells=tr.findall(qn('w:tc'))
                    for j in [10,9,5,1]:remove(cells[j])
                grid=clone.find(qn('w:tblGrid'));cols=list(grid)
                for j in [10,9,5,1]:remove(cols[j])
            if table_number==7:
                counts={}
                for r in read_csv('per_class.csv'):
                    if r['mode']=='detector':
                        arr=counts.setdefault(r['category'],[0,0,0])
                        for j,k in enumerate(('tp','fp','fn')):arr[j]+=int(r[k])
                t=doc.add_table(rows=1,cols=7)
                for c,v in zip(t.rows[0].cells,['Clase','TP','FP','FN','Precisión','Recall','F1']):c.text=v
                for name,(tp,fp,fn) in sorted(counts.items()):
                    vals=[name,tp,fp,fn,f'{tp/(tp+fp):.1%}',f'{tp/(tp+fn):.1%}',f'{2*tp/(2*tp+fp+fn):.1%}']
                    for c,v in zip(t.add_row().cells,vals):c.text=str(v).replace('.',',')
                clone=t._tbl;end.addprevious(clone)
            else:end.addprevious(clone)
    # Add audit-specific interpretation not available in the initial fragment.
    add_before(end,'La auditoría EXIF identificó seis discrepancias entre el grupo de lente nominal y el campo focal registrado, además de una variación menor de 25 a 26 mm. Se conservan las etiquetas originales del protocolo para mantener la trazabilidad; las comparaciones de lente son provisionales hasta revisar esas capturas. Las bandas publicadas reúnen 883 de las 889 instancias: seis estimaciones inferiores a 0,5 m quedan fuera del gráfico. La columna Media bootstrap es la media de los recalls agrupados calculados en las remuestras, no una media de recalls de escenas igualmente ponderadas.')
    # Conclusions and practical next work.
    change(433,'La comparación inicial sustentó la selección de EfficientDet-Lite2 para el Redmi Note 13: AP50 de 0,648, recall de 0,677 y latencia aislada de 124,9 ms. La aplicación actual integra CameraX, LiteRT, geometría letterbox, localización en seis zonas y síntesis de voz local con sherpa-onnx. Las pruebas de lógica y la reproducción Android respaldan la ejecución de los componentes; no constituyen validación con usuarios finales.')
    change(434,'La evaluación de captura completó 198 fotografías, 889 anotaciones revisadas y 33 grupos pareados. Gorillapod 0,5x produjo 82 detecciones correctas y recuperó al menos un objeto en 29 escenas; el arnés de pecho 1x obtuvo la mayor F1, de 61,9 %. La elección por cantidad favorece provisionalmente Gorillapod 0,5x, mientras la elección por equilibrio precisión-recall favorece pecho 1x. Las comparaciones no establecen un ganador universal y deben confirmarse en escenas nuevas.')
    change(435,'Los conteos por escena mostraron una ventaja de Gorillapod 0,5x frente a pecho 1x de 17 detecciones (0,515 por escena; IC bootstrap del 95 % de 0,121 a 0,939). Frente a pecho 0,5x, el intervalo incluyó cero. Al agrupar lentes, la diferencia Gorillapod-pecho no fue significativa en la prueba t corregida (p = 0,113). El límite de dos objetos aumentó precisión y redujo recall; la utilidad de ese intercambio para quien escucha requiere evaluación de audio e interacción.')
    change(436,'La exploración de profundidad sugiere menor recall en las bandas geométricamente estimadas más lejanas, pero no establece un alcance físico de 4 m. El tamaño de referencia de cada clase, la oclusión y la composición de objetos confunden la relación con la distancia. Tampoco se midieron navegación, reducción de colisiones, autonomía, comprensión de los mensajes ni ahorro energético. El aporte demostrado es un prototipo reproducible y una evaluación de detección con alcance explícito.')
    change(438,'Se recomienda utilizar conjuntamente conteos, cobertura, precisión, recall y métricas por clase; revisar las discrepancias EXIF antes de fijar conclusiones sobre lentes; mantener separados los resultados históricos de Redmi y los de emulador; conservar imágenes, etiquetas, predicciones, código y versiones; y reproducir la selección en el teléfono de destino. La salida de voz debe regularse según pruebas de comprensión y carga informativa, no solo según el número máximo de objetos recuperados.')
    change(440,'El trabajo posterior comprende una segunda revisión independiente de anotaciones; identificación de objetos compartidos entre vistas; validación de Gorillapod 0,5x en escenas nuevas y con el teléfono físico; un protocolo de distancias medidas y calibración óptica; y evaluación de inteligibilidad, tiempos de respuesta y uso con personas con discapacidad visual. La síntesis local ya está integrada; su comparación con otros motores y la incorporación de audio espacial, vibración o exploración continua requieren experimentos propios.')
    change(449,'La ejecución actual de :app:testDebugUnitTest completó 34 pruebas sin fallos. Los resultados de JUnit se conservan con la revisión técnica del informe. La prueba DatasetBenchmarkTest reprodujo las 198 imágenes por los módulos de producción, y las ocho pruebas de Python verificaron el evaluador y la función de p-valores corregida.')
    change(450,'Las pruebas del prototipo cubren LocalizationModule (6), LetterboxMapper (6), SpeechFormatter (7), CameraLensPolicy (5), TtsVoiceCatalog (7), ShutterKeyPolicy (2) y una comprobación básica (1). La detección de objetos y la síntesis de audio requieren además pruebas de integración y validación con usuarios; la cobertura JVM no sustituye esas comprobaciones.')
    change(451,'En el evaluador se comprueban correspondencia uno a uno, duplicados, clase incorrecta, imágenes vacías, cajas degeneradas y bootstrap. La estadística se verifica con la identidad de la distribución Cauchy (un grado de libertad), integración numérica independiente de la densidad Student-t, simetría y pares idénticos. Estos casos detectan la regresión que antes alteraba los p-valores.')
    change(452,'Los conteos y predicciones del benchmark permanecen sin cambios. La corrección estadística actualiza p-valores y su interpretación, sin repetir la inferencia ni modificar la verdad de campo.')
    change(454,'Manual técnico. El proyecto Android se conserva en diomedescerda/AssistiveVision. La revisión evaluada es 85c852ddcb543bce1bd69ad0db307f895d597881; declara compileSdk 37 con minor API 1, minSdk 26, AGP 9.3.1 y Gradle 9.5.0. La compilación verificada empleó el JBR de Android Studio; el objetivo Java 11 del código no debe confundirse con el JDK necesario para ejecutar Gradle. El comando ./gradlew assembleDebug genera el APK. Build/Testing/README.md documenta la reproducción, los hashes y los límites de cada ejecución.')
    change(455,'Manual de usuario. Coloque el teléfono con la cámara trasera despejada y seleccione un montaje estable. Abra AssistiveVision y conceda permiso de cámara. Ajuste idioma, velocidad de voz, confianza, número máximo de objetos y vista previa en Configuración. Espere la vista de la escena y pulse Capturar fotograma; escuche la descripción y vuelva a capturar cuando la vista se libere. La zona anunciada describe la dirección dentro de la imagen, no una distancia ni una ruta libre. Las detecciones omitidas o falsas requieren que el prototipo se utilice como apoyo informativo, junto con las ayudas habituales del usuario.')
    add_before(original[447]._p,'Build/Testing conserva labels.json (anotación revisada), benchmark/results/android.json (predicciones) y los scripts de métricas, escenas, estadística y profundidad. Los borradores no son etiquetas finales. verify_package.py comprueba el archivo base; Documents/Review registra esta revisión.')
    # Actual configuration table contents.
    for row in config.rows:
        if 'máximo' in row.cells[0].text.lower():row.cells[1].text='1, 2 o 3';row.cells[2].text='2'
    # Remove glossary sample text and excessive empty template scaffolding.
    for p in original[190:239]:
        if p._p.getparent() is not None:remove(p._p)
    anchor=original[239]._p
    for term,meaning in [('AP','Precisión promedio sobre la curva precisión-recall'),('COCO','Common Objects in Context'),('EXIF','Metadatos de captura de la fotografía'),('F1','Media armónica de precisión y recall'),('FN','Falso negativo'),('FP','Falso positivo'),('FPS','Fotogramas por segundo'),('GT','Anotación de referencia o verdad de campo'),('IC','Intervalo de confianza'),('IoU','Intersección sobre unión de cajas'),('m','Metro'),('ms','Milisegundo'),('px','Píxel'),('RGB','Canales rojo, verde y azul'),('TP','Verdadero positivo')]:
        p=add_before(anchor,f'{term}\t{meaning}','Sinespaciado')
        p.paragraph_format.tab_stops.add_tab_stop(Inches(.85))
        p.paragraph_format.space_after=Pt(5)
    # Bibliography additions verified against official documentation and archived source.
    doc.add_paragraph('[31] k2-fsa, “Text-to-speech,” sherpa-onnx documentation. [Online]. Available: https://k2-fsa.github.io/sherpa/onnx/tts/index.html. Consultado: 14 oct. 2026.')
    doc.add_paragraph('[32] Google, “LiteRT for Android,” Google AI Edge. [Online]. Available: https://developers.google.com/edge/litert/android. Consultado: 14 oct. 2026.')
    doc.add_paragraph('[33] D. Cerda, “AssistiveVision,” código fuente, revisión 85c852ddcb543bce1bd69ad0db307f895d597881. [Online]. Available: https://github.com/diomedescerda/AssistiveVision.')
    from align_proposal import apply
    apply(doc, original, add_before, change, H2, H3, CAP)
    # Heading styles contain a near-transparent textFill inherited from the source.
    for sid in [H1,H2,H3]:
        st=doc.styles[sid]
        for el in st.element.xpath('.//*[local-name()="textFill"]'):remove(el)
    # Portrait tables: scale grid and cells, repeat headers and prevent row splitting.
    for t in doc.tables:
        if len(t.columns)==1:continue
        n=len(t.columns);widths=[1.45]+[(6.08-1.45)/(n-1)]*(n-1)
        if n==3:widths=[2.1,2.45,1.53]
        if t.cell(0,0).text=='Oclusión':widths=[1.35,.60,.60,.60,.85,2.08]
        if t.cell(0,0).text=='Requerimiento':widths=[1.40,2.05,2.63]
        if 'Banda de distancia' in t.cell(0,0).text:widths=[.94,.60,.60,.64,.82,1.0,1.48]
        t.autofit=False
        borders=OxmlElement('w:tblBorders')
        for edge in ('top','left','bottom','right','insideH','insideV'):
            border=OxmlElement('w:'+edge);border.set(qn('w:val'),'single');border.set(qn('w:sz'),'4');border.set(qn('w:color'),'D9D9D9');borders.append(border)
        for old in t._tbl.tblPr.findall(qn('w:tblBorders')):remove(old)
        t._tbl.tblPr.append(borders)
        grid=t._tbl.tblGrid
        for el in list(grid):grid.remove(el)
        for width in widths:
            el=OxmlElement('w:gridCol');el.set(qn('w:w'),str(round(width*1440)));grid.append(el)
        for ri,row in enumerate(t.rows):
            props=row._tr.get_or_add_trPr();props.append(OxmlElement('w:cantSplit'))
            if ri==0:props.append(OxmlElement('w:tblHeader'))
            for ci,c in enumerate(row.cells):
                c.width=Inches(widths[ci]);c.vertical_alignment=1
                if ri==0:
                    sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'EEEEEE');c._tc.get_or_add_tcPr().append(sh)
                for p in c.paragraphs:
                    p.paragraph_format.line_spacing=1;p.paragraph_format.space_after=Pt(3)
                    for r in p.runs:r.font.name='Arial';r.font.size=Pt(9 if n>=6 else 10);r.bold=ri==0
    # Fill missing contents lists with bookmark-backed cached page references.
    # Remove the original TOC fields/results; new caches are refreshed after rendering.
    groups=[(original[97]._p,original[150]._p,'contents'),(original[152]._p,original[168]._p,'figures'),(original[170]._p,original[188]._p,'tables')]
    bookmarks=[];bid=1000
    entries=[];figure_entries=[];table_entries=[]
    for p in doc.paragraphs:
        text=p.text.strip();sid=p.style.style_id
        if not text:continue
        kind=None
        if sid not in ('TDC1','TDC2') and (sid in (H1,H2) or text.startswith('Anexo ') or sid in ('Ttulosposteriores','Ttulospreliminares2')):
            if text!='Agradecimientos':
                kind='contents'
        if sid==CAP and re.match(r'Figura \d+\.\d+\.',text):kind='figures'
        if sid==CAP and re.match(r'Tabla \d+\.\d+\.',text):kind='tables'
        if kind:
            name=f'report_{bid}';start=OxmlElement('w:bookmarkStart');start.set(qn('w:id'),str(bid));start.set(qn('w:name'),name)
            endmark=OxmlElement('w:bookmarkEnd');endmark.set(qn('w:id'),str(bid));p._p.insert(0,start);p._p.append(endmark)
            bid+=1;entry=dict(name=name,text=text,kind=kind,level=2 if sid==H2 else 1)
            bookmarks.append(entry)
    for start,end,kind in groups:
        node=start
        while node is not end:
            nxt=node.getnext();remove(node);node=nxt
        add_before(end,'Pág.','TDC1')
        for entry in [x for x in bookmarks if x['kind']==kind]:
            p=add_before(end,entry['text']+'\t','TDC2' if entry['level']==2 else 'TDC1')
            p.paragraph_format.line_spacing=1;p.paragraph_format.space_after=Pt(4)
            p.alignment=WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.tab_stops.clear_all()
            p.paragraph_format.tab_stops.add_tab_stop(Inches(6.08),WD_TAB_ALIGNMENT.RIGHT,WD_TAB_LEADER.DOTS)
            if kind!='contents':
                for r in p.runs:r.bold=False
            field=OxmlElement('w:fldSimple')
            roman=' \\* ROMAN' if entry['text'] in ('Resumen','Abstract','Contenido','Lista de figuras','Lista de tablas','Lista de símbolos') else ''
            field.set(qn('w:instr'),f' PAGEREF {entry["name"]} \\h{roman} ')
            r=OxmlElement('w:r');text=OxmlElement('w:t');text.text='0';r.append(text);field.append(r);p._p.append(field)
    settings=doc.settings.element
    update=settings.find(qn('w:updateFields'))
    if update is None:update=OxmlElement('w:updateFields');settings.append(update)
    update.set(qn('w:val'),'true')
    for section in list(doc.sections)[2:4]:
        section.footer.is_linked_to_previous=False
        p=section.footer.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.RIGHT
        fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),' PAGE ')
        run=OxmlElement('w:r');txt=OxmlElement('w:t');txt.text='I';run.append(txt);fld.append(run);p._p.append(fld)
    doc.sections[4].footer.is_linked_to_previous=False
    for section in list(doc.sections)[2:5]:
        refs=section._sectPr.findall(qn('w:footerReference'))
        rid=next(ref.get(qn('r:id')) for ref in refs if ref.get(qn('w:type'))=='default')
        for kind in ('even','first'):
            for old in refs:
                if old.get(qn('w:type'))==kind:remove(old)
            ref=OxmlElement('w:footerReference');ref.set(qn('w:type'),kind);ref.set(qn('r:id'),rid)
            section._sectPr.insert(0,ref)
    # Preserve original page geometry; suppress duplicate automatic annex numbering.
    for p in doc.paragraphs:
        if p.text.startswith('Anexo '):
            pr=p._p.get_or_add_pPr();num=OxmlElement('w:numPr');val=OxmlElement('w:numId');val.set(qn('w:val'),'0');num.append(val);pr.append(num)
        if p.style.style_id==CAP:
            p.paragraph_format.line_spacing=1;p.paragraph_format.space_before=Pt(8);p.paragraph_format.space_after=Pt(8)
            p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:r.font.size=Pt(10)
            if p.text.startswith('Tabla '):p.paragraph_format.keep_with_next=True
        if p._p.xpath('.//w:drawing') and p.text=='':p.paragraph_format.keep_with_next=True
    temp=io.BytesIO();doc.save(temp)
    with zipfile.ZipFile(BASE) as source,zipfile.ZipFile(io.BytesIO(temp.getvalue())) as edited,zipfile.ZipFile(OUT,'w',zipfile.ZIP_DEFLATED) as dest:
        changed={'word/document.xml','word/_rels/document.xml.rels','word/styles.xml','word/settings.xml','[Content_Types].xml'}
        for name in source.namelist():
            data=edited.read(name) if name in changed else source.read(name)
            if re.match(r'word/header\d+\.xml$',name):
                root=E.fromstring(data)
                # Keep the template tables and PAGE fields, repair inherited stale chapter names.
                written=False
                for t in root.xpath('//w:t',namespaces=NS):
                    if not (t.text or '').strip().isdigit():
                        t.text='' if written or name=='word/header2.xml' else 'AssistiveVision';written=True
                for table in root.xpath('//w:tbl',namespaces=NS):
                    cells=table.xpath('./w:tr[1]/w:tc',namespaces=NS)
                    if len(cells)==2:
                        first_page=bool(cells[0].xpath('.//w:instrText[contains(text(),"PAGE")]',namespaces=NS))
                        widths=[900,7855] if first_page else [7855,900]
                        for g,width in zip(table.xpath('./w:tblGrid/w:gridCol',namespaces=NS),widths):g.set(qn('w:w'),str(width))
                        for c,width in zip(cells,widths):
                            c.find('w:tcPr/w:tcW',NS).set(qn('w:w'),str(width))
                for cell in root.xpath('//w:tc',namespaces=NS):
                    if cell.xpath('.//w:instrText[contains(text(),"PAGE")]',namespaces=NS):
                        for p in cell.xpath('.//w:p',namespaces=NS):
                            pr=p.find('w:pPr',NS)
                            if pr is None:pr=OxmlElement('w:pPr');p.insert(0,pr)
                            for ind in pr.findall(qn('w:ind')):remove(ind)
                            ind=OxmlElement('w:ind');ind.set(qn('w:left'),'0');ind.set(qn('w:right'),'0');ind.set(qn('w:firstLine'),'0');pr.append(ind)
                        tcw=cell.find('w:tcPr/w:tcW',NS)
                        if tcw is not None:tcw.set(qn('w:w'),'900')
                data=E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
            dest.writestr(name,data)
        for name in edited.namelist():
            if name not in source.namelist():dest.writestr(name,edited.read(name))
        # Python-docx records new PNG media types in this part.
        # Existing template already declares png, so no extra content type is required.
    (REPO/'Documents/scripts/informe_bookmarks.json').write_text(json.dumps(bookmarks,ensure_ascii=False,indent=2)+'\n')
    print(OUT)


if __name__=='__main__':main()
