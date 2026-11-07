"""Editorial content for the tutor revision. No experimental results are generated here."""

TITLE = 'Sistema de identificación y localización espacial de objetos basado en visión por computador para asistencia a personas con discapacidad visual'

# Keys identify paragraphs of the annotated attachment, before any reordering.
REPLACEMENTS = {
243: 'Cada objeto anotado se representa mediante una caja delimitadora y una clase. La intersección sobre unión (IoU, intersection over union) compara una caja predicha con una de referencia: IoU = área de intersección / área de unión. Su valor varía de 0 a 1. Una coincidencia requiere la clase correcta y un solapamiento que alcance el umbral elegido; exigir IoU ≥ 0,50 no significa simplemente cubrir la mitad del objeto. Las anotaciones y el evaluador siguen el formato de Microsoft Common Objects in Context (COCO) [22], [27].',
244: 'La precisión promedio (AP, average precision) resume la curva de precisión frente a exhaustividad para una clase al variar el umbral de puntuación. La media de precisión promedio entre clases (mAP, mean average precision) agrega las categorías evaluables. En este informe, mAP50 exige IoU ≥ 0,50; mAP50-95 promedia además diez umbrales, de 0,50 a 0,95 con incrementos de 0,05. El segundo indicador es más exigente respecto al ajuste geométrico. Las tablas por clase conservan AP50; los resultados agregados se denominan uniformemente mAP50 y mAP50-95, aunque los archivos del evaluador COCO utilicen las claves AP50 y AP50-95 [22], [27].',
245: 'Una detección emparejada correctamente es un verdadero positivo (TP, true positive); una predicción sin correspondencia es un falso positivo (FP, false positive), y una instancia anotada sin detección correcta es un falso negativo (FN, false negative). El emparejamiento es uno a uno: una anotación solo puede justificar un TP y una predicción duplicada puede convertirse en FP. Un error de clase no recupera la instancia de la clase verdadera [27].',
362: '4 Evaluación técnica del sistema y de las condiciones de captura',
363: '4.1 Diseño y protocolo de evaluación',
364: 'La evaluación aborda tres preguntas con un mismo archivo de fotografías: cómo varían las instancias visibles y correctamente detectadas entre montajes; qué cambia al combinar montaje y lente; y cómo se distribuye el recall en bandas de distancia estimada. Estas preguntas son líneas de análisis, no tres espacios físicos ni tres conjuntos nuevos. Primero se definen las unidades del estudio y se describen los espacios físicos; después se presenta la reproducción de las imágenes en Android y se interpretan los resultados. El cierre distingue esta evaluación de detección de la evidencia disponible sobre voz.',
365: '4.1.1 Espacios físicos y contenido de las capturas',
366: 'El análisis se organiza a partir de seis unidades de observación. Un inmueble es la edificación o vivienda donde se realiza la toma; un espacio físico (o recinto) es una habitación o zona real dentro de él; una escena es la disposición observable desde una orientación de la cámara; un grupo de captura (identificado con los códigos G01 a G33) reúne seis fotografías sucesivas tomadas en una misma ubicación para comparar las seis configuraciones de montaje y lente; y una fotografía es cada una de esas observaciones (33 × 6 = 198 fotografías en total, cifra que no equivale a 33 habitaciones distintas). Por su parte, una instancia corresponde a cada aparición anotada de un objeto dentro de una fotografía, de modo que un mismo objeto físico puede aportar varias instancias entre vistas.',
367: '4.1.2 Grupos de captura y configuraciones',
368: 'Dentro de cada grupo de captura (G01 a G33), las seis fotografías sucesivas corresponden a las seis configuraciones experimentales (c = 1 a 6), obtenidas al cruzar tres montajes del dispositivo (arnés de cabeza, arnés de pecho y palo de selfie dirigido hacia los objetos) con dos lentes nominales (1x y 0,5x). Como existen 33 grupos, cada configuración reúne 33 fotografías y cada posición de montaje agrupa 66 fotografías (33 grupos × 2 lentes), según el orden detallado en la Tabla 4.2.',
369: '4.1.3 Reproducción en Android y emparejamiento de cajas',
370: 'La prueba de instrumentación carga los archivos fotográficos e invoca los módulos de producción de preprocesamiento, detección y transformación inversa de coordenadas. No vuelve a fotografiar los espacios con la cámara Android. EfficientDet-Lite2 recibe 448 × 448 píxeles; cada imagen vertical se escala a 336 × 448 y se completa con gris 114. Se conservan candidatos desde puntuación 0,001 y hasta 15 detecciones para calcular mAP. La evaluación operativa aplica puntuación ≥ 0,30, coincidencia de clase e IoU ≥ 0,50. Las 198 imágenes se recorren en orden barajado con semilla 20261013, después de tres pasadas de calentamiento.',
371: '4.1.4 Anotaciones y variables de respuesta',
372: 'Las 198 fotografías proceden de un iPhone 12 Pro Max, con resolución de 1536 × 2048 y orientación vertical incorporada al archivo. Hay 889 instancias anotadas: persona (56), silla (438), sofá (11), cama (56), mesa de comedor (107), inodoro (38), televisor (50), computador portátil (34), lavamanos (56) y refrigerador (43). Dieciséis imágenes no contienen anotaciones de las diez clases y se conservan. El autor corrigió en Roboflow el borrador asistido de cajas y clases; trece cajas se recortaron a los límites por desviaciones mínimas de redondeo. La referencia final es labels.json. La integridad de los archivos se controla mediante sumas de verificación SHA-256, del algoritmo Secure Hash Algorithm de 256 bits.',
373: '4.1.5 Comparación pareada y alcance estadístico',
374: 'El emparejamiento estadístico compara dos configuraciones dentro de un mismo grupo, en lugar de contrastar fotografías sin relación. Por ejemplo, para cada grupo g (de G01 a G33) se calcula Δg = TPg,A − TPg,B; la media de esas 33 diferencias describe la ganancia por grupo. Al agrupar lentes, primero se suman dentro del grupo los dos conteos de cada montaje. Se aplica una prueba t de Student pareada con 33 pares y 32 grados de libertad (gl) [42]. Los intervalos de confianza (IC) del 95 % se obtienen mediante 10.000 remuestreos bootstrap de grupos completos, con semilla 20261013 [43], [44]. El remuestreo conserva juntas las seis vistas. Las comparaciones son exploratorias, sin ajuste por multiplicidad, y compartir un mismo recinto entre grupos puede reducir su independencia.',
377: '4.2 Comparación de posiciones de montaje',
378: 'El primer análisis agrupa los dos lentes y compara tres montajes. Cada montaje aporta dos fotografías por grupo y 66 fotografías en total. El propósito es describir por separado cuántas instancias quedan dentro de sus encuadres y cuántas de ellas recupera el detector. Los conteos no identifican objetos únicos entre vistas y no aíslan el efecto mecánico del soporte de la orientación usada al capturar.',
383: 'El pecho presenta la mayor F1 agrupada (60,2 %); el Gorillapod reúne más instancias visibles (319) y más detecciones correctas (157); la cabeza obtiene 126 correctas de 293 visibles y F1 de 53,1 %. La comparación muestra por qué cobertura y exactitud no son equivalentes: recuperar más instancias en total puede coexistir con una menor proporción recuperada. Las 13 imágenes de cabeza sin objetos objetivo anotados, frente a dos de pecho y una de Gorillapod, describen diferencias de encuadre; no demuestran por sí solas un fallo de clasificación.',
392: '4.3 Comparación de montaje y lente',
393: 'El segundo análisis conserva por separado las seis combinaciones de la Tabla 4.2. Cada una aporta 33 fotografías y se compara con las otras dentro de los mismos grupos. Las etiquetas 1x y 0,5x se mantienen como condiciones nominales del registro, sujetas a las discrepancias de metadatos descritas en la sección 4.6.',
407: '4.4 Detección por bandas de distancia estimada',
419: '4.5 Desempeño por clase y selección para la salida de voz',
420: 'El desempeño agrupado se complementa con resultados por clase y con la lista de hasta dos detecciones seleccionadas para componer el mensaje. Estas vistas responden a preguntas distintas: qué objetos recupera el detector y qué parte de esa información llega a la selección textual. El límite de salida no cambia el conjunto de instancias anotadas utilizado como denominador del recall.',
431: '4.6.1 Validez interna',
432: 'El emparejamiento por grupo mantiene una referencia de captura común, pero no hace idénticos los encuadres. Los grupos se reconstruyeron según el orden ascendente de los archivos, con estado provisional en capture_groups.csv, por lo que dicho registro no constituye una verificación independiente de los recintos. Las tomas son sucesivas y pueden cambiar la pose o la presencia de personas. Las cajas fueron corregidas por el autor, sin segunda auditoría humana independiente. Además, el Gorillapod se orientó hacia los objetos: se compara soporte junto con estrategia de encuadre. Elegir una configuración en este mismo conjunto favorece al ganador observado y exige confirmación en escenas nuevas.',
433: '4.6.2 Correspondencia entre métricas y uso previsto',
435: '4.6.3 Alcance de la generalización',
437: '4.6.4 Incertidumbre de las distancias',
438: 'Las distancias se estiman a partir de metadatos y alturas de referencia por clase, sin medición física ni calibración de cada objeto. La oclusión puede reducir la altura visible y sobreestimar la distancia; la mezcla de clases cambia entre bandas. La caída de recall alrededor de las bandas de 4 m describe este archivo y no establece un alcance operativo de la aplicación.',
439: '4.6.5 Alcance de las comparaciones estadísticas',
442: '4.7 Distribución del tiempo de procesamiento',
443: 'Se analizaron los tiempos guardados de las 198 fotografías, sin repetir inferencia. La ejecución retuvo candidatos desde puntuación 0,001; no corresponde a una nueva medición con corte de 0,30. La Tabla 4.10 resume mediana y percentiles: P25, P75 y P95 son los valores bajo los cuales se sitúa aproximadamente el 25 %, 75 % y 95 % de los tiempos. Se calculan mediante interpolación lineal en la posición (n − 1)q, donde n es el número de observaciones y q el cuantil entre 0 y 1 [47].',
447: '4.8 Brillo digital y oclusión observada',
448: 'La propuesta contempla iluminación y oclusión [10], pero la adquisición no documenta un protocolo de niveles controlados de iluminancia ni porcentajes físicos de superficie oculta. El análisis utiliza las condiciones presentes en las fotografías. El brillo medio se calcula sobre el archivo original, mediante conversión de RGB a escala de grises de ocho bits con Pillow [48], y se divide en tres grupos por los cuantiles 1/3 y 2/3. Es una comparación de brillo digital, afectada también por exposición y composición; no una medición en lux ni una prueba de tolerancia a la oscuridad.',
476: 'Anexo Repositorio y reproducción de los experimentos',
492: 'Referencias',
}

