"""v53 annual chart: immutable, SHA256-checked approved color source.

Reads the palette from the sealed v17 ZIP; no fallbacks, no guessed Chiron.
Separate zodiac palette: its CSV values are still flagged under review.
"""
from __future__ import annotations
import csv, hashlib, io, re, zipfile
from pathlib import Path
from types import MappingProxyType

SOURCE_SHA256='7163a04026d738ca1ffa672dd999073515abec9bc3207a7e8c2e0823410e23d9'
SOURCE_MEMBER='data/ホシトウラナイ_カラー一覧表_試作_v03_白50パーセント.csv'
BODIES=('太陽','水星','金星','火星','木星','土星','天王星','海王星','冥王星','ドラゴンヘッド')

def load_approved_colors(locked_zip: Path):
    with zipfile.ZipFile(locked_zip) as z:
        raw=z.read(SOURCE_MEMBER)
    got=hashlib.sha256(raw).hexdigest()
    if got!=SOURCE_SHA256:
        raise ValueError(f'Palette SHA256 mismatch: {got}')
    rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    color_map={}
    for row in rows:
        if row['対象'] in BODIES:
            if row['状態']!='基準色承認済':
                raise ValueError(f"Not approved: {row['対象']}")
            color=row['基準色HEX'].upper()
            if not re.fullmatch(r'#[0-9A-F]{6}',color):
                raise ValueError(f"Invalid hex: {row['対象']}: {color}")
            if row['対象'] in color_map:
                raise ValueError(f"Duplicate name: {row['対象']}")
            color_map[row['対象']]=color
    if set(color_map)!=set(BODIES):
        raise ValueError(f'Missing/extra color entries: {set(BODIES)^set(color_map)}')
    return MappingProxyType(color_map)

def validated_track_color(name, color_map):
    """Fail closed: missing unapproved body/color cannot enter annual renderer."""
    return color_map[name]
