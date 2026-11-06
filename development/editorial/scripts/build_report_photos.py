"""Assemble report panels from unchanged photographs and real app captures.

Only proportional resizing and white-page arrangement are applied. The original
photos and screenshot pixels remain available at the paths in the source ledger.
"""
from pathlib import Path
import argparse
import hashlib
import json

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[3]
FIGURES = REPO / 'Documents/Figures'
LEDGER = FIGURES / 'fuentes_fotograficas.json'
FONT = '/usr/share/fonts/liberation/LiberationSans-Regular.ttf'


def font(size):
    candidates = [Path(FONT), Path('/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf')]
    chosen = next((p for p in candidates if p.is_file()), None)
    if chosen is None:
        raise SystemExit('Install Liberation Sans or pass --font /path/to/LiberationSans-Regular.ttf')
    return ImageFont.truetype(str(chosen), size)


def verify(path, expected):
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError(f'Source changed: {path}')


def main():
    global FONT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--font', help='Path to LiberationSans-Regular.ttf for panel labels')
    args = parser.parse_args()
    if args.font:
        FONT = args.font
    ledger = json.loads(LEDGER.read_text())
    canvas = Image.new('RGB', (1950, 1900), 'white')
    draw = ImageDraw.Draw(canvas)
    for i, entry in enumerate(ledger['scenes']):
        path = REPO / entry['source']
        verify(path, entry['sha256'])
        image = Image.open(path).convert('RGB')
        image.thumbnail((590, 787), Image.Resampling.LANCZOS)
        x, y = 30 + (i % 3) * 650, 28 + (i // 3) * 950
        draw.text((x, y), f"({chr(97+i)}) {entry['label']}", font=font(38), fill='black')
        canvas.paste(image, (x + (590-image.width)//2, y + 70))
        draw.text((x, y+875), f"G{entry['group']:02d} · {path.name}", font=font(31), fill='black')
    canvas.save(FIGURES / 'escenas_ejemplo.png', dpi=(300, 300))

    captures = {Path(e['source']).stem:e for e in ledger['ui']['captures']}
    canvas = Image.new('RGB', (1560, 1970), 'white')
    draw = ImageDraw.Draw(canvas)
    for i, (key, label) in enumerate([('captura', 'Captura manual'), ('configuracion', 'Configuración')]):
        entry = captures[key]
        path = REPO / entry['source']
        verify(path, entry['sha256'])
        image = Image.open(path).convert('RGB')
        assert image.width == 720
        x = 25 + 790*i
        draw.text((x, 24), f"({chr(97+i)}) {label}", font=font(38), fill='black')
        canvas.paste(image, (x, 95))
    canvas.save(FIGURES / 'interfaz_app.png', dpi=(300, 300))
    print('Created escenas_ejemplo.png and interfaz_app.png from verified sources.')


if __name__ == '__main__':
    main()