def scoped_replacements(original):
    """Keep the annotated manuscript's wording except for identified requests.

    Source-derived replacements make a move, acronym expansion or cross-reference
    update distinct from permission to rewrite a whole paragraph.
    """
    changes = dict(REPLACEMENTS)

    def replace(index, before, after):
        text = changes.get(index, original[index])
        if before not in text:
            raise ValueError(f'Scope anchor absent in source paragraph {index}: {before}')
        changes[index] = text.replace(before, after, 1)

    # Comment 0: introduce and standardize metrics/acronyms; retain both abstracts.
    for index in [60, 63]:
        changes[index] = original[index].replace('AP50', 'mAP50')
    replace(60, 'mAP50 de', 'media de precisión promedio con intersección sobre unión mínima de 0,50 (mAP50) de')
    replace(60, 'CPU de', 'la unidad central de procesamiento (CPU, central processing unit) de')
    replace(60, 'pruebas JVM', 'pruebas de la máquina virtual de Java (JVM, Java Virtual Machine)')
    replace(60, 'F1 de', 'una puntuación F1, media armónica de precisión y exhaustividad, de')
    replace(60, '33 grupos permitieron', '33 grupos de captura (G01–G33, en 30 recintos físicos) permitieron')
    replace(63, 'mAP50 of', 'mean average precision at an intersection-over-union threshold of 0.50 (mAP50) of')
    replace(63, 'CPU latency', 'central processing unit (CPU) latency')
    replace(63, 'JVM tests', 'Java Virtual Machine (JVM) tests')
    replace(63, 'F1 of', 'an F1 score, the harmonic mean of precision and recall, of')
    replace(63, '33 capture groups supported', '33 capture groups (G01–G33, across 30 physical rooms) supported')
    replace(196, 'en 33 grupos; sus resultados', 'en 33 grupos de captura (G01–G33); sus resultados')

    # Comment 19 applies to this introduction paragraph, not every related study.
    changes[183] = original[183] + ' La revisión incluye además aplicaciones que combinan soportes corporales, estimación aproximada de distancia y voz [3], y sistemas que conectan reconocimiento y síntesis de etiquetas [4]. Estos antecedentes orientan la comparación hacia la detección, su ejecución móvil y la comunicación de la información.'
    replace(183, 'Faster R-CNN', 'Faster Region-based Convolutional Neural Network (Faster R-CNN)')
    replace(183, 'YOLO [7]', 'You Only Look Once (YOLO) [7]')
    replace(183, 'SSD [8]', 'Single Shot MultiBox Detector (SSD) [8]')
    replace(180, 'TensorFlow Lite [5]', 'TensorFlow Lite (TFLite) [5]')
    replace(194, 'campo visual', 'campo visual de la cámara, entendido como la parte de la escena registrada en la imagen,')

    # Movements require an accurate roadmap and numbering, not new section titles.
    changes[201] = original[201].replace('la literatura y las arquitecturas de detección', 'la literatura, los conceptos, las métricas y las arquitecturas de detección').replace('documenta la selección inicial', 'presenta la metodología y documenta la selección inicial').replace('los anexos permiten localizar el código, reproducir la evaluación y utilizar la aplicación', 'un único anexo permite localizar el código y reproducir la evaluación; las instrucciones de uso se mantienen en los README')
    changes[204] = original[204].replace('Primero se revisan', 'Primero se presentan los conceptos y las métricas de evaluación y se revisan').replace(', los modelos candidatos y el paradigma DETR', ' y el paradigma DETR')
    changes[237] = original[237].replace('Primero se establecen los criterios de selección; después se describen las métricas, el entorno y la metodología', 'Primero se presenta la metodología general y se establecen los criterios de selección; después se describen los candidatos, el entorno y el protocolo de evaluación')
    numbers = {195:'2.1',205:'1.2',213:'1.3',217:'1.4',224:'2.3',238:'2.2',251:'1.5',253:'1.5.1',259:'2.4',260:'2.4.1',262:'2.4.2',265:'2.5',266:'2.5.1',268:'2.5.2',272:'2.6',273:'2.6.1',280:'2.6.2',284:'2.6.3',288:'2.7',289:'2.7.1',295:'2.7.2',297:'2.7.3',301:'2.8'}
    import re
    for index, number in numbers.items():
        changes[index] = number + ' ' + re.sub(r'^\d+(?:\.\d+)*\.?\s*', '', original[index])
    replace(240, 'desarrolladas en las secciones siguientes', 'desarrolladas en la sección 1.1')
    replace(267, 'sección 2.1', 'sección 2.2')

    # Comments 42–45 target the explanation of these metrics. Recall/F1 survive.
    changes[245] = REPLACEMENTS[245] + ' La precisión responde a qué proporción de las predicciones es correcta: P = TP / (TP + FP) [28]. Por ejemplo, si se anotan cinco objetos y el detector produce cuatro predicciones, tres correctas y una incorrecta, TP = 3, FP = 1 y FN = 2. La precisión es 75 % y el recall es 60 %. Este ejemplo es ilustrativo y no pertenece a los resultados experimentales.'
    changes[247] = original[247].replace('F1 Score. El F1 score', 'La puntuación F1')
    replace(248, 'Los fotogramas por segundo (FPS) y latencia de inferencia. Los fotogramas por segundo (FPS)  los primeros expresan', 'Los fotogramas por segundo (FPS, frames per second) expresan')
    replace(249, 'La memoria se reporta', 'La memoria de acceso aleatorio (RAM, random access memory) se reporta')
    replace(209, 'TensorFlow Object Detection API', 'la interfaz de programación de aplicaciones (API, application programming interface) TensorFlow Object Detection')
    replace(208, 'gTTS', 'Google Text-to-Speech (gTTS)')
    replace(215, 'Red de Propuesta de Regiones (RPN)', 'Red de Propuesta de Regiones (RPN, region proposal network)')
    replace(222, 'FP16', 'de coma flotante de 16 bits (FP16)')
    replace(228, 'BiFPN', 'una red piramidal de características bidireccional (BiFPN, bidirectional feature pyramid network)')
    replace(231, 'ONNX Runtime', 'el motor para Open Neural Network Exchange (ONNX Runtime)')
    replace(233, 'DETR (DEtection TRansformer)', 'El transformador de detección (DETR, DEtection TRansformer)')
    replace(252, 'pesos Float32 a Float16', 'pesos en coma flotante de 32 bits (Float32) a 16 bits (Float16)')
    replace(252, 'INT8', 'la representación de enteros de ocho bits (INT8)')
    replace(256, 'vía ADB', 'vía Android Debug Bridge (ADB)')
    replace(258, 'El GPU Delegate', 'El delegado de la unidad de procesamiento gráfico (GPU, graphics processing unit)')
    replace(258, 'CPU', 'la unidad central de procesamiento (CPU, central processing unit)')
    replace(258, 'OpenCL', 'Open Computing Language (OpenCL)')
    replace(269, 'CC BY 4.0', 'de atribución Creative Commons 4.0 (CC BY 4.0)')
    replace(354, 'pruebas JVM', 'pruebas de la máquina virtual de Java (JVM, Java Virtual Machine)')

    # Comment 54 and author clarification: latency is decisive for the intended
    # interaction; connect that criterion to the measured accuracy trade-off.
    changes[292] = 'Con este criterio, EfficientDet-Lite2 ofrece un equilibrio favorable. Alcanzó el mayor mAP50 del conjunto (0,648) y una latencia de inferencia de 124,9 ms en Android CPU (8,00 inferencias/s), frente a 620,8 ms de YOLOv8s Float32: aproximadamente una quinta parte del tiempo. Aunque su mAP50-95 fue menor (0,486 frente a 0,514), las puntuaciones F1 fueron próximas (0,695 y 0,702). Se aceptó, por tanto, un menor ajuste de las cajas a umbrales de solapamiento exigentes para reducir el tiempo del componente de detección, conservando una F1 cercana a la de YOLOv8s en esta evaluación. Estas latencias corresponden a inferencia aislada; el ciclo de captura y voz incorpora etapas adicionales.'
    changes[305] = 'La reducción a Float16 fue descartada dado que no ofrece ventaja de velocidad en el hardware evaluado, y la diferencia de tamaño (4,8 MB) no representa un factor determinante para la distribución de la aplicación. En cambio, la latencia de inferencia resulta crítica para la experiencia de asistencia: como la aplicación congela la captura y solo emite la descripción de voz cuando termina la detección, un mayor tiempo de inferencia retrasa directamente la respuesta auditiva y aumenta el desfase entre el instante en que el usuario apunta la cámara y el momento en que escucha qué objetos tiene enfrente.'
    changes[306] = 'Se seleccionó EfficientDet-Lite2 en CPU porque combinó el mayor mAP50 del conjunto (0,648) y un recall de 0,677 con un costo temporal menor que los candidatos YOLO. La latencia fue decisiva para el propósito de ofrecer descripciones auditivas oportunas: frente a YOLOv8s Float32, el modelo requirió aproximadamente una quinta parte del tiempo de inferencia y menos memoria (65,8 frente a 164,1 MB). También superó a YOLO11n Float32 en mAP50 (0,648 frente a 0,615), latencia (124,9 frente a 188,6 ms) y memoria (65,8 frente a 80,5 MB). Se aceptó una mAP50-95 inferior a la de ambos modelos para priorizar el tiempo de procesamiento sin renunciar a la recuperación de objetos observada. La elección se circunscribe al conjunto y al teléfono evaluados; la implementación y la evaluación posterior se presentan en los capítulos 3 y 4.'

    # User requests: define field of view and notation, retain the technical prose.
    changes[315] = original[315] + ' El campo visual de la cámara es la extensión angular de la escena registrada; depende de la óptica, el sensor y el recorte y no equivale al campo visual fisiológico del usuario. Las etiquetas 1x y 0,5x no son ángulos calibrados ni permiten afirmar que el campo angular se duplica.'
    replace(320, 'canales RGB', 'canales rojo, verde y azul (RGB, red, green, blue)')
    changes[320] += ' En [1, 448, 448, 3], los ejes representan lote, alto, ancho y canales.'
    changes[327] = original[327] + ' Para una caja [x, y, w, h], el centro es (cx, cy) = (x + w/2, y + h/2). Si W y H son el ancho y alto del fotograma original, u = cx/W y v = cy/H son sus coordenadas normalizadas. El origen está arriba a la izquierda; x crece a la derecha e y hacia abajo. Izquierda corresponde a u < 0,35, centro a 0,35 ≤ u < 0,65 y derecha a u ≥ 0,65; la mitad superior cumple v < 0,50.'
    changes[349] = original[349] + ' La Figura 3.4 muestra las pantallas de captura y de configuración de la aplicación.'

    # Comments 119, 121, 122: retain findings and remove subtitle fragmentation.
    changes[465] = original[465].replace('Se desarrolló', 'En cuanto al segundo objetivo, se desarrolló', 1)
    changes[466] = original[466].replace('La evaluación', 'A partir de esta integración, para el tercer objetivo la evaluación', 1).replace('33 grupos pareados.', '33 grupos pareados (G01–G33, en 30 recintos físicos).').replace('la elección por cantidad', 'la elección por número de detecciones correctas').replace('29 escenas', '29 grupos')
    changes[467] = original[467].replace('por escena', 'por grupo')
    changes[468] = original[468].replace('El aporte demostrado es', 'Respecto del objetivo general, el aporte demostrado es')
    return changes


