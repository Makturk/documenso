#!/usr/bin/env python3
"""Türkçe kataloğu upstream'e (Crowdin / .po) vermek için temiz kopya üretir.

Bizim `tr/web.po` çevrilmemiş metinlerde İngilizce kopyayı taşır (uygulama boş metin göstermesin
diye). Upstream'e/Crowdin'e bu haliyle verilirse İngilizce metinler "Türkçe çeviri" sayılır →
bu betik `msgstr == msgid` olanları boşaltır ve özet basar.

Kullanım: python3 scripts/atlas/export_tr_for_upstream.py <çıktı.po>
"""
import re
import sys

SRC = 'packages/lib/translations/tr/web.po'


def text(block):
    return ''.join(re.findall(r'"((?:[^"\\]|\\.)*)"', block))


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else sys.exit(__doc__)
    entries = open(SRC, encoding='utf-8').read().split('\n\n')
    out, translated, emptied = [], 0, 0
    for entry in entries:
        mid = re.search(r'^msgid ((?:".*"\n?)+)', entry, re.M)
        ms = re.search(r'^msgstr ((?:".*"\n?)+)', entry + '\n', re.M)
        if mid and ms and text(mid.group(1)):
            a, b = text(mid.group(1)), text(ms.group(1))
            if not b or a == b:
                entry = entry[: entry.index('msgstr ')] + 'msgstr ""'
                emptied += 1
            else:
                translated += 1
        out.append(entry)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(out).rstrip('\n') + '\n')
    print(f'{translated} çevrili, {emptied} boş bırakıldı → {out_path}')


if __name__ == '__main__':
    main()
