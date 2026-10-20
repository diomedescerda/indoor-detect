from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt


ROOT = Path(__file__).parent
OUT = Path("/home/kenma/work/Research Internship/Documents/Slides/panoramic_object_detection_benchmark.pptx")
ASSET_DIR = Path("/home/kenma/work/Research Internship/Documents/Slides/img")
PANORAMIC_DATA = ROOT / "panoramic/data"
PANORAMIC_VIS = ROOT / "visualizations/panoramic/YOLO11n_Float16"

NAVY = RGBColor(8, 15, 30)
PANEL = RGBColor(15, 28, 49)
PANEL_2 = RGBColor(20, 39, 65)
CYAN = RGBColor(55, 221, 235)
GREEN = RGBColor(111, 235, 164)
ORANGE = RGBColor(255, 175, 86)
RED = RGBColor(255, 104, 119)
WHITE = RGBColor(240, 247, 255)
MUTED = RGBColor(157, 177, 201)
GRID = RGBColor(42, 66, 94)

W, H = 13.333, 7.5
prs = Presentation()
prs.slide_width = Inches(W)
prs.slide_height = Inches(H)


def rect(slide, x, y, w, h, fill, radius=False, line=None):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = line or fill
    if radius:
        shape.adjustments[0] = 0.08
    return shape


