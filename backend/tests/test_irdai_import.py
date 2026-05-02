"""
ValueTrack -- IRDAI import parser tests (no DB required).
The sample rows below are made up, but follow the column layout of
https://irdai.gov.in/health-insurance-products
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import date

from services.irdai_import import parse_any, parse_html, parse_delimited, normalize

# Shaped like the saved IRDAI page: a checkbox column, header links,
# a "Documents" column, and scripts on the page that must be ignored.
SAMPLE_HTML = """
<html><head><script>var x = "<table><tr><td>not real</td></tr></table>";</script></head>
<body>
<table class="table table-bordered">
  <thead><tr>
    <th><input type="checkbox"></th>
    <th><a href="#">Archive / Non Archive</a></th>
    <th><a href="#">Financial Year</a></th>
    <th><a href="#">Name of the Insurer</a></th>
    <th>UIN</th>
    <th><a href="#">Product Name</a></th>
    <th>Date of Approval</th>
    <th>Documents</th>
    <th>Type Of Product</th>
  </tr></thead>
  <tbody>
    <tr><td><input type="checkbox"></td><td>Non-Archived</td><td>2025-2026</td>
        <td>Example General Insurance Co. Ltd.</td><td>EXAHLIP26001V012526</td>
        <td>Example Health Shield</td><td>12-06-2025</td>
        <td><a href="#">EXAHLIP26001V012526.pdf</a> 1.1 MB</td><td>Individual</td></tr>
    <tr><td><input type="checkbox"></td><td>Archived</td><td>2019-2020</td>
        <td>Sample Health Insurance Ltd.</td><td>SMPHLGP20007V011920</td>
        <td>Sample Group Care &amp; Wellness</td><td>01-02-2020</td>
        <td></td><td>Group</td></tr>
    <tr><td></td><td>Non-Archived</td><td>2025-2026</td>
        <td></td><td>BADROW</td><td>Missing insurer</td><td>01-01-2026</td><td></td><td>Add on</td></tr>
  </tbody>
</table>
</body></html>
"""

HEADER = ['Archive / Non Archive', 'Financial Year', 'Name of the Insurer', 'UIN',
          'Product Name', 'Date of Approval', 'Documents', 'Type Of Product']
ROW = ['Non-Archived', '2025-2026', 'Example General Insurance Co. Ltd.', 'EXAHLIP26001V012526',
       'Example Health Shield', '12-06-2025', 'EXAHLIP26001V012526.pdf 1.1 MB', 'Individual']


def test_parse_saved_html_page():
    records = parse_html(SAMPLE_HTML)
    assert len(records) == 3
    assert records[0]['uin'] == 'EXAHLIP26001V012526'
    assert records[0]['insurer_name'] == 'Example General Insurance Co. Ltd.'
    assert records[1]['product_name'] == 'Sample Group Care & Wellness'


def test_parse_any_detects_html():
    assert len(parse_any(SAMPLE_HTML)) == 3


def test_parse_pasted_tab_separated_rows():
    # Browsers copy table selections as tab-separated text
    text = '\t'.join(HEADER) + '\n' + '\t'.join(ROW) + '\n'
    records = parse_any(text)
    assert len(records) == 1
    assert records[0]['product_name'] == 'Example Health Shield'


def test_parse_csv_with_bom_and_quotes():
    row = [f'"{c}"' for c in ROW]
    text = '﻿' + ','.join(HEADER) + '\r\n' + ','.join(row) + '\r\n'
    records = parse_delimited(text)
    assert len(records) == 1
    assert records[0]['uin'] == 'EXAHLIP26001V012526'


def test_header_found_below_title_lines():
    text = 'IRDAI Health Insurance Products\n\n' + '\t'.join(HEADER) + '\n' + '\t'.join(ROW)
    assert len(parse_any(text)) == 1


def test_repeated_header_rows_are_skipped():
    text = '\n'.join(['\t'.join(HEADER), '\t'.join(ROW), '\t'.join(HEADER), '\t'.join(ROW)])
    assert len(parse_any(text)) == 2


def test_no_table_returns_empty():
    assert parse_any('just some text\nwith no table') == []
    assert parse_any('<html><table><tr><td>a</td></tr></table></html>') == []


def test_normalize_good_row():
    fields, err = normalize(parse_html(SAMPLE_HTML)[0])
    assert err is None
    assert fields['uin'] == 'EXAHLIP26001V012526'
    assert fields['approval_date'] == date(2025, 6, 12)
    assert fields['is_archived'] == 0
    assert fields['product_type'] == 'Individual'
    assert fields['financial_year'] == '2025-2026'


def test_normalize_archived_flag():
    fields, _ = normalize(parse_html(SAMPLE_HTML)[1])
    assert fields['is_archived'] == 1


def test_normalize_rejects_missing_fields():
    fields, err = normalize(parse_html(SAMPLE_HTML)[2])
    assert fields is None
    assert 'insurer' in err


def test_normalize_cleans_uin_and_accepts_old_format():
    fields, err = normalize({'uin': ' exahlip26001v012526 ', 'insurer_name': 'X', 'product_name': 'Y'})
    assert err is None and fields['uin'] == 'EXAHLIP26001V012526'

    # Pre-2016 UINs used slashes and dots
    fields, err = normalize({'uin': 'IRDAI/HLT/EXA/P-H/V.I/12/2015-16', 'insurer_name': 'X', 'product_name': 'Y'})
    assert err is None


def test_normalize_rejects_junk_uin():
    fields, err = normalize({'uin': 'n/a', 'insurer_name': 'X', 'product_name': 'Y'})
    assert fields is None


def test_date_formats():
    for raw in ('12-06-2025', '12/06/2025', '2025-06-12', '12.06.2025'):
        fields, _ = normalize({'uin': 'EXAHLIP26001V012526', 'insurer_name': 'X',
                               'product_name': 'Y', 'approval_date': raw})
        assert fields['approval_date'] == date(2025, 6, 12), raw
    fields, _ = normalize({'uin': 'EXAHLIP26001V012526', 'insurer_name': 'X',
                           'product_name': 'Y', 'approval_date': 'soon'})
    assert fields['approval_date'] is None