INTRO_OBJECTIVES = 'El trabajo busca desarrollar un sistema de asistencia visual en un dispositivo móvil que identifique objetos de entornos interiores y comunique su ubicación relativa mediante descriptores de audio, como apoyo a la percepción del entorno de personas con discapacidad visual. Este propósito requiere seleccionar un modelo de detección optimizado para su ejecución móvil e integrarlo con la cámara y la síntesis de voz en un prototipo funcional para Android. La evaluación del prototipo en entornos interiores controlados se orienta a analizar la exactitud de detección, la latencia de procesamiento y la claridad de la retroalimentación auditiva, para valorar la identificación de los objetos y la información que se busca transmitir al usuario.'

MODEL_SELECTION_CRITERION = 'El uso previsto de AssistiveVision hace que la latencia tenga un peso decisivo en la selección. Cada captura solicitada por el usuario debe procesarse antes de generar el mensaje de voz, de modo que el tiempo de inferencia contribuye a la espera y al desfase entre la escena registrada y su descripción. Se busca reducir esa espera conservando capacidad para identificar los objetos del entorno. Por ello, las métricas de exactitud se interpretan junto con el tiempo de procesamiento y la memoria que exige cada modelo en el teléfono.'

CONCLUSION_MODEL = 'El primer objetivo se atendió con la selección de EfficientDet-Lite2 en CPU. La comparación de seis configuraciones mostró un compromiso entre mAP50, recall, latencia y memoria: el modelo obtuvo 0,648, 0,677, 124,9 ms y 65,8 MB, respectivamente. La latencia fue decisiva por su contribución a la espera previa al mensaje de voz; frente a YOLOv8s Float32 se aceptó una mAP50-95 inferior a cambio de reducir el tiempo de inferencia a aproximadamente una quinta parte. La selección corresponde al conjunto y al teléfono evaluados y no establece una superioridad universal.'