def text(slide, value, x, y, w, h, size=18, color=WHITE, bold=False,
         font="Aptos", align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.vertical_anchor = valign
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = value
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return box


def base(title, section="PANORAMICAS / DETECCION DE OBJETOS"):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = NAVY
    rect(slide, 0, 0, W, 0.06, CYAN)
    text(slide, section, 0.55, 0.22, 5.5, 0.25, 9, CYAN, True, "Aptos")
    text(slide, title, 0.55, 0.58, 12.2, 0.55, 27, WHITE, True)
    text(slide, f"{len(prs.slides):02d}", 12.25, 0.25, 0.5, 0.25, 10, MUTED, True, "Aptos", PP_ALIGN.RIGHT)
    return slide


def bullet(slide, value, x, y, w, color=WHITE, size=17, accent=CYAN):
    rect(slide, x, y + 0.12, 0.08, 0.08, accent, radius=True)
    text(slide, value, x + 0.22, y, w - 0.22, 0.48, size, color)


def metric(slide, x, y, w, label, value, color=CYAN, detail=None):
    rect(slide, x, y, w, 1.08, PANEL, True, GRID)
    text(slide, value, x + 0.18, y + 0.13, w - 0.36, 0.42, 25, color, True, "Aptos Display")
    text(slide, label.upper(), x + 0.18, y + 0.62, w - 0.36, 0.2, 9, MUTED, True)
    if detail:
        text(slide, detail, x + 0.18, y + 0.82, w - 0.36, 0.17, 8, MUTED)


def image_fit(slide, path, x, y, w, h):
    with Image.open(path) as im:
        iw, ih = im.size
    scale = min(w / iw, h / ih)
    nw, nh = iw * scale, ih * scale
    slide.shapes.add_picture(str(path), Inches(x + (w - nw) / 2), Inches(y + (h - nh) / 2), Inches(nw), Inches(nh))


def create_letterbox_image(source, destination, size=640):
    with Image.open(source).convert("RGB") as image:
        image.thumbnail((size, size), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (size, size), (114, 114, 114))
        left = (size - image.width) // 2
        top = (size - image.height) // 2
        canvas.paste(image, (left, top))
        canvas.save(destination, "JPEG", quality=95)


def bar(slide, x, y, w, label, value, max_value, color):
    text(slide, label, x, y - 0.02, 2.2, 0.22, 11, WHITE, True)
    rect(slide, x + 2.25, y, w, 0.24, PANEL_2, True)
    rect(slide, x + 2.25, y, w * value / max_value, 0.24, color, True)
    text(slide, f"{value:.3f}", x + 2.25 + w + 0.12, y - 0.03, 0.6, 0.25, 11, color, True)


# 1. Cover
slide = prs.slides.add_slide(prs.slide_layouts[6])
slide.background.fill.solid()
slide.background.fill.fore_color.rgb = NAVY
rect(slide, 0, 0, W, 0.08, CYAN)
rect(slide, 8.55, 0, 4.78, H, PANEL)
for i in range(9):
    rect(slide, 8.9 + i * 0.42, 1.2 + (i % 3) * 0.72, 0.15, 3.8 - (i % 4) * 0.35, GRID)
text(slide, "PRESENTADO POR DIOMEDES CERDA", 0.75, 0.72, 5.8, 0.3, 11, CYAN, True)
text(slide, "UNIVERSIDAD DEL MAGDALENA", 0.75, 1.05, 5.8, 0.25, 11, GREEN, True)
text(slide, "Deteccion de objetos\npanoramicos", 0.75, 1.45, 7.2, 1.55, 42, WHITE, True, "Aptos Display")
text(slide, "Como la geometria equirectangular cambia lo que\nlos detectores ven, puntuan y seleccionan.", 0.78, 3.35, 6.8, 0.75, 19, MUTED)
rect(slide, 0.78, 5.05, 2.15, 0.05, GREEN)
text(slide, "RESUMEN DEL BENCHMARK", 0.78, 5.34, 3.2, 0.28, 11, GREEN, True)
text(slide, "YOLOv8s · YOLO11n · SSD · EfficientDet\nTensorFlow Lite / solo CPU", 0.78, 5.75, 4.5, 0.6, 15, WHITE)
text(slide, "models_comparison", 9.0, 6.75, 3.4, 0.25, 11, CYAN, True, "Courier New")

# 2. Scope
slide = base("Que cambiamos")
text(slide, "Un benchmark configurable permite ejecutar el mismo\nproceso de inferencia sobre dos mundos visuales.", 0.58, 1.35, 7.7, 0.65, 21, WHITE)
rect(slide, 0.58, 2.35, 5.55, 3.65, PANEL, True, GRID)
text(slide, "MODO NORMAL", 0.9, 2.7, 2.5, 0.25, 12, GREEN, True)
text(slide, "test_images/data/", 0.9, 3.05, 4.6, 0.35, 19, WHITE, True, "Courier New")
bullet(slide, "Fotografias en perspectiva", 0.9, 3.72, 4.5)
bullet(slide, "Geometria de imagen estandar", 0.9, 4.25, 4.5)
bullet(slide, "Resultados: results/desktop.md", 0.9, 4.78, 4.8, MUTED, 14)
rect(slide, 7.0, 2.35, 5.75, 3.65, PANEL, True, GRID)
text(slide, "MODO PANORAMICO", 7.32, 2.7, 3.2, 0.25, 12, CYAN, True)
text(slide, "panoramic/data/", 7.32, 3.05, 4.8, 0.35, 19, WHITE, True, "Courier New")
bullet(slide, "Panoramas equirectangulares", 7.32, 3.72, 4.7)
bullet(slide, "Campo de vision amplio + distorsion", 7.32, 4.25, 4.9)
bullet(slide, "Resultados: results/panoramic_desktop.md", 7.32, 4.78, 5.0, MUTED, 14)
text(slide, "benchmark_config.json", 4.85, 6.48, 3.7, 0.25, 11, ORANGE, True, "Courier New", PP_ALIGN.CENTER)

# 3. Panoramic geometry
slide = base("El problema geometrico", "01 / REPRESENTACION VISUAL")
text(slide, "Una escena de 360 grados se despliega sobre un rectangulo plano.\nEl modelo recibe pixeles, no coordenadas esfericas.", 0.58, 1.3, 7.6, 0.7, 20, WHITE)
rect(slide, 0.62, 2.45, 7.15, 2.55, PANEL, True, GRID)
text(slide, "PROYECCION EQUIRECTANGULAR", 0.95, 2.72, 3.6, 0.2, 10, CYAN, True)
for i in range(9):
    x = 1.05 + i * 0.72
    rect(slide, x, 3.2, 0.015, 1.28, GRID)
for i in range(4):
    y = 3.2 + i * 0.42
    rect(slide, 1.05, y, 5.95, 0.015, GRID)
rect(slide, 1.25, 3.52, 1.18, 0.58, CYAN, True)
text(slide, "objeto", 1.25, 3.69, 1.18, 0.2, 11, NAVY, True, "Courier New", PP_ALIGN.CENTER)
rect(slide, 5.18, 3.3, 1.55, 1.0, ORANGE, True)
text(slide, "objeto\nestirado", 5.18, 3.53, 1.55, 0.42, 11, NAVY, True, "Courier New", PP_ALIGN.CENTER)
text(slide, "centro del panorama", 2.6, 4.63, 2.3, 0.18, 10, MUTED, False, "Aptos", PP_ALIGN.CENTER)
text(slide, "borde / polo de proyeccion", 5.2, 4.63, 1.8, 0.18, 10, MUTED, False, "Aptos", PP_ALIGN.CENTER)
bullet(slide, "La escala horizontal cambia con la latitud", 8.35, 2.55, 4.2)
bullet(slide, "Las lineas rectas pueden curvarse o estirarse", 8.35, 3.25, 4.2, WHITE, 17, ORANGE)
bullet(slide, "Un objeto puede adoptar formas muy distintas", 8.35, 3.95, 4.25, WHITE, 17, RED)
bullet(slide, "Los patrones aprendidos son menos fiables", 8.35, 4.65, 4.2, WHITE, 17, GREEN)

# 4. Data
slide = base("Dataset y superficie de evaluacion", "02 / EXPERIMENTO")
metric(slide, 0.62, 1.35, 2.25, "imagenes panoramicas", "28", CYAN)
metric(slide, 3.05, 1.35, 2.25, "anotaciones", "159", GREEN)
metric(slide, 5.48, 1.35, 2.25, "clases interiores", "10", ORANGE)
metric(slide, 7.91, 1.35, 2.25, "modelos", "6", RED)
metric(slide, 10.34, 1.35, 2.35, "ejecucion", "TFLite", CYAN, "Solo CPU")
text(slide, "Clases mapeadas a IDs COCO", 0.65, 2.85, 4.5, 0.27, 13, MUTED, True)
classes = ["person", "chair", "couch", "bed", "dining table", "toilet", "tv", "laptop", "sink", "refrigerator"]
for i, item in enumerate(classes):
    x = 0.72 + (i % 5) * 2.42
    y = 3.35 + (i // 5) * 0.72
    rect(slide, x, y, 2.12, 0.42, PANEL, True, GRID)
    text(slide, f"{i + 1:02d}  {item}", x + 0.14, y + 0.1, 1.9, 0.2, 12, WHITE, False, "Courier New")
text(slide, "Evaluacion", 0.65, 5.2, 2, 0.25, 13, CYAN, True)
text(slide, "COCO mAP50 · mAP50-95 · precision · recall · F1", 0.65, 5.56, 7.2, 0.3, 18, WHITE, True, "Courier New")
text(slide, "Se usaron el mismo postprocesamiento y umbrales\npara aislar el efecto de la geometria de entrada.", 8.55, 5.26, 3.9, 0.65, 16, MUTED)

# 5. Pipeline
slide = base("De los pixeles a la decision", "03 / PROCESO DE INFERENCIA")
steps = [("01", "cargar", "imagen JPEG"), ("02", "letterbox", "640 × 640"), ("03", "inferir", "TFLite"), ("04", "filtrar", "confianza"), ("05", "NMS", "cajas finales")]
for i, (num, name, detail) in enumerate(steps):
    x = 0.7 + i * 2.48
    rect(slide, x, 2.05, 1.95, 1.58, PANEL, True, CYAN if i == 2 else GRID)
    text(slide, num, x + 0.17, 2.22, 0.4, 0.22, 11, CYAN, True, "Courier New")
    text(slide, name, x + 0.17, 2.64, 1.55, 0.3, 19, WHITE, True, "Aptos Display")
    text(slide, detail, x + 0.17, 3.13, 1.55, 0.2, 11, MUTED, False, "Courier New")
    if i < 4:
        text(slide, ">", x + 2.05, 2.68, 0.35, 0.35, 21, GREEN, True, "Courier New", PP_ALIGN.CENTER)
rect(slide, 0.7, 4.5, 11.95, 1.22, PANEL, True, GRID)
text(slide, "EFECTO PANORAMICO", 1.0, 4.8, 2.1, 0.22, 11, ORANGE, True)
text(slide, "La distorsion aparece antes de la inferencia. Una vez aplicado el letterbox,\nla red interpreta evidencia estirada usando patrones de imagen en perspectiva.", 3.25, 4.72, 8.8, 0.55, 17, WHITE)

# 4. Letterbox input visualization
letterbox_source = PANORAMIC_DATA / "bathroom_jpg.rf.K4s6QY4N1fVIsazeojzp.jpg"
letterbox_output = ASSET_DIR / "bathroom_letterbox_640.jpg"
create_letterbox_image(letterbox_source, letterbox_output)
slide = base("Que recibe realmente el modelo", "04 / ENTRADA LETTERBOX")
text(slide, "Antes de la inferencia, la imagen se redimensiona manteniendo su proporcion\ny se centra en un lienzo cuadrado de 640 × 640 pixeles.", 0.7, 1.22, 9.5, 0.62, 19, WHITE)
for x, label, path, color in [
    (0.7, "IMAGEN PANORAMICA ORIGINAL", letterbox_source, CYAN),
    (6.85, "ENTRADA AL MODELO: 640 × 640", letterbox_output, ORANGE),
]:
    rect(slide, x, 2.15, 5.75, 3.7, PANEL, True, GRID)
    text(slide, label, x + 0.25, 2.38, 4.9, 0.22, 11, color, True, "Courier New")
    image_fit(slide, path, x + 0.18, 2.78, 5.38, 2.55)
text(slide, "El area gris es padding: no contiene informacion visual de la escena.", 0.7, 6.18, 11.9, 0.3, 15, MUTED, False, "Courier New", PP_ALIGN.CENTER)

# 5. Results table
slide = base("Impacto medido: normal vs panoramico", "05 / RESULTADOS")
text(slide, "El mAP50 baja para todos los modelos en el benchmark panoramico.", 0.62, 1.28, 7.5, 0.4, 20, WHITE)
headers = [(0.72, "MODELO"), (4.3, "NORMAL"), (6.15, "PANORAMICO"), (8.2, "CAMBIO"), (10.25, "CAMBIO EN RECALL")]
for x, label in headers:
    text(slide, label, x, 2.0, 1.5, 0.22, 10, MUTED, True, "Courier New")
rows = [
    ("YOLOv8s", 0.642, 0.499, 0.673, 0.453, GREEN),
    ("YOLO11n", 0.615, 0.402, 0.619, 0.315, CYAN),
    ("SSD MobileNet", 0.518, 0.100, 0.545, 0.115, ORANGE),
    ("EfficientDet", 0.648, 0.269, 0.677, 0.220, RED),
]
for i, (name, normal, pano, nr, pr, color) in enumerate(rows):
    y = 2.42 + i * 0.75
    rect(slide, 0.62, y - 0.11, 11.95, 0.58, PANEL if i % 2 == 0 else NAVY, True)
    text(slide, name, 0.9, y + 0.04, 2.8, 0.22, 14, WHITE, True)
    text(slide, f"{normal:.3f}", 4.3, y + 0.04, 1.0, 0.22, 15, GREEN, True, "Courier New")
    text(slide, f"{pano:.3f}", 6.15, y + 0.04, 1.0, 0.22, 15, color, True, "Courier New")
    text(slide, f"{pano-normal:+.3f}", 8.2, y + 0.04, 1.0, 0.22, 15, RED, True, "Courier New")
    text(slide, f"{pr-nr:+.3f}", 10.25, y + 0.04, 1.2, 0.22, 15, RED, True, "Courier New")
text(slide, "Mejor mAP50 panoramico: YOLOv8s con 0.499", 0.72, 5.75, 5.8, 0.25, 14, CYAN, True)
text(slide, "Mayor caida de mAP50: EfficientDet-Lite2 (−0.379)", 6.9, 5.75, 5.3, 0.25, 14, ORANGE, True)

# 7. Decision effects
slide = base("Como la distorsion cambia las decisiones", "05 / INTERPRETACION")
cards = [
    ("CONFIANZA", "La evidencia visual es mas debil", "El estiramiento cambia textura, bordes y proporciones. Los scores bajan o son menos estables.", CYAN),
    ("LOCALIZACION", "Las cajas encajan peor", "Un detector entrenado con rectangulos normales ve formas desconocidas y aumenta el error de IoU.", ORANGE),
    ("RECALL", "Se pierden mas objetos", "La caida medida del recall muestra que el modelo se vuelve conservador ante objetos distorsionados.", RED),
    ("CLASIFICACION", "Las clases similares compiten", "Las pistas de silla, sofa o mesa pueden deformarse y cambiar la clase ganadora.", GREEN),
]
for i, (label, title, body, color) in enumerate(cards):
    x = 0.65 + (i % 2) * 6.1
    y = 1.48 + (i // 2) * 2.23
    rect(slide, x, y, 5.55, 1.72, PANEL, True, GRID)
    rect(slide, x, y, 0.08, 1.72, color)
    text(slide, label, x + 0.32, y + 0.24, 2.0, 0.2, 10, color, True, "Courier New")
    text(slide, title, x + 0.32, y + 0.6, 4.8, 0.3, 18, WHITE, True)
    text(slide, body, x + 0.32, y + 1.03, 4.85, 0.48, 13, MUTED)
text(slide, "Patron observado: la precision se mantiene relativamente alta en YOLO,\nmientras que el recall absorbe la mayor parte de la penalizacion panoramica.", 0.7, 6.18, 11.7, 0.42, 17, WHITE, True, "Aptos Display", PP_ALIGN.CENTER)

# 8. Charts
slide = base("La senal mas afectada es el recall", "06 / COMPORTAMIENTO DEL MODELO")
text(slide, "Comparacion de recall", 0.72, 1.28, 3.3, 0.3, 17, WHITE, True)
bar(slide, 0.72, 1.95, 2.65, "YOLOv8s normal", 0.673, 0.75, GREEN)
bar(slide, 0.72, 2.45, 2.65, "YOLOv8s pano", 0.453, 0.75, CYAN)
bar(slide, 0.72, 3.15, 2.65, "YOLO11n normal", 0.619, 0.75, GREEN)
bar(slide, 0.72, 3.65, 2.65, "YOLO11n pano", 0.315, 0.75, CYAN)
bar(slide, 0.72, 4.35, 2.65, "SSD normal", 0.545, 0.75, GREEN)
bar(slide, 0.72, 4.85, 2.65, "SSD pano", 0.115, 0.75, CYAN)
rect(slide, 7.0, 1.55, 5.55, 4.35, PANEL, True, GRID)
text(slide, "Lectura", 7.35, 1.9, 2.0, 0.25, 12, ORANGE, True, "Courier New")
text(slide, "YOLOv8s es la linea base mas resistente", 7.35, 2.35, 4.45, 0.45, 21, WHITE, True)
bullet(slide, "Recall panoramico: 0.453", 7.35, 3.15, 4.4, WHITE, 16, CYAN)
bullet(slide, "mAP50 panoramico: 0.499", 7.35, 3.72, 4.4, WHITE, 16, CYAN)
bullet(slide, "Float16 ≈ Float32 en precision", 7.35, 4.29, 4.4, WHITE, 16, GREEN)
text(slide, "Esto sugiere que el cuello de botella\nes la representacion, no la cuantizacion.", 7.35, 5.05, 4.4, 0.48, 16, MUTED)

# 9. Visual examples
slide = base("Lo que el modelo debe interpretar", "07 / CONTEXTO VISUAL")
images = [
    (PANORAMIC_DATA / "WhatsApp Image 2026-08-03 at 4-05-23 PM_jpeg.rf.BsAHjQIbBibDtrvGBf6F.jpeg", "captura de WhatsApp 01"),
    (ASSET_DIR / "cabin.jpg", "contexto de escena amplia"),
    (PANORAMIC_DATA / "WhatsApp Image 2026-07-24 at 12-12-20 PM(1)_jpeg.rf.paJMlbkDj1yVsnde9xu0.jpeg", "captura de WhatsApp 02"),
]
for i, (filename, caption) in enumerate(images):
    x = 0.7 + i * 4.17
    rect(slide, x, 1.45, 3.72, 3.85, PANEL, True, GRID)
    image_fit(slide, filename, x + 0.12, 1.58, 3.48, 2.9)
    text(slide, caption, x + 0.22, 4.72, 3.25, 0.25, 13, WHITE, True)
    text(slide, "entrada equirectangular", x + 0.22, 5.05, 3.25, 0.2, 10, MUTED, False, "Courier New")
text(slide, "La misma clase puede verse compacta en una region y estirada en otra.", 0.75, 6.15, 11.8, 0.32, 17, CYAN, True, "Aptos Display", PP_ALIGN.CENTER)

# 10-12. Original vs prediction visualizations
comparison_images = [
    "WhatsApp Image 2026-08-03 at 4-05-23 PM_jpeg.rf.BsAHjQIbBibDtrvGBf6F.jpeg",
    "WhatsApp Image 2026-07-24 at 12-12-20 PM(1)_jpeg.rf.paJMlbkDj1yVsnde9xu0.jpeg",
    "bathroom_jpg.rf.K4s6QY4N1fVIsazeojzp.jpg",
]
for slide_number, filename in enumerate(comparison_images, start=10):
    slide = base("Imagen original frente a detecciones", f"{slide_number - 1:02d} / RESULTADO VISUAL")
    text(slide, "La visualizacion permite observar como el modelo convierte la escena\npanoramica en decisiones concretas: clase, caja y confianza.", 0.7, 1.22, 8.6, 0.62, 19, WHITE)
    original = PANORAMIC_DATA / filename
    detected = PANORAMIC_VIS / filename
    for x, label, path, color in [
        (0.7, "ORIGINAL", original, CYAN),
        (6.85, "CON CAJAS PREDICHAS", detected, GREEN),
    ]:
        rect(slide, x, 2.15, 5.75, 3.7, PANEL, True, GRID)
        text(slide, label, x + 0.25, 2.38, 3.5, 0.22, 11, color, True, "Courier New")
        image_fit(slide, path, x + 0.18, 2.78, 5.38, 2.55)
    text(slide, "YOLO11n Float16 · umbral de confianza aplicado · salida sobre la misma imagen", 0.7, 6.22, 11.9, 0.3, 14, MUTED, False, "Courier New", PP_ALIGN.CENTER)

# 13. Conclusions
slide = base("Conclusiones", "12 / CONCLUSION")
text(slide, "La deteccion panoramica no es solo un problema de imagen mas grande.\nEs un cambio de dominio causado por la geometria.", 0.7, 1.3, 8.4, 0.75, 24, WHITE, True, "Aptos Display")
takeaways = [
    ("01", "YOLOv8s es el mejor punto de partida", "mAP50 0.499 y F1 0.561 en el conjunto panoramico.", CYAN),
    ("02", "El recall es la senal de alerta", "Los modelos pierden mas objetos aunque la precision siga siendo competitiva.", ORANGE),
    ("03", "Float16 no es el problema principal", "La precision casi no cambia entre Float32 y Float16.", GREEN),
    ("04", "La adaptacion es el siguiente paso", "Entrenamiento consciente del panorama, aumentos con proyeccion o vistas cube-map pueden reducir la brecha.", RED),
]
for i, (num, title, body, color) in enumerate(takeaways):
    y = 2.48 + i * 0.82
    text(slide, num, 0.75, y, 0.5, 0.25, 13, color, True, "Courier New")
    text(slide, title, 1.45, y, 4.3, 0.25, 16, WHITE, True)
    text(slide, body, 6.0, y, 6.1, 0.35, 14, MUTED)
    rect(slide, 1.45, y + 0.48, 10.6, 0.012, GRID)

prs.save(OUT)
print(f"Saved {OUT}")
