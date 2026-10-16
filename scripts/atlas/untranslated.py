#!/usr/bin/env python3
"""İmza sayfası / müşteriye görünen ekranlarda Türkçesi eksik (msgstr == msgid) metinleri listeler.

Kullanım: python3 scripts/atlas/untranslated.py  (depo kökünden; önce `npx lingui extract --clean`)
Çıkış kodu 1 = çevrilmemiş müşteri metni var.
"""
import re
import sys

PO = 'packages/lib/translations/tr/web.po'
CUSTOMER_FILES = re.compile(
    r'(_recipient\+|document-signing|envelope-signing|signature-pad|sign\.\$token|signing-|'
    r'recipient-roles|utils/fields|pdf-viewer|generic-error|claim-account|components/document/)',
    re.I,
)


def parse(text):
    for entry in text.split('\n\n'):
        mid = re.search(r'^msgid ((?:".*"\n?)+)', entry, re.M)
        mstr = re.search(r'^msgstr ((?:".*"\n?)+)', entry, re.M)
        if not mid or not mstr:
            continue
        join = lambda m: ''.join(re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1)))
        refs = ' '.join(line for line in entry.split('\n') if line.startswith('#:'))
        yield join(mid), join(mstr), refs


missing = [
    msgid for msgid, msgstr, refs in parse(open(PO, encoding='utf-8').read())
    if msgid and re.search('[A-Za-z]', msgid) and (not msgstr or msgstr == msgid) and CUSTOMER_FILES.search(refs)
]
for msgid in missing:
    print(msgid)
print(f'\n{len(missing)} çevrilmemiş müşteri metni ({PO})', file=sys.stderr)
sys.exit(1 if missing else 0)