NOTATION_ROWS = [
('Símbolo', 'Significado y convención'),
('B = [x, y, w, h]', 'Caja anotada en píxeles: esquina superior izquierda, ancho y alto.'),
('W, H; cx, cy', 'Ancho y alto del fotograma original; coordenadas del centro de la caja.'),
('u, v', 'Centro normalizado: u = cx/W; v = cy/H. Origen arriba a la izquierda.'),
('g (G01–G33); c', 'Grupo de captura (1 a 33, abreviado de G01 a G33); configuración de montaje y lente (1 a 6).'),
('GT', 'Referencia anotada (ground truth); en tablas de conteos, número de instancias anotadas.'),
('TP, FP, FN', 'Detecciones correctas, predicciones sin correspondencia e instancias no recuperadas.'),
('P, R, F1', 'Precisión, exhaustividad y su media armónica. Se expresan como razón o porcentaje.'),
('Δg; n', 'Diferencia entre dos configuraciones del mismo grupo; tamaño de muestra del análisis.'),
('α; t; gl; p', 'Nivel de significación, estadístico t, grados de libertad y valor p.'),
('IC 95 %', 'Intervalo de confianza del 95 %. En el capítulo 4 procede del bootstrap de grupos.'),
('d; f_px; H_cls; h_px', 'Distancia aproximada, focal en píxeles, altura de referencia de clase y alto de caja.'),
('m, ms, px, MB', 'Metro, milisegundo, píxel y megabyte. 0,30 equivale a 30 %.'),
]

