"""Read Ambumar's published flag; never infer a bathing permission or source date."""
import json
import re
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

SOURCE = 'https://ambumar.app/estados-playas.php'

class Rows(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self.row, self.cell = [], None, None
    def handle_starttag(self, tag, attrs):
        if tag == 'tr': self.row = []
        elif tag == 'td' and self.row is not None: self.cell = {'text': '', 'images': []}
        elif tag == 'img' and self.cell is not None: self.cell['images'].append(dict(attrs))
    def handle_data(self, data):
        if self.cell is not None: self.cell['text'] += data
    def handle_endtag(self, tag):
        if tag == 'td' and self.cell is not None:
            self.row.append(self.cell)
            self.cell = None
        elif tag == 'tr' and self.row is not None:
            self.rows.append(self.row)
            self.row = None

def parse(html):
    parser = Rows()
    parser.feed(html)
    matches = [r for r in parser.rows if r and ' '.join(r[0]['text'].split()) == 'CALA BOSQUE']
    if len(matches) != 1 or len(matches[0]) != 2:
        raise ValueError('Beach row missing, duplicated or changed')
    cell = matches[0][1]
    if not cell['images'] and not cell['text'].strip():
        return {'state': 'no_report', 'flag': None, 'source_time': None}
    flags = {'verde': 'green', 'amarilla': 'yellow', 'roja': 'red'}
    if len(cell['images']) != 1: raise ValueError('Unrecognised flag markup')
    img = cell['images'][0]
    match = re.search(r'(?:^|/)ban-(verde|amarilla|roja)\.png$', img.get('src', ''))
    if not match: raise ValueError('Unrecognised flag image')
    title = img.get('title', '').strip()
    colour = match[1]
    if title and not title.upper().startswith(colour.upper()):
        raise ValueError('Flag image and title disagree')
    stamp = re.search(r'\b([01]\d|2[0-3]):[0-5]\d:[0-5]\d\b', title)
    return {'state': 'reported', 'flag': flags[colour], 'source_time': stamp[0] if stamp else None}

def collect():
    result = {'schema_version': 1, 'beach': 'CALA BOSQUE', 'source_url': SOURCE,
              'checked_at': datetime.now(timezone.utc).isoformat(), 'fetched_at': None,
              'source_date': None, 'source_timezone': None}
    try:
        req = urllib.request.Request(SOURCE, headers={'User-Agent': 'LaZeniaFlag/1.0 (personal beach status page)', 'Cache-Control': 'no-cache'})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read(2_000_001)
            if len(data) > 2_000_000: raise ValueError('Response too large')
            result['fetched_at'] = datetime.now(timezone.utc).isoformat()
            result.update(parse(data.decode('utf-8')))
    except Exception:
        # Do not expose response bodies or retain yesterday's flag as current.
        result.update(state='unavailable', flag=None, source_time=None)
        print('Source unavailable or changed; publishing an unknown status.')
    path = Path(__file__).resolve().parents[1] / 'site' / 'status.json'
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Collector state:', result['state'])
    return result

if __name__ == '__main__': collect()
