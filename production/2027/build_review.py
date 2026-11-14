import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import swisseph as swe
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen.canvas import Canvas

from events import SIGNS, _jd, _lon_speed


def main():
    parser = argparse.ArgumentParser()
    for name in ('ledger', 'template', 'icon', 'ephemeris', 'annual', 'mercury', 'monthly', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    swe.set_ephe_path(str(args.ephemeris))
    with args.ledger.open(encoding='utf-8-sig') as stream:
        rows = [(datetime.fromisoformat(r[0]), *r[1:]) for r in list(csv.reader(stream))[1:]]
    year, = {row[0].year for row in rows}
    template = json.loads(args.template.read_text())
    glyphs = {name: glyph for glyph, name, _ in template['planets']}
    bodies = [swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS, swe.JUPITER,
              swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO, swe.TRUE_NODE, swe.CHIRON]
    pages = Canvas(str(args.output), pagesize=landscape(A4), invariant=True)
    width, height = landscape(A4)
    pages.setTitle(f'HOSHITOURANAI {year} 本文確認用')

    def add(path, label, bookmark=False):
        if bookmark:
            pages.bookmarkPage(label)
            pages.addOutlineEntry(label, label)
        pages.drawImage(str(path), 0, 0, width, height, preserveAspectRatio=True, anchor='c')
        pages.showPage()

    def event_pages(month):
        selected = [row for row in rows if month is None or row[0].month == month]
        section = '年間' if month is None else f'{month}月'
        total = (len(selected) + 9) // 10
        for number, start in enumerate(range(0, len(selected), 10), 1):
            data = dict(template, year=year, month=f'{section} {number}/{total}',
                        events=[], values=[[] for _ in bodies])
            for stamp, name, kind, sign, degree in selected[start:start + 10]:
                event_glyph = chr(0x2648 + SIGNS.index(sign))
                data['events'].append([glyphs[name], event_glyph, kind.replace('サイン移動（逆行）', '逆行中入座'),
                                       f'{stamp.month}/{stamp.day}', stamp.strftime('%H:%M')])
                for index, body in enumerate(bodies):
                    longitude, _, _, speed, *_ = _lon_speed(_jd(stamp), body)
                    minute = round(longitude * 60) % 21600
                    glyph = chr(0x2648 + minute // 1800)
                    cell = [glyph, f'{minute % 1800 // 60:02d}°{minute % 60:02d}′']
                    if template['planets'][index][1] == name:
                        cell = [event_glyph, degree]
                    data['values'][index].append(cell + (['R'] if speed < 0 else []))
            src = args.output.parent / f'event-{section}-{number}.json'
            png = src.with_suffix('.png')
            src.write_text(json.dumps(data, ensure_ascii=False))
            subprocess.run([sys.executable, str(Path(__file__).with_name('render_review.py')),
                            '--data', str(src), '--icon', str(args.icon), '--output', str(png)], check=True)
            add(png, f'{section}主要天体イベント', number == 1)
    add(args.annual, '年間天体運行図', True)
    add(args.mercury, '年間水星運行詳細', True)
    event_pages(None)
    for month in range(1, 13):
        add(next(args.monthly.glob(f'{year}年{month:02d}月*.png')), f'{month}月 天体運行図', True)
        event_pages(month)
    pages.save()


if __name__ == '__main__':
    main()