SCENE_ROWS = [
('Tipología observable', 'Grupos de ejemplo', 'Clases anotadas en los ejemplos'),
('Dormitorio', 'G01, G02, G13, G31', 'Cama, silla, mesa, portátil y televisor, según el grupo.'),
('Baño', 'G06, G09, G14, G32', 'Inodoro y lavamanos.'),
('Cocina', 'G04, G08, G11, G24', 'Refrigerador, lavamanos y, en algunos encuadres, silla o mesa.'),
('Sala o comedor', 'G03, G07, G12, G20, G33', 'Silla, mesa y, según el grupo, sofá, televisor, refrigerador o lavamanos.'),
('Espacio de trabajo', 'G27, G30', 'Persona, silla, portátil y televisor.'),
('Terraza o zona abierta', 'G28', 'Persona, silla y mesa.'),
]

CONFIG_ROWS = [
('Orden en el grupo', 'Montaje', 'Lente nominal', 'Fotografías'),
('1', 'Arnés de cabeza', '1x', '33'),
('2', 'Arnés de cabeza', '0,5x', '33'),
('3', 'Arnés de pecho', '1x', '33'),
('4', 'Arnés de pecho', '0,5x', '33'),
('5', 'Gorillapod dirigido a objetos', '1x', '33'),
('6', 'Gorillapod dirigido a objetos', '0,5x', '33'),
]

PHYSICAL_FIELD = 'Las 198 fotografías se adquirieron en seis inmuebles (cinco viviendas y un edificio de oficinas), que abarcan 30 recintos físicos únicos distribuidos en los 33 grupos G01 a G33: Vivienda 1 (dormitorios G01, G02 y G05; sala-comedor G03; cocina G04; baño G06), Vivienda 2 (sala-comedor G07; cocina G08; baño G09), Vivienda 3 (sala-comedor en dos orientaciones, G10 y G12; cocina principal G11; dormitorios G13, G15–G16 en dos orientaciones y G18; baños G14, G17, G19 y G21; sala de estar G20; cocina auxiliar G22), Vivienda 4 (sala-comedor G23; cocina G24; dormitorio G25; baño G26), edificio de oficinas (sala de trabajo en dos sectores, G27 y G30; terraza cubierta G28; recepción G29) y Vivienda 5 (dormitorio G31; baño G32; sala-comedor con cocina G33). Los recintos se eligieron por accesibilidad y por contener de forma natural las diez clases objetivo bajo su iluminación habitual (luz diurna y eléctrica en G01–G30; artificial nocturna en G31–G33), sin controlar niveles de iluminancia ni reubicar objetos para inducir oclusiones artificiales. Según su contenido visible, los recintos se agrupan en seis tipologías observables (dormitorios, baños, cocinas, salas o comedores, espacios de trabajo y terraza), con mobiliario cercano, oclusiones parciales, superficies reflectantes y agrupaciones de sillas; la Tabla 4.1 relaciona ejemplos de cada tipología con sus clases anotadas.'

PAIRED_CAPTURE = 'El emparejamiento de capturas significa que las seis configuraciones de un grupo se refieren a una situación de captura próxima, de modo que sus diferencias se analizan dentro del grupo. El orden de la Tabla 4.2 se reconstruye a partir de los nombres de archivo y se conserva con estado provisional en capture_groups.csv. No garantiza campos visuales idénticos, objetos inmóviles ni equivalencia completa de la escena: cambiar soporte y lente cambia lo que entra en la imagen. El emparejamiento reduce la comparación entre contextos ajenos, pero no elimina esas diferencias.'

