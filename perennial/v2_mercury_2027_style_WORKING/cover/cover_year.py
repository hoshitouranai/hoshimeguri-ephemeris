"""HOSHITOURANAI 2027 cover: adopted B design only (Python/Pillow)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageChops
import math
import random

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'output'
LOGO = ROOT / 'assets' / 'hoshitouranai_python_v6_vertical_balance.png'
W, H = 3508, 2480  # A4 landscape, 300dpi
SERIF = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc'
SANS = '/usr/share/fonts/opentype/noto/noto-sans-cjk-jp-regular.ttf'
if not Path(SANS).exists():
    SANS = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
WHITE = (247, 247, 242)
MUTED = (192, 207, 226)
GOLD = (229, 191, 120)


def font(path, size):
    return ImageFont.truetype(path, size)


def centered_text(draw, text, x, cy, text_font, fill, spacing=0):
    if spacing == 0:
        box = draw.textbbox((0, 0), text, font=text_font)
        draw.text((round(x - (box[0] + box[2]) / 2),
                   round(cy - (box[1] + box[3]) / 2)),
                  text, font=text_font, fill=fill)
        return
    widths = [draw.textlength(ch, font=text_font) for ch in text]
    total_width = sum(widths) + spacing * (len(text) - 1)
    cursor = x - total_width / 2
    for ch, width in zip(text, widths):
        box = draw.textbbox((0, 0), ch, font=text_font)
        draw.text((round(cursor), round(cy - (box[1] + box[3]) / 2)),
                  ch, font=text_font, fill=fill)
        cursor += width + spacing


def cover_background():
    im = Image.new('RGB', (W, H))
    draw = ImageDraw.Draw(im)
    top, bottom = (8, 22, 53), (3, 10, 28)
    for y in range(H):
        t = y / H
        glow = math.exp(-((y - H * .44) / (H * .42)) ** 2) * .16
        rgb = tuple(round(top[i] * (1 - t) + bottom[i] * t +
                          (12 if i == 2 else 0) * glow) for i in range(3))
        draw.line((0, y, W - 1, y), fill=rgb, width=1)
    return im


def add_stars_and_star_map(im):
    rng = random.Random(20271115)
    d = ImageDraw.Draw(im, 'RGBA')
    for _ in range(310):
        x = rng.randint(160, W - 160)
        y = rng.randint(140, H - 160)
        if 660 < y < 2020 and 550 < x < 3000 and rng.random() < .90:
            continue
        r = rng.choice([1, 1, 1, 2, 2, 3])
        alpha = rng.randint(70, 170)
        d.ellipse((x-r, y-r, x+r, y+r), fill=(223, 232, 246, alpha))
    for x, y in [(410, 415), (3090, 610), (278, 1870),
                 (3200, 2150), (640, 2210), (2860, 310)]:
        d.line((x-11, y, x+11, y), fill=(224, 218, 192, 85), width=2)
        d.line((x, y-11, x, y+11), fill=(224, 218, 192, 85), width=2)
    clusters = [
        [(210,740),(370,660),(520,755),(450,980),(655,1040)],
        [(2790,600),(3020,665),(3220,540),(3300,800),(3040,965)],
        [(270,1710),(455,1800),(600,1700),(730,1880)],
        [(2920,1760),(3160,1650),(3300,1910),(3100,2135)],
    ]
    for points in clusters:
        d.line(points, fill=(160,190,226,72), width=3, joint='curve')
        for x, y in points:
            d.ellipse((x-5,y-5,x+5,y+5), fill=(231,219,183,150))
            d.ellipse((x-12,y-12,x+12,y+12), outline=(169,201,235,38), width=2)


def add_brand(im):
    logo = Image.open(LOGO).convert('RGBA')
    rgb = logo.convert('RGB')
    background = rgb.getpixel((0,0))
    difference = ImageChops.difference(rgb, Image.new('RGB', rgb.size, background))
    mask = difference.convert('L').point(lambda z: 255 if z > 35 else 0)
    logo = logo.crop(mask.getbbox() or (0,0,logo.width,logo.height))
    logo.thumbnail((113,113), Image.Resampling.LANCZOS)
    label = 'HOSHITOURANAI'
    brand_font = font(SANS, 65)
    d = ImageDraw.Draw(im)
    text_width = d.textlength(label, font=brand_font)
    left = int(W / 2 - (logo.width + 32 + text_width) / 2)
    center_y = 335
    round_mask = Image.new('L', logo.size, 0)
    ImageDraw.Draw(round_mask).ellipse((0,0,logo.width-1,logo.height-1), fill=255)
    im.paste(logo, (left,round(center_y-logo.height/2)), round_mask)
    bb = d.textbbox((0,0),label,font=brand_font)
    d.text((round(left+logo.width+32), round(center_y-(bb[1]+bb[3])/2)),
           label, font=brand_font, fill=WHITE)
    return d


def generate(year=2027):
    OUT.mkdir(parents=True, exist_ok=True)
    im = cover_background()
    add_stars_and_star_map(im)
    d = add_brand(im)
    centered_text(d,str(year),W/2,705,font(SERIF,350),WHITE,spacing=6)
    d.line((W/2-320,945,W/2+320,945),fill=(202,162,99),width=3)
    centered_text(d,'星めぐり天文暦',W/2,1105,font(SERIF,158),WHITE,spacing=6)
    centered_text(d,'収録内容',W/2,1370,font(SANS,55),GOLD,spacing=8)
    details = [
        '年間天体運行図',
        '年間水星運行詳細（ドラゴンヘッド・キロン掲載）',
        '月間天体運行図（1月〜12月）',
        '主要天体イベント一覧（サイン移動・逆行・順行）',
    ]
    for i, line in enumerate(details):
        centered_text(d,line,W/2,1495+i*131,font(SANS,57),WHITE)
    d.line((615,2040,W-615,2040),fill=(121,149,181),width=2)
    centered_text(d,'イベントは日付・時刻（日本時間）・サイン・度数を掲載',
                  W/2,2118,font(SANS,42),MUTED)
    centered_text(d,'ANNUAL  •  MONTHLY',W/2,2295,font(SANS,36),GOLD,spacing=6)
    png = OUT / f'星めぐり天文暦{year}_表紙B案_採用版.png'
    pdf = OUT / f'星めぐり天文暦{year}_表紙B案_採用版.pdf'
    im.save(png,dpi=(300,300),optimize=True)
    im.save(pdf,format='PDF',resolution=300.0)
    return png,pdf

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='採用B案の表紙を年指定で再生成')
    parser.add_argument('--year', type=int, required=True)
    args = parser.parse_args()
    if not 1900 <= args.year <= 2200:
        parser.error('year must be 1900..2200')
    print(*generate(args.year), sep='\n')
