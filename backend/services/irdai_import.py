"""
ValueTrack — IRDAI Product Import
Reads IRDAI's public list of approved health insurance products and stores it
in the irdai_products table.

Where the data comes from:
  https://irdai.gov.in/health-insurance-products
  IRDAI's robots.txt doesn't allow automated crawling, so this module never
  fetches anything. An admin opens the page in a browser and gives us one of:
    - the saved page (Ctrl+S -> "Webpage, HTML only")
    - a CSV / TSV export (e.g. the table copied into Excel and saved as CSV)
    - the table rows copy-pasted as text (browsers copy tables as tab-separated)

The IRDAI table columns are:
  Archive / Non Archive | Financial Year | Name of the Insurer | UIN |
  Product Name | Date of Approval | Documents | Type Of Product
"""
import csv
import io
import re
from datetime import datetime
from html.parser import HTMLParser

from models import IrdaiProduct
from db import db_session

# Header text (lowercased, single-spaced) -> our field name
HEADER_MAP = {
    'uin': 'uin',
    'uin no': 'uin',
    'uin no.': 'uin',
    'name of the insurer': 'insurer_name',
    'name of insurer': 'insurer_name',
    'insurer': 'insurer_name',
    'insurer name': 'insurer_name',
    'product name': 'product_name',
    'name of the product': 'product_name',
    'type of product': 'product_type',
    'product type': 'product_type',
    'financial year': 'financial_year',
    'date of approval': 'approval_date',
    'approval date': 'approval_date',
    'archive / non archive': 'archive',
    'archive/non archive': 'archive',
    'archive': 'archive',
    'status': 'archive',
}

REQUIRED = ('uin', 'insurer_name', 'product_name')
UIN_RE = re.compile(r'^[A-Z0-9][A-Z0-9/\-\.]{5,59}$')
DATE_FORMATS = ('%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%d.%m.%Y', '%d-%b-%Y', '%d %b %Y')


def _clean(text) -> str:
    return re.sub(r'\s+', ' ', str(text or '')).strip()


def _header_key(text):
    return HEADER_MAP.get(_clean(text).lower())


# ---------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------

class _TableParser(HTMLParser):
    """Collects every <table> on a page as a list of rows of cell text."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self._stack = []      # tables being built (handles nesting)
        self._row = None
        self._cell = None
        self._skip = 0        # inside <script>/<style>

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self._skip += 1
        elif tag == 'table':
            self._stack.append([])
        elif tag == 'tr' and self._stack:
            self._row = []
        elif tag in ('td', 'th') and self._row is not None:
            self._cell = []
        elif tag == 'br' and self._cell is not None:
            self._cell.append(' ')

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self._skip = max(0, self._skip - 1)
        elif tag in ('td', 'th') and self._cell is not None and self._row is not None:
            self._row.append(_clean(''.join(self._cell)))
            self._cell = None
        elif tag == 'tr' and self._row is not None and self._stack:
            if any(self._row):
                self._stack[-1].append(self._row)
            self._row = None
        elif tag == 'table' and self._stack:
            self.tables.append(self._stack.pop())

    def handle_data(self, data):
        if self._cell is not None and not self._skip:
            self._cell.append(data)


def _rows_to_records(rows):
    """Find the header row (needs UIN + product name) and map the rows below it."""
    for i, row in enumerate(rows):
        keys = [_header_key(c) for c in row]
        if 'uin' in keys and 'product_name' in keys:
            records = []
            for data in rows[i + 1:]:
                if [_header_key(c) for c in data] == keys:
                    continue  # repeated header (e.g. two pages pasted together)
                rec = {}
                for key, value in zip(keys, data):
                    if key and key not in rec:
                        rec[key] = value
                if any(rec.values()):
                    records.append(rec)
            return records
    return None


def parse_html(text: str) -> list:
    parser = _TableParser()
    parser.feed(text)
    parser.close()
    records = []
    for table in parser.tables:
        found = _rows_to_records(table)
        if found:
            records.extend(found)
    return records


def parse_delimited(text: str) -> list:
    text = text.lstrip(chr(0xFEFF))
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return []
    sample = '\n'.join(lines[:20])
    if '\t' in sample:
        delimiter = '\t'
    else:
        try:
            delimiter = csv.Sniffer().sniff(sample, delimiters=',;|').delimiter
        except csv.Error:
            delimiter = ','
    rows = [[_clean(c) for c in r] for r in csv.reader(io.StringIO('\n'.join(lines)), delimiter=delimiter)]
    return _rows_to_records(rows) or []


def parse_any(text: str) -> list:
    """Detect HTML vs CSV/TSV/pasted text and parse it."""
    if re.search(r'<table', text, re.I):
        return parse_html(text)
    return parse_delimited(text)


def _parse_date(value):
    value = _clean(value)
    if not value:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def normalize(record: dict):
    """Turn one raw record into clean fields. Returns (fields, error)."""
    uin = re.sub(r'\s+', '', _clean(record.get('uin'))).upper()
    insurer = _clean(record.get('insurer_name'))
    product = _clean(record.get('product_name'))

    missing = [f for f, v in (('UIN', uin), ('insurer', insurer), ('product name', product)) if not v]
    if missing:
        return None, f"missing {', '.join(missing)}"
    if not UIN_RE.match(uin):
        return None, f"'{uin}' doesn't look like an IRDAI UIN"

    archive = _clean(record.get('archive')).lower()
    return {
        'uin': uin,
        'insurer_name': insurer[:200],
        'product_name': product[:255],
        'product_type': _clean(record.get('product_type'))[:60] or None,
        'financial_year': _clean(record.get('financial_year'))[:20] or None,
        'approval_date': _parse_date(record.get('approval_date')),
        'is_archived': 1 if archive.startswith('archiv') else 0,
    }, None


# ---------------------------------------------------------------------
# Saving
# ---------------------------------------------------------------------

def import_products(text: str) -> dict:
    """Parse text and upsert into irdai_products (matched on UIN)."""
    if not text or not text.strip():
        raise ValueError("The file or pasted text is empty")

    records = parse_any(text)
    if not records:
        raise ValueError("Couldn't find the IRDAI table. Make sure it has 'UIN', "
                         "'Name of the Insurer' and 'Product Name' columns.")

    clean, errors = {}, []
    for n, rec in enumerate(records, start=1):
        fields, err = normalize(rec)
        if err:
            errors.append(f"Row {n}: {err}")
        else:
            clean[fields['uin']] = fields  # last one wins if a UIN repeats

    added = updated = 0
    uins = list(clean)
    existing = {}
    for i in range(0, len(uins), 500):
        chunk = uins[i:i + 500]
        for p in db_session.query(IrdaiProduct).filter(IrdaiProduct.uin.in_(chunk)).all():
            existing[p.uin] = p

    for uin, fields in clean.items():
        product = existing.get(uin)
        if product:
            for key, value in fields.items():
                setattr(product, key, value)
            updated += 1
        else:
            db_session.add(IrdaiProduct(**fields))
            added += 1

    db_session.commit()
    return {
        'rows_found': len(records),
        'added': added,
        'updated': updated,
        'skipped': len(errors),
        'errors': errors[:10],
        'total_in_catalogue': db_session.query(IrdaiProduct).count(),
    }