FOV = 'Las opciones nominales 1x y 0,5x corresponden a la cámara principal y al ultra gran angular del teléfono de captura. El archivo registra equivalencias focales cercanas a 25 y 14 mm, pero no una calibración del ángulo de campo; además, se identificaron discrepancias entre seis etiquetas nominales y los metadatos. Una vista más amplia puede incorporar más objetos y representar cada uno con menos píxeles en la entrada de 448 × 448. Esa relación geométrica ayuda a interpretar los resultados, sin atribuirle por sí sola la causa de cada error ni suponer que el 0,5x duplica el ángulo de visión.'

MATCHING = 'Este emparejamiento de cajas es distinto del emparejamiento de capturas: en cada fotografía se ordenan las predicciones por puntuación y se asigna cada una a una anotación todavía libre de la misma clase cuando alcanza el IoU requerido. Una caja de referencia solo puede contarse una vez. La comparación estadística empareja grupos de captura, mientras que la evaluación del detector empareja cajas dentro de cada imagen, por lo que ambas operaciones actúan sobre niveles de análisis distintos.'

COVERAGE = 'Se distinguen tres niveles de respuesta que dan nombre a las columnas de las tablas siguientes. La cobertura observada corresponde a las instancias anotadas dentro del encuadre (reportadas como «Visibles» o GT); el desempeño del detector compara sus predicciones con esas instancias mediante detecciones «Correctas» (TP), predicciones «Falsas» (FP), instancias no recuperadas (FN), precisión, recall, F1 y mAP; y la selección para la voz conserva hasta dos detecciones por fotograma («Correctas (lista)»). Un objeto fuera del encuadre reduce las instancias visibles, pero no es un FN del detector. Sin identificadores entre vistas, no se calcula la cobertura de objetos únicos de un recinto.'

AUDIO = [
('h2', '4.9 Evaluación de la retroalimentación auditiva'),
('p', 'Para responder al tercer objetivo en entornos interiores controlados, la claridad de la retroalimentación auditiva se evaluó técnicamente en tres dimensiones complementarias: la claridad informativa del contenido seleccionado para el anuncio, la claridad sintáctica y espacial de las oraciones construidas, y la ejecución de la síntesis neuronal local fuera de línea.'),
('p', 'En la dimensión informativa (sección 4.5 y Figura 4.6), el filtrado por confianza (≥ 0,30) y la restricción por defecto a un máximo de dos objetos prioritarios por captura evitaron anuncios extensos o saturados de falsos positivos: la precisión de los elementos comunicados por voz ascendió de 72,6 % a 90,7 % en el palo de selfie 0,5x y de 75,6 % a 88,1 % en el arnés de pecho 1x (alcanzando 86,4 % y 84,4 % al agrupar lentes). De este modo, casi nueve de cada diez objetos incluidos en la descripción verbal corresponden a instancias verdaderas correctamente localizadas.'),
('p', 'En la dimensión sintáctica y espacial, se ejecutaron 13 pruebas unitarias automatizadas en la JVM con un 100 % de aprobación: seis pruebas sobre LocalizationModule verificaron la asignación determinista del centro normalizado (u, v) a las seis regiones del encuadre, y siete pruebas sobre SpeechFormatter comprobaron la construcción de frases completas y sin ambigüedad gramatical en español e inglés (incluyendo concordancia de artículos, conectores para uno, dos o tres objetos y notificación de escena sin detecciones).'),
('p', 'Finalmente, en la dimensión de síntesis y reproducción local, el módulo de voz superó el 100 % de las pruebas de configuración y ejecución: siete pruebas unitarias de TtsVoiceCatalog validaron los parámetros e identificadores bilingües, y cinco pruebas de instrumentación en Android ejecutadas con modo avión confirmaron la integridad de los 362 activos fonéticos (espeak-ng-data), la inicialización de los modelos VITS/Piper (es_MX-claude-high-int8 y en_US-amy-low-int8) con sherpa-onnx, la generación íntegra de la señal de voz en el dispositivo y su emisión mediante AudioTrack con liberación automática de la captura. En conjunto, estos resultados acreditan el cumplimiento de los tres criterios técnicos del tercer objetivo.'),
]


from reproduction_revision_content import ANNEX

