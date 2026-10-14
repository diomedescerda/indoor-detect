"""Build the Chapter 4 (.docx, Spanish) from the archived benchmark tables and the
depth/scenario-1 analyses. Every number is read from saved metric files, not retyped."""
import csv
import json
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'benchmark/results/android'
OUT = ROOT.parent.parent / 'Documents/Fragments/Capitulo 4 - Diseño experimental.docx'
CONFIGS = [(m, l) for m in ('head_harness', 'chest_harness', 'gorillapod') for l in ('1x', '0.5x')]
NAMES = ['Arnés de cabeza 1x', 'Arnés de cabeza 0,5x', 'Arnés de pecho 1x',
         'Arnés de pecho 0,5x', 'Gorillapod 1x', 'Gorillapod 0,5x']
NAME = dict(zip(CONFIGS, NAMES))
MOUNTS = ('head_harness', 'chest_harness', 'gorillapod')
MOUNT_NAME = {'head_harness': 'Arnés de cabeza', 'chest_harness': 'Arnés de pecho', 'gorillapod': 'Gorillapod'}
CLS_ID = [1, 62, 63, 65, 67, 70, 72, 73, 81, 82]
CLS_ES = {1: 'persona', 62: 'silla', 63: 'sofá', 65: 'cama', 67: 'mesa de comedor', 70: 'inodoro',
          72: 'televisor', 73: 'computador portátil', 81: 'lavamanos', 82: 'nevera'}


def num(v, d=1, suffix='%'):
    v = float(v)
    if suffix == '%':
        v *= 100
    return f'{v:.{d}f}'.replace('.', ',') + (suffix if suffix else '')


def dec(v, n=3, sign=False):
    s = f'{float(v):+.{n}f}' if sign else f'{float(v):.{n}f}'
    return s.replace('.', ',')


def read(rel):
    return list(csv.DictReader((RESULTS / rel).open()))


