import re
import hashlib
import json

def paper_date(when, *, year=False, time=False):
    prefix = f'{when.year}/' if year else ''
    return f'{prefix}{when.month}/{when.day}' + (f' {when:%H:%M}' if time else '')

def attest_page(image, artists):
    labels = [artist.get_text() for artist in artists]
    invalid = [label for label in labels if re.search(r'(?<![\d/])\d{1,4}-\d{1,2}(?!\d)', label)]
    if invalid or not any(re.search(r'\d/\d', label) for label in labels):
        raise ValueError(f'Invalid paper date labels: {invalid}')
    image.with_suffix('.dates.json').write_text(json.dumps({
        'sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
        'labels': labels,
    }, ensure_ascii=False), encoding='utf-8')