# Reference entries use *italics*. Citation labels are generated from this same map.
# Undated documentation is disambiguated in alphabetical title order by the builder.
REFERENCES = {
1: ('World Health Organization', '2019', 'World Health Organization. (2019). *World report on vision*. https://www.who.int/publications/i/item/9789241516570'),
2: ('More et al.', '2025', 'More, S. S., Patil, N., Lobo, V. B., Shet, N., Goswami, D., & Rane, P. (2025). Empowering the visually impaired: YOLOv8-based object detection in Android applications. *Procedia Computer Science, 252*, 457–469. https://doi.org/10.1016/j.procs.2025.01.005'),
3: ('Meenakshi et al.', '2022', 'Meenakshi, R., Ponnusamy, R., Alghamdi, S., Khalaf, O. I., & Alotaibi, Y. (2022). Development of mobile app to support the mobility of visually impaired people. *Computers, Materials & Continua, 73*(2), 3473–3495. https://doi.org/10.32604/cmc.2022.028540'),
4: ('Guravaiah et al.', '2023', 'Guravaiah, K., Bhavadeesh, Y. S., Shwejan, P., Vardhan, A. H., & Lavanya, S. (2023). Third eye: Object recognition and speech generation for visually impaired. *Procedia Computer Science, 218*, 1144–1155. https://doi.org/10.1016/j.procs.2023.01.093'),
5: ('TensorFlow', 's. f.', 'TensorFlow. (s. f.). *TensorFlow Lite*. Recuperado el 5 de noviembre de 2026, de https://www.tensorflow.org/lite/guide'),
6: ('Ren et al.', '2015', 'Ren, S., He, K., Girshick, R., & Sun, J. (2015). *Faster R-CNN: Towards real-time object detection with region proposal networks* [Preprint]. arXiv. https://doi.org/10.48550/arXiv.1506.01497'),
7: ('Redmon et al.', '2016', 'Redmon, J., Divvala, S., Girshick, R., & Farhadi, A. (2016). You only look once: Unified, real-time object detection. En *2016 IEEE Conference on Computer Vision and Pattern Recognition (CVPR)* (pp. 779–788). IEEE. https://doi.org/10.1109/CVPR.2016.91'),
8: ('Liu et al.', '2016', 'Liu, W., Anguelov, D., Erhan, D., Szegedy, C., Reed, S., Fu, C.-Y., & Berg, A. C. (2016). SSD: Single shot MultiBox detector. En B. Leibe, J. Matas, N. Sebe, & M. Welling (Eds.), *Computer vision – ECCV 2016* (pp. 21–37). Springer. https://doi.org/10.1007/978-3-319-46448-0_2'),
9: ('Tan et al.', '2020', 'Tan, M., Pang, R., & Le, Q. V. (2020). EfficientDet: Scalable and efficient object detection. En *2020 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)* (pp. 10781–10790). IEEE. https://doi.org/10.1109/CVPR42600.2020.01079'),
10: ('Cerda Leon', 's. f.', 'Cerda Leon, D. F. (s. f.). *Sistema de identificación y localización espacial de objetos basado en visión por computador para asistencia a personas con discapacidad visual* [Propuesta de pasantía en investigación]. Universidad del Magdalena.'),
11: ('Universidad del Magdalena', '2020', 'Universidad del Magdalena. (2020). *Plan de Desarrollo UNIMAGDALENA Comprometida 2020–2030*.'),
12: ('Universidad del Magdalena', '2024', 'Universidad del Magdalena. (2024). *Plan de Gobierno Rectoral 2024–2028*.'),
13: ('Pawar', '2025', 'Pawar, D. R. (2025). *Deep learning-driven assistive technology for blind users: Real-time object detection and speech feedback on Android* [Preprint]. https://doi.org/10.13140/RG.2.2.28125.12005'),
14: ('Figura et al.', '2025', 'Figura, J., Kuźmiczuk, R., & Badurowicz, M. (2025). Analysis of object recognition systems using augmented reality glasses. *Journal of Computer Sciences Institute, 34*, 8–13. https://doi.org/10.35784/jcsi.6469'),
15: ('Howard et al.', '2017', 'Howard, A. G., Zhu, M., Chen, B., Kalenichenko, D., Wang, W., Weyand, T., Andreetto, M., & Adam, H. (2017). *MobileNets: Efficient convolutional neural networks for mobile vision applications* [Preprint]. arXiv. https://arxiv.org/abs/1704.04861'),
16: ('Sandler et al.', '2018', 'Sandler, M., Howard, A., Zhu, M., Zhmoginov, A., & Chen, L.-C. (2018). MobileNetV2: Inverted residuals and linear bottlenecks. En *2018 IEEE/CVF Conference on Computer Vision and Pattern Recognition* (pp. 4510–4520). IEEE. https://doi.org/10.1109/CVPR.2018.00474'),
17: ('Dai', '2020', 'Dai, J. (2020). Real-time and accurate object detection on edge device with TensorFlow Lite. *Journal of Physics: Conference Series, 1651*(1), Artículo 012114. https://doi.org/10.1088/1742-6596/1651/1/012114'),
18: ('Magdy et al.', '2025', 'Magdy, A., Moustafa, M. S., Ebied, H. M., & Tolba, M. F. (2025). Lightweight faster R-CNN for object detection in optical remote sensing images. *Scientific Reports, 15*, Artículo 16163. https://doi.org/10.1038/s41598-025-99242-y'),
19: ('Google', 's. f.', 'Google. (s. f.). *Object detection with TensorFlow Lite Model Maker*. Google AI Edge. Recuperado el 5 de noviembre de 2026, de https://developers.google.com/edge/litert/libraries/modify/object_detection'),
20: ('Ultralytics', 's. f.', 'Ultralytics. (s. f.). *Explore Ultralytics YOLOv8*. Recuperado el 5 de noviembre de 2026, de https://docs.ultralytics.com/models/yolov8/'),
21: ('Ultralytics', 's. f.', 'Ultralytics. (s. f.). *Ultralytics YOLO11*. Recuperado el 5 de noviembre de 2026, de https://docs.ultralytics.com/models/yolo11/'),
22: ('Lin et al.', '2014', 'Lin, T.-Y., Maire, M., Belongie, S., Hays, J., Perona, P., Ramanan, D., Dollár, P., & Zitnick, C. L. (2014). Microsoft COCO: Common objects in context. En D. Fleet, T. Pajdla, B. Schiele, & T. Tuytelaars (Eds.), *Computer vision – ECCV 2014* (pp. 740–755). Springer. https://doi.org/10.1007/978-3-319-10602-1_48'),
23: ('Kuznetsova et al.', '2020', 'Kuznetsova, A., Rom, H., Alldrin, N., Uijlings, J., Krasin, I., Pont-Tuset, J., Kamali, S., Popov, S., Malloci, M., Kolesnikov, A., Duerig, T., & Ferrari, V. (2020). The Open Images Dataset V4: Unified image classification, object detection, and visual relationship detection at scale. *International Journal of Computer Vision, 128*, 1956–1981. https://doi.org/10.1007/s11263-020-01316-z'),
24: ('ONNX Runtime', 's. f.', 'ONNX Runtime. (s. f.). *ONNX Runtime documentation*. Recuperado el 5 de noviembre de 2026, de https://onnxruntime.ai/docs/'),
25: ('PyTorch', 's. f.', 'PyTorch. (s. f.). *ExecuTorch documentation*. Recuperado el 5 de noviembre de 2026, de https://pytorch.org/executorch/stable/'),
26: ('Carion et al.', '2020', 'Carion, N., Massa, F., Synnaeve, G., Usunier, N., Kirillov, A., & Zagoruyko, S. (2020). End-to-end object detection with transformers. En A. Vedaldi, H. Bischof, T. Brox, & J.-M. Frahm (Eds.), *Computer vision – ECCV 2020* (pp. 213–229). Springer. https://doi.org/10.1007/978-3-030-58452-8_13'),
27: ('COCO dataset contributors', 's. f.', 'COCO dataset contributors. (s. f.). *COCO API: PythonAPI/pycocotools/cocoeval.py* [Código fuente]. GitHub. Recuperado el 5 de noviembre de 2026, de https://github.com/cocodataset/cocoapi/blob/master/PythonAPI/pycocotools/cocoeval.py'),
28: ('Manning et al.', '2008', 'Manning, C. D., Raghavan, P., & Schütze, H. (2008). *Introduction to information retrieval*. Cambridge University Press. https://nlp.stanford.edu/IR-book/'),
29: ('TensorFlow contributors', 's. f.', 'TensorFlow contributors. (s. f.). *Performance measurement* [Documentación de software]. GitHub. Recuperado el 5 de noviembre de 2026, de https://github.com/tensorflow/tensorflow/blob/master/tensorflow/lite/g3doc/performance/measurement.md'),
30: ('Google', 's. f.', 'Google. (s. f.). *Android Debug Bridge (adb)*. Android Developers. Recuperado el 5 de noviembre de 2026, de https://developer.android.com/tools/adb'),
31: ('Google', 's. f.', 'Google. (s. f.). *GPU acceleration delegate with Interpreter API*. Google AI Edge. Recuperado el 5 de noviembre de 2026, de https://developers.google.com/edge/litert/android/gpu'),
32: ('Khronos Group', 's. f.', 'Khronos Group. (s. f.). *OpenCL: The open standard for parallel programming of heterogeneous systems*. Recuperado el 5 de noviembre de 2026, de https://www.khronos.org/opencl/'),
33: ('Roboflow', 's. f.', 'Roboflow. (s. f.). *Roboflow: Computer vision tools for developers and enterprises*. Recuperado el 5 de noviembre de 2026, de https://roboflow.com/'),
34: ('Cerda Leon', '2026', 'Cerda Leon, D. F. (2026). *AssistiveVision* (revisión 85c852ddcb543bce1bd69ad0db307f895d597881) [Código fuente]. GitHub. https://github.com/diomedescerda/AssistiveVision/tree/85c852ddcb543bce1bd69ad0db307f895d597881'),
35: ('Google', 's. f.', 'Google. (s. f.). *CameraX*. Android Developers. Recuperado el 5 de noviembre de 2026, de https://developer.android.com/media/camera/camerax'),
36: ('Google', 's. f.', 'Google. (s. f.). *LiteRT for Android*. Google AI Edge. Recuperado el 5 de noviembre de 2026, de https://developers.google.com/edge/litert/android'),
37: ('k2-fsa', 's. f.', 'k2-fsa. (s. f.). *Text-to-speech*. sherpa-onnx. Recuperado el 5 de noviembre de 2026, de https://k2-fsa.github.io/sherpa/onnx/tts/index.html'),
38: ('Kim et al.', '2021', 'Kim, J., Kong, J., & Son, J. (2021). *Conditional variational autoencoder with adversarial learning for end-to-end text-to-speech* [Preprint]. arXiv. https://doi.org/10.48550/arXiv.2106.06103'),
39: ('Rhasspy contributors', 's. f.', 'Rhasspy contributors. (s. f.). *Piper: A fast, local neural text to speech system* [Código fuente]. GitHub. Recuperado el 5 de noviembre de 2026, de https://github.com/rhasspy/piper'),
40: ('Google', 's. f.', 'Google. (s. f.). *AudioTrack*. Android Developers. Recuperado el 5 de noviembre de 2026, de https://developer.android.com/reference/android/media/AudioTrack'),
41: ('Google', 's. f.', 'Google. (s. f.). *DataStore*. Android Developers. Recuperado el 5 de noviembre de 2026, de https://developer.android.com/topic/libraries/architecture/datastore'),
42: ('NIST/SEMATECH', 's. f.', 'NIST/SEMATECH. (s. f.). Analysis of paired observations. En *e-Handbook of statistical methods* (sección 7.3.1.1). Recuperado el 5 de noviembre de 2026, de https://www.itl.nist.gov/div898/handbook/prc/section3/prc311.htm'),
43: ('Efron', '1979', 'Efron, B. (1979). Bootstrap methods: Another look at the jackknife. *The Annals of Statistics, 7*(1), 1–26. https://doi.org/10.1214/aos/1176344552'),
44: ('Field & Welsh', '2007', 'Field, C. A., & Welsh, A. H. (2007). Bootstrapping clustered data. *Journal of the Royal Statistical Society: Series B (Statistical Methodology), 69*(3), 369–390. https://doi.org/10.1111/j.1467-9868.2007.00593.x'),
45: ('Szeliski', '2011', 'Szeliski, R. (2011). *Computer vision: Algorithms and applications*. Springer. https://doi.org/10.1007/978-1-84882-935-0'),
46: ('Camera & Imaging Products Association', '2017', 'Camera & Imaging Products Association. (2017). *Exif 2.31 metadata for XMP* (borrador CIPA DC-X010-2017). https://www.cipa.jp/std/documents/e/DC-X010-2017.pdf'),
47: ('NumPy developers', 's. f.', 'NumPy developers. (s. f.). *numpy.quantile*. Recuperado el 5 de noviembre de 2026, de https://numpy.org/doc/stable/reference/generated/numpy.quantile.html'),
48: ('Pillow contributors', 's. f.', 'Pillow contributors. (s. f.). *Pillow reference* [Documentación de software]. Recuperado el 5 de noviembre de 2026, de https://pillow.readthedocs.io/en/stable/reference/'),
49: ('Hunter', '2007', 'Hunter, J. D. (2007). Matplotlib: A 2D graphics environment. *Computing in Science & Engineering, 9*(3), 90–95. https://doi.org/10.1109/MCSE.2007.55'),
}