def main():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Inches(8.27)
    sec.page_height = Inches(11.69)
    sec.top_margin = sec.bottom_margin = Inches(0.9)
    sec.left_margin = sec.right_margin = Inches(1.0)
    for name in ('Normal', 'Heading 1', 'Heading 2', 'Caption'):
        style = doc.styles[name]
        style.font.name = 'Times New Roman'
        style.font.color.rgb = RGBColor(0, 0, 0)
    doc.styles['Normal'].font.size = Pt(11)
    doc.styles['Normal'].paragraph_format.line_spacing = 1.15
    doc.styles['Normal'].paragraph_format.space_after = Pt(6)
    doc.styles['Heading 1'].font.size = Pt(14)
    doc.styles['Heading 2'].font.size = Pt(12)
    doc.styles['Caption'].font.size = Pt(10)
    doc.styles['Caption'].font.italic = False

    def para(text, style=None, align=None):
        p = doc.add_paragraph(text, style)
        if align is not None:
            p.alignment = align
        return p

    def heading(text, level=1):
        doc.add_heading(text, level)

    def table(headers, rows, widths, size=10):
        t = doc.add_table(rows=1, cols=len(headers))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        for c, w in zip(t.columns, widths):
            c.width = Inches(w)
        for c, h in zip(t.rows[0].cells, headers):
            c.text = h
        for row in rows:
            for c, v in zip(t.add_row().cells, row):
                c.text = str(v)
        borders = OxmlElement('w:tblBorders')
        for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
            e = OxmlElement('w:' + edge)
            e.set(qn('w:val'), 'single')
            e.set(qn('w:sz'), '4')
            e.set(qn('w:color'), '999999')
            borders.append(e)
        t._tbl.tblPr.append(borders)
        for ri, row in enumerate(t.rows):
            no_split = OxmlElement('w:cantSplit')
            row._tr.get_or_add_trPr().append(no_split)
            if ri == 0:
                row._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
            for cell in row.cells:
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                for p in cell.paragraphs:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.paragraph_format.space_after = Pt(0)
                    p.paragraph_format.line_spacing = 1
                    for r in p.runs:
                        r.font.size = Pt(size)
                        r.bold = ri == 0
                        r.font.color.rgb = RGBColor(0, 0, 0)
        para('')
        return t

    def fig(rel, caption, width_in):
        doc.add_picture(str(RESULTS / rel), width=Inches(width_in))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        para(caption, 'Caption')

    # ---- source tables ----
    summary = read('summary.csv')
    sm = {(r['mode'], r['mount'], r['lens']): r for r in summary if r['aggregation'] == 'configuration'}
    s_mount = {(r['mode'], r['mount']): r for r in summary if r['aggregation'] == 'mount'}
    slens = {(r['mode'], r['lens']): r for r in summary if r['aggregation'] == 'lens'}
    effects = {(r['mode'], r['factor'], r['condition_a'], r['condition_b']): r for r in read('paired_effects.csv')}
    count_pairs = [r for r in read('scenes/paired_count_differences.csv') if r['mode'] == 'detector' and r['metric'] == 'tp']
    count_summary = {r['configuration']: r for r in read('scenes/count_summary.csv') if r['mode'] == 'detector'}
    depth = read('depth/depth_bands.csv')
    dpooled = [r for r in depth if r['mode'] == 'detector' and r['mount'] == 'all']
    dep_cfg = {(r['mount'], r['lens'], int(float(r['band']))): r for r in depth if r['mode'] == 'detector' and r['mount'] != 'all'}
    ttests = read('scenario1/paired_t_tests.csv')
    counts = {}
    for ann in [json.loads((ROOT / 'labels.json').read_text())][0]['annotations']:
        counts[ann['category_id']] = counts.get(ann['category_id'], 0) + 1
    class_list = ', '.join(f'{CLS_ES[i]} (n = {counts[i]})' for i in CLS_ID)
    tt = {(t['mode'], t['config_a'], t['config_b']): t for t in ttests}

    # ================= 4.1 =================
    heading('4.1 Diseño experimental')
    para('Este capítulo evalúa experimentalmente el sistema de detección de objetos AssistiveVision mediante tres '
         'preguntas encadenadas: (a) qué posición de montaje del teléfono produce las mejores detecciones '
         '(escenario 1); (b) cuál combinación de posición y lente funciona mejor (escenario 2); y (c) en qué '
         'rango de distancia entre el objeto y la cámara las detecciones siguen siendo confiables (escenario 3). '
         'Los tres escenarios comparten el mismo conjunto de fotografías, el mismo modelo y la misma '
         'instrumentación software, de modo que las diferencias observadas puedan atribuirse al factor manipulado '
         'en cada escenario.')
    heading('Factores, niveles y diseño', 2)
    para('El escenario 1 manipula la posición de montaje del dispositivo con tres niveles: arnés de cabeza, arnés '
         'de pecho y soporte Gorillapod (mini trípode flex a la altura del pecho). El escenario 2 cruza ese factor '
         'con el lente con el que se fotografía (principal de 1x, equivalente a 25 mm; ultra gran angular de 0,5x, '
         'equivalente a 14 mm), para seis configuraciones de captura. El diseño es intra-grupo con emparejamiento '
         'por escena: la misma escena se fotografía seis veces seguidas, una por configuración, formando 33 grupos '
         'de captura pareados (198 fotografías en total). El escenario 3 no añade capturas nuevas: estima la '
         'distancia entre el objeto y la cámara dentro de las mismas 198 fotografías mediante el modelo estenopeico '
         'con la distancia focal del EXIF, clasifica las instancias anotadas en bandas de distancia y analiza el '
         'recall por banda.')
    heading('Unidades experimentales y variables', 2)
    para('La unidad experimental es la fotografía, o la escena cuando el análisis es pareado por grupo. Las '
         'variables independientes son la posición de montaje, el lente y la distancia estimada objeto-cámara. Las '
         'variables dependientes principales son: el número de objetos anotados visibles por fotografía '
         '(cobertura), las detecciones correctas (TP) y falsas (FP), la precisión, el recall, la F1 del detector y '
         'las métricas COCO AP50 y AP50-95. Una variable secundaria aplica el límite operacional de dos objetos por '
         'fotograma del prototipo (lista de anuncios) y cuenta las selecciones correctas y falsas de esa lista.')
    heading('Instrumentación del sistema bajo prueba', 2)
    para('El sistema bajo prueba es la aplicación Android ejercida por una prueba de instrumentación que invoca los '
         'módulos de producción del prototipo (preprocesamiento, detección y mapeo inverso de coordenadas). El '
         'modelo seleccionado es EfficientDet-Lite2 en 448 × 448 píxeles; las imágenes verticales se '
         'redimensionan a 336 × 448 con relleno gris 114. Se retienen detecciones desde una puntuación mínima de '
         '0,001 con un máximo de 15 por fotograma (valores de producción), y la operación se evalúa con un umbral '
         'de confianza de 0,30 y emparejamiento voraz uno a uno con IoU ≥ 0,50 y coincidencia de clase. El orden '
         'de las imágenes se baraja con la semilla 20261013 después de tres pasadas de calentamiento. La ejecución '
         'se verificó completa sobre las 198 fotografías; el entorno de ejecución y sus consecuencias se discuten '
         'en la sección 4.6.')
    heading('Conjunto de datos', 2)
    para('El conjunto de evaluación contiene 198 fotografías tomadas con un iPhone 12 Pro Max a resolución '
         '1536 × 2048 orgánica (sin rotación EXIF requerida), organizadas en 33 grupos consecutivos con el orden '
         'fijo descrito arriba. La anotación final revisada contiene 889 instancias de diez clases COCO: '
         f'{class_list}; 16 fotografías no contienen objetos objetivo anotados y se conservan en la evaluación. '
         'Las cajas provienen de un borrador inicial asistido por modelo, corregido a mano sobre la plataforma '
         'Roboflow y mapeado por nombre a los identificadores COCO; trece cajas con desviación de redondeo se '
         'recortaron a los límites de la imagen. La integridad del archivo (imágenes, etiquetas, predicciones y '
         'tablas de métricas) se verificó con sumas de verificación SHA-256.')
    heading('Método de comparación estadística', 2)
    para('Sobre los mismos datos de predicción se aplican dos comparaciones complementarias: una prueba t de '
         'Student pareada por escena (33 pares, gl = 32) sobre el número de objetos detectados correctamente por '
         'escena, y un bootstrap pareado de 10 000 remuestreos por grupo de captura (semilla 20261013) sobre '
         'razones como F1 y recall por banda, remuestreando grupos completos para preservar el emparejamiento. '
         'Todas las comparaciones son exploratorias, sin corrección por comparaciones múltiples; los supuestos y '
         'sus limitaciones se enumeran en la sección 4.6.')
    table(['Escenario', 'Factor manipulado', 'Datos', 'Comparación estadística'],
          [['4.2 Posiciones del arnés', 'Posición de montaje (3 niveles, lentes agrupadas)', '66 fotos por posición',
            't pareada por escena; bootstrap de grupos'],
           ['4.3 Arnés y lente', 'Posición × lente (6 combinaciones)', '33 fotos por combinación',
            't pareada por escena; bootstrap de grupos'],
           ['4.4 Profundidad de detección', 'Distancia objeto-cámara (estimada, 6 bandas)', '889 instancias en 198 fotos',
            'Recall por banda con IC bootstrap']],
          [1.45, 1.75, 1.05, 1.65])

    # ================= 4.2 =================
    heading('4.2 Escenario 1: posiciones del arnés')
    para('Primero se contrastan las tres posiciones de montaje agrupando los dos lentes, de modo que cada posición '
         'acumula 66 fotografías (los 33 grupos × 2 lentes) sobre la misma secuencia de escenas. La tabla '
         'siguiente resume el desempeño del detector por posición.')
    rows = []
    for m in MOUNTS:
        r, a = s_mount['detector', m], s_mount['app_output', m]
        rows.append([MOUNT_NAME[m], r['images'], r['gt'], r['tp'], r['fp'], num(r['mean_tp_per_image'], 2, ''),
                     num(r['precision']), num(r['recall']), num(r['f1']), a['tp'], num(a['precision'])])
    table(['Posición', 'Fotos', 'Visibles', 'Correctas', 'Falsas', 'Correctas/foto', 'Precisión', 'Recall', 'F1',
           'Correctas (lista)', 'Precisión (lista)'],
          rows, [1.15, 0.45, 0.62, 0.65, 0.5, 0.8, 0.68, 0.55, 0.5, 0.9, 0.9])
    para('Cada posición suma 66 fotografías (33 escenas × 2 lentes). "Correctas/foto" es la media de detecciones '
         'correctas del detector por fotografía; las dos últimas columnas aplican el límite operacional de dos '
         'objetos por fotograma del prototipo.', 'Caption')
    d_chest, d_gorilla, d_head = s_mount['detector', 'chest_harness'], s_mount['detector', 'gorillapod'], s_mount['detector', 'head_harness']
    para(f"El arnés de pecho logra la mejor F1 agrupada ({num(d_chest['f1'])}, con {num(d_chest['precision'])} de precisión); "
         f"el Gorillapod produce la mayor cantidad absoluta de objetos correctos ({d_gorilla['tp']} de {d_gorilla['gt']} visibles, "
         f"{num(d_gorilla['mean_tp_per_image'], 2, '')} por fotografía); y el arnés de cabeza queda último en ambas "
         f"dimensiones ({num(d_head['f1'])} de F1, {num(d_head['mean_tp_per_image'], 2, '')} objetos por fotografía). El peor desempeño de la "
         f"cabeza va acompañado de {d_head['empty_images']} fotografías donde no se anotó ningún objeto objetivo, contra 2 del "
         'pecho y 1 del Gorillapod, lo que apunta a problemas de encuadre y cobertura más que de clasificación.')
    para('La prueba t pareada por escena (lentes agrupadas) contrasta las posiciones dentro de cada grupo de '
         'captura; con gl = 32 el valor crítico a dos colas es t = 2,04 (α = 0,05).')
    ES = {'Head': MOUNT_NAME['head_harness'], 'Chest': MOUNT_NAME['chest_harness'], 'Gorillapod': MOUNT_NAME['gorillapod']}
    mount_rows = []
    for (mode, ca, cb), t in tt.items():
        if mode == 'detector' and ca in ('Head', 'Chest') and cb in ('Chest', 'Gorillapod'):
            mount_rows.append([ES[ca], ES[cb], dec(t['mean_diff'], 3, True), dec(t['t'], 2, True), t['df'], num(float(t['p']), 4, '')])
    table(['Posición A', 'Posición B', 'Diferencia media (A−B) objetos/escena', 't', 'gl', 'p (dos colas)'],
          sorted(mount_rows), [1.1, 1.25, 1.75, 0.55, 0.45, 0.85])
    para('Diferencias por escena del número de objetos correctos entre posiciones, prueba t pareada (gl = 32).', 'Caption')
    t_hg = tt['detector', 'Head', 'Gorillapod']
    t_cg = tt['detector', 'Chest', 'Gorillapod']
    t_hc = tt['detector', 'Head', 'Chest']
    para(f"El Gorillapod supera significativamente a la cabeza (t(32) = {dec(t_hg['t'], 2, True)}, "
         f"p = {num(t_hg['p'], 4, '')}) y, con margen más estrecho, también al pecho "
         f"(t(32) = {dec(t_cg['t'], 2, True)}, p = {num(t_cg['p'], 4, '')}); la diferencia entre cabeza y pecho no "
         f"es significativa (t(32) = {dec(t_hc['t'], 2, True)}, p = {num(t_hc['p'], 4, '')}). En conjunto: la vista de "
         'cabeza queda descartada por cobertura; entre pecho y Gorillapod el mayor número de objetos del '
         'Gorillapod convive con un margen relativamente estrecho (0,455 objetos/escena), lo que anticipa el '
         'análisis por configuración de la sección 4.3. La figura siguiente muestra la dispersión de los conteos.')
    fig('scenario1/boxplot_mount.png',
        'Figura 4.1. Objetos detectados correctamente por fotografía y posición de montaje (detector, 66 fotografías '
        'por posición, lentes agrupadas).', 4.6)
    a_head, a_chest, a_gorilla = s_mount['app_output', 'head_harness'], s_mount['app_output', 'chest_harness'], s_mount['app_output', 'gorillapod']
    para(f"Con el límite de dos objetos por fotograma, la lista de anuncios conserva {a_head['tp']} selecciones correctas de la "
         f"cabeza, {a_chest['tp']} del pecho y {a_gorilla['tp']} del Gorillapod, con precisiones de {num(a_head['precision'])}, "
         f"{num(a_chest['precision'])} y {num(a_gorilla['precision'])} respectivamente: la restricción de salida prioriza la calidad de lo que se "
         'anuncia sobre la cantidad recuperada.')

    # ================= 4.3 =================
    heading('4.3 Escenario 2: combinaciones de arnés y lente')
    para('El segundo escenario desagrega el lente y cruza las tres posiciones con las dos focales, resultando seis '
         'configuraciones de 33 fotografías pareadas por escena (tabla siguiente).')
    rows = []
    for c, name in zip(CONFIGS, NAMES):
        r, a = sm['detector', *c], sm['app_output', *c]
        rows.append([name, r['gt'], r['tp'], r['fp'], num(r['f1']), f"{num(r['AP50'])} / {num(r['AP'])}", a['tp']])
    table(['Configuración', 'Visibles', 'Correctas', 'Falsas', 'F1', 'AP50 / AP50-95', 'Correctas (lista)'],
          rows, [1.32, 0.62, 0.65, 0.55, 0.6, 1.05, 0.88])
    para('Correctas y falsas se contabilizan con confianza 0,30 e IoU ≥ 0,50 sobre las 33 fotografías por configuración; '
         'AP se calcula con el historial completo de puntuaciones del detector; "Correctas (lista)" aplica el límite '
         'de dos objetos por fotograma.', 'Caption')
    c11, c05 = sm['detector', 'chest_harness', '1x'], sm['detector', 'gorillapod', '0.5x']
    para(f"La mejor F1 es del arnés de pecho 1x ({num(c11['f1'])}; precisión {num(c11['precision'])}, recall {num(c11['recall'])}, "
         f"AP50-95 {num(c11['AP'])}) y el máximo de objetos correctos es del Gorillapod 0,5x ({c05['tp']} de {c05['gt']} instancias "
         'visibles). Como la cantidad de objetos anunciados es el objetivo para la utilidad del sistema, el análisis '
         'principal compara el Gorillapod 0,5x contra cada alternativa en los mismos 33 grupos de captura.')
    e_lens = effects['detector', 'lens', '1x', '0.5x']
    para(f"La comparación de lentes agrupando montajes tampoco es concluyente: F1 {num(slens['detector', '1x']['f1'])} para 1x "
         f"frente a {num(slens['detector', '0.5x']['f1'])} para 0,5x (diferencia pareada "
         f"{dec(float(e_lens['delta_f1']) * 100, 1, True)} puntos de F1, IC 95 % "
         f"[{dec(float(e_lens['ci95_low']) * 100, 1)}; {dec(float(e_lens['ci95_high']) * 100, 1)}]). La vista amplia contiene {slens['detector', '0.5x']['gt']} instancias visibles frente a "
         f"{slens['detector', '1x']['gt']} del 1x (+23,4 %) y recupera {slens['detector', '0.5x']['tp']} correctas frente a {slens['detector', '1x']['tp']} (+16,8 %): la "
         'ganancia en recuperación se paga con más falsas por fotograma y una F1 levemente menor.')
    rows = []
    for r in count_pairs:
        m, l = r['configuration_b'].split('/')
        t = next(t for t in ttests if t['mode'] == 'detector' and t['config_b'] == 'Gorillapod 0.5x'
                 and t['config_a'].replace('0,5x', '0.5x') == f"{m.replace('_harness', '').capitalize()} {l}")
        rows.append([NAME[(m, l)], f"{r['scenes_a_greater']} / {r['scenes_tied']} / {r['scenes_a_lower']}",
                     f"{int(r['total_difference']):+d}", dec(r['mean_difference'], 3, True),
                     f"[{dec(r['ci95_low'])}, {dec(r['ci95_high'])}]", num(float(t['p']), 4, '')])
    table(['Alternativa', 'Escenas + / = / −', 'Ganancia total de objetos', 'Ganancia/escena', 'IC 95 % (bootstrap)', 'p (t pareada)'],
          rows, [1.42, 0.95, 1.0, 0.8, 1.05, 0.8])
    para('Escenas + / = / − cuenta en cuántos de los 33 grupos el Gorillapod 0,5x detectó más, igual o menos objetos '
         'correctos que la alternativa. El IC proviene de un bootstrap percentil de 10 000 remuestreos pareados por '
         'grupos (semilla 20261013, sin corrección por comparaciones múltiples); p proviene de la prueba t '
         'pareada de objetos correctos por escena.', 'Caption')
    para('Frente al arnés de pecho 1x la ventaja es de +0,515 objetos por escena (IC 95 % [0,121; 0,939]; p = 0,019), '
         'y frente al pecho 0,5x se reduce a +0,152 con un intervalo que incluye el cero (p = 0,406), de modo que '
         'esa ventaja no queda establecida. El conteo por escena alcanza el mejor resultado con detección no nula '
         f"en {count_summary['Gorillapod 0.5x']['scenes_with_correct_detection']} de 33 escenas, y el mejor conteo no nulo por escena en "
         f"{count_summary['Gorillapod 0.5x']['scenes_at_best_nonzero_count']} de 33 (empates incluidos).")
    fig('scenario1/boxplot_configuration.png',
        'Figura 4.2. Objetos detectados correctamente por fotografía en las seis configuraciones (detector, '
        '33 fotografías por configuración).', 4.9)
    para('La elección definitiva depende del objetivo del sistema: para maximizar los objetos anunciados al '
         'usuario, el Gorillapod 0,5x es el candidato provisional; para maximizar el equilibrio '
         'precisión/recall por fotograma, el arnés de pecho 1x. En ambos casos los intervalos no descartan '
         'todas las alternativas, por lo que la confirmación en escenas nuevas forma parte del plan de '
         'validación (sección 4.6).')

    # ================= 4.4 =================
    heading('4.4 Escenario 3: rango de profundidad de detección')
    para('Para caracterizar el rango de profundidad útil del sistema se estima la distancia entre el objeto y la '
         'cámara para cada instancia anotada de las mismas 198 fotografías, sin capturas adicionales. El modelo '
         'estenopeico de la cámara entrega d ≈ f_px · H_cls / h_px, donde f_px es la distancia focal en píxeles —'
         'calculada del campo FocalLengthIn35mmFilm del EXIF (equivalente a 25 mm para el lente 1x y a 14 mm para '
         'el 0,5x; en 7 de las 198 fotografías el EXIF no coincide con lo previsto en el protocolo y se adoptó el '
         'valor del EXIF)—, h_px es la altura de la caja anotada en píxeles y H_cls es una altura de referencia '
         'fija por clase (persona 1,70 m; nevera 1,75 m; silla 0,90 m; sofá 0,85 m; inodoro 0,78 m; mesa de '
         'comedor 0,76 m; lavamanos 0,80 m; televisor 0,60 m; cama 0,60 m; computador portátil 0,25 m). Las '
         'distancias resultantes son aproximaciones, no mediciones, por lo que el análisis se reporta exclusivamente '
         'en bandas.')
    para('La tabla siguiente resume el recall del detector por banda de distancia estimada agregando las seis '
         'configuraciones. "Recall" se calcula agrupando todas las instancias de la banda; "Media por grupo" y su '
         'IC 95 % ponderan por los 33 grupos de captura (bootstrap de 10 000 remuestreos, semilla 20261013).')
    rows = []
    for r in dpooled:
        comp = r['composition_top3']
        for en, es in {'person': 'persona', 'chair': 'silla', 'couch': 'sofá', 'bed': 'cama',
                       'dining table': 'mesa', 'toilet': 'inodoro', 'tv': 'televisor',
                       'laptop': 'portátil', 'sink': 'lavamanos', 'refrigerator': 'nevera'}.items():
            comp = comp.replace(en, es)
        comp = comp.replace('%', ' %')
        rows.append([r['band_label'].replace('.', ',') + ' m', r['gt'], r['tp'], num(r['recall']), num(r['recall_group_mean']),
                     f"[{num(r['recall_ci95_low'])}; {num(r['recall_ci95_high'])}]", comp])
    table(['Banda de distancia', 'Instancias', 'Correctas', 'Recall', 'Media por grupo', 'IC 95 %', 'Clases dominantes'],
          rows, [0.95, 0.72, 0.72, 0.6, 0.85, 1.1, 1.5])
    para('Detector: confianza 0,30, IoU ≥ 0,50 y coincidencia de clase. Las clases dominantes muestran la proporción '
         'de la banda que ocupan las tres clases más frecuentes: la mezcla de clases cambia con la distancia, de '
         'modo que profundidad y clase están parcialmente confundidas.', 'Caption')
    fig('depth/depth_recall.png',
        'Figura 4.3. Recall del detector por banda de distancia estimada objeto-cámara, agrupado sobre las seis '
        'configuraciones. Barras de error: IC 95 % por bootstrap de grupos de captura.', 4.9)
    para(f"El recall se mantiene entre 60 % y 75 % hasta aproximadamente 4 m (bandas 0,5-1 m: {num(dpooled[0]['recall'])}; "
         f"1-2 m: {num(dpooled[1]['recall'])}; 2-3 m: {num(dpooled[2]['recall'])}; 3-4 m: {num(dpooled[3]['recall'])}), cae a "
         f"{num(dpooled[4]['recall'])} en 4-6 m y colapsa a {num(dpooled[5]['recall'])} a partir de 6 m. Bajo un criterio operativo de "
         'recall ≥ 50 % con al menos 30 instancias anotadas por banda, el rango de detección sugerido para el '
         'prototipo es de unos 4 metros: los objetos más lejanos deberían presentarse al usuario con baja '
         'confianza o quedar fuera del alcance del asistente.')
    para('Entre posiciones también hay matices en las bandas lejanas: a más de 6 m, el Gorillapod 1x preserva el '
         f"mejor recall ({num(dep_cfg['gorillapod', '1x', 5]['recall'])} con {dep_cfg['gorillapod', '1x', 5]['gt']} instancias) frente a "
         f"{num(dep_cfg['head_harness', '1x', 5]['recall'])} del arnés de cabeza y {num(dep_cfg['chest_harness', '1x', 5]['recall'])} del de pecho; y el ultra "
         f"gran angular pierde algo más a distancia (Gorillapod 0,5x: {num(dep_cfg['gorillapod', '0.5x', 5]['recall'])}). Como en las bandas "
         'lejanas dominan sillas, mesas y lavamanos vistos de lejos, ese margen es únicamente exploratorio.')
    para('Tres limitaciones condicionan esta conclusión. Primero, la incertidumbre de la altura de referencia por '
         'clase es proporcional (~±30 %), de manera que una instancia puede desplazarse una banda. Segundo, los '
         'objetos parcialmente ocultos pierden altura visible en la caja, lo que sobreestima su distancia. '
         'Tercero, la mezcla de clases cambia con la distancia (las bandas cercanas concentran camas y '
         'computadores; las lejanas, sillas), por lo que el recall por banda mezcla profundidad con dificultad por '
         'clase. El resultado debe entenderse como una guía operacional del prototipo —priorizar objetos a menos '
         'de ~4 m— y no como una caracterización del sensor; su adopción como restricción de producto requiere '
         'validación con distancias medidas en escenas nuevas.')

    # ================= 4.5 =================
    heading('4.5 Métricas complementarias con métodos bioinspirados')
    para('Los detectores evaluados son métodos bioinspirados: redes neuronales convolucionales de una sola pasada '
         'cuyo procesamiento jerárquico de la imagen imita los estadios de la corteza visual. Como métricas '
         'complementarias al conteo bruto de objetos se reportan, por configuración, la media de objetos visibles '
         'y correctos por fotografía, el recall, la precisión, la F1 y las métricas COCO AP50/AP50-95, además de '
         'las métricas de la lista de anuncios con el límite de dos objetos.')
    rows = []
    for c, name in zip(CONFIGS, NAMES):
        r, a = sm['detector', *c], sm['app_output', *c]
        rows.append([name, num(r['mean_gt_per_image'], 2, ''), num(r['mean_tp_per_image'], 2, ''), num(r['recall']),
                     num(r['precision']), num(r['f1']), f"{num(r['AP50'])} / {num(r['AP'])}",
                     num(a['mean_tp_per_image'], 2, ''), num(a['recall'])])
    table(['Configuración', 'Visibles/foto', 'Correctas/foto', 'Recall', 'Precisión', 'F1', 'AP50 / AP50-95',
           'Lista/foto', 'Recall lista'],
          rows, [1.32, 0.72, 0.75, 0.55, 0.6, 0.45, 1.0, 0.65, 0.65])
    para('"Correctas/foto" (y "Lista/foto") es la media de objetos emparejados correctamente por fotografía del '
         'detector (y de la lista de anuncios de dos objetos); "Recall lista" se define sobre las instancias '
         'visibles de cada fotografía.', 'Caption')
    para('Dos observaciones atraviesan la tabla. Primera: recall y conteo medio se separan porque las vistas '
         f"amplias contienen más instancias —el Gorillapod 0,5x tiene la mayor media de visibles por foto ({num(c05['mean_gt_per_image'], 2, '')}) y "
         f"recupera la mayor media de objetos ({num(c05['mean_tp_per_image'], 2, '')})—, pero su recall relativo ({num(c05['recall'])}) queda "
         f"por debajo del del arnés de pecho 1x ({num(c11['recall'])}); el recall aislado premia encuadres estrechos que "
         'ocultan objetos difíciles, por eso siempre se acompaña de la media de visibles. Segunda: la caída entre '
         f"AP50 ({num(c11['AP50'])}) y AP50-95 ({num(c11['AP'])}) indica que las cajas correctas son a menudo imprecisas, "
         'consecuencia esperada del redimensionamiento a 448 × 448; para la tarea del prototipo (nombrar el objeto '
         'y ubicarlo en izquierda/centro/derecha) la soltura geométrica exigida por AP50-95 es secundaria.')
    para('Finalmente, el límite de dos objetos eleva la precisión de la lista por encima del 80 % en todas las '
         'configuraciones: anunciar menos objetos mejora la calidad de cada anuncio. Ese intercambio '
         'entre cantidad y calidad de lo anunciado es un comportamiento de diseño del prototipo y este '
         'experimento no mide la claridad del habla, cuyo desempeño corresponde al módulo de descriptores '
         'de audio.')

    # ================= 4.6 =================
    heading('4.6 Consideraciones de validez')
    heading('Validez interna', 2)
    para('El emparejamiento por escena controla ambiente, objetos y pose entre las seis capturas de cada grupo; es '
         'la fortaleza principal del diseño. Las amenazas principales son: (a) la verdad de campo se revisó una única vez '
         'por el autor del proyecto sobre un borrador asistido por modelo, sin auditoría de un segundo revisor '
         'independiente; (b) el emparejamiento por grupos proviene del orden ascendente de archivo y debe '
         'verificarse contra las notas de captura; (c) seleccionar la mejor configuración sobre este mismo '
         'conjunto lo convierte en conjunto de selección, sesgando a favor del ganador observado; (d) los '
         'remuestreos de grupos pueden compartir habitación entre grupos vecinos, con lo que la varianza queda '
         'subestimada; y (e) ninguna comparación se ajusta por comparaciones múltiples.')
    heading('Validez de construcción', 2)
    para('Las métricas cuentan instancias visibles en cada fotografía, no objetos únicos del mundo: un mismo '
         'escritorio fotografiado desde tres posiciones genera tres instancias y tres oportunidades de acierto, y '
         'un objeto fuera de encuadre no penaliza al detector. La lista de dos objetos modela la salida de la '
         'aplicación, pero no mide la calidad del habla ni la utilidad para el usuario con discapacidad visual. '
         f"Las sillas representan {num(438 / 889)} de las instancias, de modo que las métricas agrupadas heredan ese "
         'desbalance; las métricas por clase acompañan el reporte y deben consultarse antes de sacar conclusiones '
         'de utilidad por objeto.')
    heading('Validez externa', 2)
    para('Las fotografías provienen de un iPhone 12 Pro Max y la inferencia corrió en un perfil de emulador Pixel 8 '
         '(Android 17, API 37, x86_64): las latencias reportadas (mediana 246,3 ms por detección y 104,0 ms por '
         'decodificación + preprocesamiento) son mediciones de depuración sobre emulador y no extrapolan al '
         'teléfono de destino. Las ópticas del lente 0,5x del iPhone no se trasferirán directamente al teléfono '
         'Android del prototipo. El muestreo se limita a interiores con iluminación doméstica o diurna y a diez '
         'clases COCO; la generalización a exteriores, iluminación nocturna u otras clases queda fuera del '
         'alcance de este capítulo.')
    heading('Validez del análisis de profundidad', 2)
    para('Las distancias del escenario 3 se estiman con el EXIF del iPhone y alturas de referencia por clase: '
         'su incertidumbre es proporcional a la altura de la clase (~±30 %), los objetos ocultos se alejan '
         'artificialmente y la mezcla de clases confunde profundidad con dificultad. El rango sugerido de ~4 m '
         'es una guía operacional del prototipo; de adoptarse como restricción del producto, debe validarse con '
         'distancias medidas en escenas nuevas.')
    heading('Validez estadística', 2)
    para('La prueba t pareada usa 33 escenas por comparación (gl = 32) y el bootstrap 10 000 remuestreos por '
         'grupos de captura (semilla 20261013); ambos se reportan como análisis exploratorio. Los intervalos no '
         'se ajustan ni por la correlación entre grupos vecinos ni por las comparaciones pareadas múltiples '
         'entre configuraciones; los p-valores y los intervalos describen este conjunto de datos y no '
         'recomiendan por sí solos una configuración de despliegue. La agenda de trabajo posterior queda '
         'definida por estas limitaciones: segunda revisión de la verdad de campo, validación en escenas '
         'nuevas con el teléfono físico, protocolo de distancias medido y pruebas de claridad del módulo de '
         'audio.')

    doc.save(OUT)
    print(OUT)


if __name__ == '__main__':
    main()
