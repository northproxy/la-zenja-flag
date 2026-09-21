import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from collect import parse

def row(content='', beach='CALA BOSQUE'):
    return '<table><tr><td>' + beach + '</td><td>' + content + '</td></tr></table>'

class SourceTests(unittest.TestCase):
    def test_three_colours_and_no_invented_date(self):
        for colour, expected in [('verde','green'),('amarilla','yellow'),('roja','red')]:
            result = parse(row(f'<img src="sistema/adm/assets/img/ban-{colour}.png" title="{colour.upper()} - 10:30:00 "> &nbsp;'))
            self.assertEqual(result, {'state':'reported','flag':expected,'source_time':'10:30:00'})
    def test_empty_is_not_green(self):
        self.assertEqual(parse(row(' \n &nbsp;'))['state'], 'no_report')
    def test_no_beach_is_not_empty_report(self):
        with self.assertRaises(ValueError): parse(row('', 'CALA CAPITAN'))
    def test_unknown_or_conflicting_flags_fail_closed(self):
        for content in ['<img src="ban-azul.png">','<img src="ban-verde.png" title="ROJA - 10:30:00">','Unavailable']:
            with self.assertRaises(ValueError): parse(row(content))
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError): parse(row()+row())
    def test_clock_optional(self):
        self.assertIsNone(parse(row('<img src="ban-roja.png">'))['source_time'])

if __name__ == '__main__': unittest.main()
