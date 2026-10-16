#!/usr/bin/env python3
"""Upstream documenso/documenso'yu kontrol eder: bizdeki tabandan yeni sürüm + güvenlik duyurusu var mı?

Kullanım (depo kökünden, upstream etiketleri çekilebilir olmalı):
    GITHUB_TOKEN=... python3 scripts/atlas/upstream_check.py --out rapor.md

Çıktı:
  - `--out` dosyasına issue gövdesi (Markdown)
  - stdout'a `title=...`, `needed=true|false`, `security=true|false` (GITHUB_OUTPUT'a eklenir)

Çakışma riski için yeni sürüm etiketini geçici bir worktree'de açar ve bizim Atlas commit'lerimizi
(taban etiketinden sonrakiler) tek tek cherry-pick eder; çakışan dosyaları raporlar. Depoyu değiştirmez.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request

UPSTREAM = 'documenso/documenso'
UPSTREAM_URL = f'https://github.com/{UPSTREAM}.git'
CUSTOMER_FILES = re.compile(
    r'(_recipient\+|document-signing|envelope-signing|signature-pad|sign\.\$token|signing-|'
    r'recipient-roles|utils/fields|pdf-viewer|generic-error|claim-account|components/document/|'
    r'server-only/pdf/|utils/document-audit-logs|document-certificate-qr-view|constants/document-auth|'
    r'constants/i18n\.ts|articles\.signature-disclosure)',
    re.I,
)
NOTE_FLAG = re.compile(r'(secur|vulnerab|xss|csrf|cve|ghsa|auth|leak|disclos|injection|bypass)', re.I)


def git(*args, check=True, cwd=None):
    r = subprocess.run(['git', *args], capture_output=True, text=True, cwd=cwd)
    if check and r.returncode != 0:
        raise RuntimeError(f'git {" ".join(args)}: {r.stderr.strip()}')
    return r.stdout


def api(path):
    req = urllib.request.Request(f'https://api.github.com/{path}', headers={'Accept': 'application/vnd.github+json'})
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    if token:
        req.add_header('Authorization', f'Bearer {token}')
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def ver(tag):
    return tuple(int(x) for x in re.findall(r'\d+', tag)[:3])


def base_tag():
    text = open('scripts/atlas/upgrade.sh', encoding='utf-8').read()
    m = re.search(r'ATLAS_BASE_TAG:-(v[0-9.]+)', text)
    if not m:
        sys.exit('scripts/atlas/upgrade.sh içinde ATLAS_BASE_TAG bulunamadı')
    return m.group(1)


def range_hits(rng, v):
    """GitHub danışma aralığı ('<= 2.17.0', '>= 1.0.0, < 2.18.0') bizim sürümü kapsıyor mu?"""
    if not rng:
        return True
    for part in rng.split(','):
        m = re.match(r'\s*(<=|>=|<|>|=)?\s*v?([\d.]+)', part)
        if not m:
            continue
        op, target = m.group(1) or '=', ver(m.group(2))
        ok = {'<': v < target, '<=': v <= target, '>': v > target, '>=': v >= target, '=': v == target}[op]
        if not ok:
            return False
    return True


def msgids(tag):
    out = git('show', f'{tag}:packages/lib/translations/en/web.po', check=False)
    ids = {}
    for entry in out.split('\n\n'):
        mid = re.search(r'^msgid ((?:".*"\n?)+)', entry, re.M)
        if mid:
            key = ''.join(re.findall(r'"((?:[^"\\]|\\.)*)"', mid.group(1)))
            ids[key] = ' '.join(l for l in entry.split('\n') if l.startswith('#:'))
    return ids


def trial_cherry_pick(new_tag, commits):
    """Atlas commit'lerini yeni etiket üstüne dener; [(commit, [çakışan dosyalar])] döner."""
    conflicts = []
    with tempfile.TemporaryDirectory() as tmp:
        wt = os.path.join(tmp, 'wt')
        git('worktree', 'add', '--detach', wt, new_tag)
        try:
            for c in commits:
                r = subprocess.run(['git', 'cherry-pick', '--no-commit', c], capture_output=True, text=True, cwd=wt)
                if r.returncode != 0:
                    files = git('diff', '--name-only', '--diff-filter=U', cwd=wt).split()
                    # Upstream iş akışlarını biz siliyoruz; upstream değiştirdiyse silme/değiştirme çakışması
                    # olur — beklenen, upgrade.sh de aynı şekilde siler. Gerçek çakışma sayılmaz.
                    workflows = [f for f in files if f.startswith('.github/workflows/') and not f.startswith('.github/workflows/atlas-')]
                    if workflows:
                        git('rm', '-q', '--', *workflows, cwd=wt)
                    real = [f for f in files if f not in workflows]
                    if real:
                        conflicts.append((c, real))
                        # Sonraki commit'ler doğru zeminde denensin: çakışan dosyada Atlas sürümünü al.
                        git('checkout', '--theirs', '--', *real, cwd=wt)
                        git('add', '--', *real, cwd=wt)
                git('-c', 'user.name=atlas', '-c', 'user.email=atlas@invalid', 'commit', '-q', '--no-verify',
                    '--allow-empty', '-m', f'trial {c}', cwd=wt)
        finally:
            git('worktree', 'remove', '--force', wt, check=False)
    return conflicts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--head', default='HEAD')
    args = ap.parse_args()

    base = base_tag()
    bv = ver(base)

    releases = [r for r in api(f'repos/{UPSTREAM}/releases?per_page=30')
                if not r['draft'] and not r['prerelease'] and ver(r['tag_name']) > bv]
    releases.sort(key=lambda r: ver(r['tag_name']))

    advisories = []
    for a in api(f'repos/{UPSTREAM}/security-advisories?per_page=100&state=published'):
        vulns = a.get('vulnerabilities') or [{}]
        if any(range_hits(v.get('vulnerable_version_range'), bv) for v in vulns):
            advisories.append(a)

    out = [f'Bizdeki taban: **{base}** (`atlas/{base}-tr` dalı, `scripts/atlas/upgrade.sh` → `ATLAS_BASE_TAG`).', '']

    if advisories:
        out += ['## 🔴 Bizdeki sürümü etkileyen güvenlik duyuruları', '']
        for a in advisories:
            rng = '; '.join(f"etkilenen `{v.get('vulnerable_version_range')}` → düzeltme `{v.get('patched_versions')}`"
                            for v in a.get('vulnerabilities') or [])
            out.append(f"- **{a['severity'].upper()}** [{a['ghsa_id']}]({a['html_url']}) — {a['summary']} "
                       f"({a.get('published_at', '')[:10]}; {rng})")
        out += ['', 'Önce canlıda gerçekten açık mı kontrol et (yalnız okuma), sonra ATLAS.md → '
                '"Upstream güncelleme" adımlarıyla düzeltilmiş sürüme geç ya da düzeltmeyi kopyaya aktar.', '']

    latest = releases[-1]['tag_name'] if releases else None
    if latest:
        git('fetch', '--no-tags', '-q', UPSTREAM_URL, f'refs/tags/{base}:refs/tags/{base}',
            f'refs/tags/{latest}:refs/tags/{latest}')
        out += [f'## Yeni sürümler ({len(releases)})', '']
        for r in reversed(releases):
            body = (r.get('body') or '').splitlines()
            items = [l.strip() for l in body if l.strip().startswith(('* ', '- '))]
            flagged = [l for l in items if NOTE_FLAG.search(l)]
            out.append(f"### [{r['tag_name']}]({r['html_url']}) — {r['published_at'][:10]} ({len(items)} değişiklik)")
            for l in flagged[:15]:
                out.append(f'- ⚠️ {l[2:]}')
            for l in [l for l in items if l not in flagged][:12]:
                out.append(f'- {l[2:]}')
            if len(items) > len(flagged[:15]) + 12:
                out.append(f'- … tamamı sürüm notunda')
            out.append('')

        ours = set(git('diff', '--name-only', f'{base}..{args.head}').split())
        theirs = set(git('diff', '--name-only', base, latest).split())
        overlap = sorted(f for f in ours & theirs if not f.startswith('.github/workflows/'))
        migrations = sorted(f for f in git('diff', '--name-only', '--diff-filter=A', base, latest, '--',
                                           'packages/prisma/migrations').split() if f.endswith('migration.sql'))
        commits = git('rev-list', '--reverse', f'{base}..{args.head}').split()
        conflicts = trial_cherry_pick(latest, commits)

        old_ids, new_ids = msgids(base), msgids(latest)
        added = [k for k in new_ids if k and k not in old_ids]
        added_customer = [k for k in added if CUSTOMER_FILES.search(new_ids[k])]

        risk = 'YÜKSEK' if conflicts or migrations else ('ORTA' if overlap else 'DÜŞÜK')
        out += [f'## {latest} üzerine taşıma riski: **{risk}**', '',
                f'- Atlas commit sayısı: {len(commits)}; deneme cherry-pick: '
                + ('**çakışma var**' if conflicts else 'çakışmasız'),
                ]
        for c, files in conflicts:
            subject = git('log', '-1', '--format=%s', c).strip()
            out.append(f'  - `{c[:10]}` {subject}: ' + ', '.join(f'`{f}`' for f in files))
        out.append(f'- Bizim de değiştirdiğimiz, upstream\'in de değiştirdiği dosyalar: {len(overlap)}')
        for f in overlap[:40]:
            out.append(f'  - `{f}`')
        out.append(f'- Yeni veritabanı göçü: {len(migrations)}'
                   + (' → **eski imaja geri dönüş mümkün değil, önce pg_dump yedeği**' if migrations else ''))
        for f in migrations[:20]:
            out.append(f'  - `{f}`')
        out.append(f'- Yeni çevrilecek metin: {len(added)} (müşteriye görünen ekranlarda: {len(added_customer)})')
        for k in added_customer[:30]:
            out.append(f'  - {k[:120]}')
        out += ['', '## Yapılacaklar', '',
                f'ATLAS.md → "Upstream güncelleme" prosedürü: `scripts/atlas/upgrade.sh {latest}` → çevir → '
                'imaj → deneme konteyneri → canlı → geri dönüş satırını güncelle.']

    needed = bool(releases or advisories)
    sec = bool(advisories)
    title = (('[GÜVENLİK] ' if sec else '')
             + (f'Upstream Documenso {latest} çıktı (bizde {base})' if latest
                else f'Upstream Documenso güvenlik duyurusu (bizde {base})'))
    if not needed:
        out.append(f'Yeni sürüm ya da bizi etkileyen güvenlik duyurusu yok.')
    out += ['', f'_Bu issue `.github/workflows/atlas-upstream-check.yml` tarafından açıldı._']

    with open(args.out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out) + '\n')
    print(f'title={title}')
    print(f'needed={"true" if needed else "false"}')
    print(f'security={"true" if sec else "false"}')


if __name__ == '__main__':
    main()
