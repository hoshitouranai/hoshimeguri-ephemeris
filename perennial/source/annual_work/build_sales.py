from pathlib import Path
import hashlib
import json
import sys
import fitz
from PIL import Image

root = Path(__file__).resolve().parent
baseline, destination = map(Path, sys.argv[1:])
charts = {1: root/'annual-2027.png'}
for month in range(1, 13):
    charts[2*month+1] = root/'output'/f'2027年{month:02d}月_v16_年間共通候補.png'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

if digest(baseline) != 'cccd2e652094006714328b1a3a7b6319537f1ec6daf31e434562a8b31df51460':
    raise ValueError('Unexpected 2027 sales baseline')
with fitz.open(baseline) as pdf:
    if len(pdf) != 40:
        raise ValueError('Unexpected page count')
    for index, image in charts.items():
        report = json.loads(image.with_suffix('.dates.json').read_text())
        if digest(image) != report['sha256']:
            raise ValueError(f'Unverified chart image: {image}')
        page = pdf[index]
        [slot] = page.get_image_info(xrefs=True)
        page.replace_image(slot['xref'], filename=str(image))
    pdf.set_toc([[1, '表紙', 1], [1, '年間天体運行図', 2], [1, '水星の運行詳細', 3]]
                + [[1, f'{m}月 {label}', 2*m+2+offset]
                   for m in range(1, 13)
                   for offset, label in enumerate(('天体運行図', '天体イベント'))]
                + [[1, '年間 主要天体イベント', 28]])
    pdf.save(destination, garbage=4, deflate=True)
with fitz.open(baseline) as original, fitz.open(destination) as final:
    for index, page in enumerate(final):
        if index in charts:
            [slot] = page.get_image_info(xrefs=True)
            pixmap = fitz.Pixmap(final, slot['xref'])
            if pixmap.samples != Image.open(charts[index]).convert('RGB').tobytes():
                raise ValueError(f'Image pixels differ on page {index+1}')
        elif page.get_pixmap().samples != original[index].get_pixmap().samples:
            raise ValueError(f'Baseline page changed: {index+1}')
print('40 pages: 13 verified chart images; 27 baseline pages identical')
