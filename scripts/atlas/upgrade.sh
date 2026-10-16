#!/usr/bin/env bash
# Atlas Documenso kopyasını yeni bir upstream sürümüne taşır.
#
#   scripts/atlas/upgrade.sh v2.21.0
#
# 1. upstream etiketini çeker, `atlas/<etiket>-tr` dalını o etiketten açar
# 2. mevcut atlas dalındaki Atlas commit'lerini (upstream etiketinden sonrakiler) üstüne taşır
# 3. çeviri kataloglarını yeniden çıkarır ve imza sayfasındaki çevrilmemiş metinleri listeler
#
# Çakışma olursa cherry-pick durur: çöz, `git cherry-pick --continue`, betiği yeniden çalıştırma —
# kalan adımları (3) elle: `npm ci && npx lingui extract --clean && python3 scripts/atlas/untranslated.py`.
# ⚠️ Yeni sürüm veritabanı göçü içeriyorsa eski imaja geri dönüş mümkün değildir → önce yedek.
set -euo pipefail

NEW_TAG="${1:?kullanım: scripts/atlas/upgrade.sh <upstream etiketi, ör. v2.21.0>}"
CUR_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
CUR_BASE="${ATLAS_BASE_TAG:-v2.16.0}"   # mevcut dalın kurulduğu upstream etiketi
NEW_BRANCH="atlas/${NEW_TAG}-tr"

git remote get-url upstream >/dev/null 2>&1 || git remote add upstream https://github.com/documenso/documenso.git
git fetch --no-tags upstream "refs/tags/${NEW_TAG}:refs/tags/${NEW_TAG}" "refs/tags/${CUR_BASE}:refs/tags/${CUR_BASE}"

ATLAS_COMMITS="$(git rev-list --reverse "${CUR_BASE}..${CUR_BRANCH}")"
echo "Taşınacak Atlas commit'leri:"; git log --oneline "${CUR_BASE}..${CUR_BRANCH}"

git checkout -b "${NEW_BRANCH}" "${NEW_TAG}"
for c in ${ATLAS_COMMITS}; do
  if ! git cherry-pick "$c"; then
    # Upstream iş akışlarını biz siliyoruz; upstream değiştirdiyse silme/değiştirme çakışması beklenir.
    wf="$(git diff --name-only --diff-filter=U -- .github/workflows | grep -v '/atlas-' || true)"
    [ -n "${wf}" ] && git rm -q -- ${wf}
    if [ -n "$(git diff --name-only --diff-filter=U)" ]; then
      echo "Gerçek çakışma ($c) — çöz, 'git cherry-pick --continue', kalan commit'leri elle taşı:"
      git diff --name-only --diff-filter=U
      exit 1
    fi
    git -c core.editor=true cherry-pick --continue
  fi
done

sed -i.bak "s/ATLAS_BASE_TAG:-v[0-9.]*/ATLAS_BASE_TAG:-${NEW_TAG}/" scripts/atlas/upgrade.sh && rm -f scripts/atlas/upgrade.sh.bak
sed -i.bak "s/:atlas-[0-9.]*-tr/:atlas-${NEW_TAG#v}-tr/" .github/workflows/atlas-image.yml && rm -f .github/workflows/atlas-image.yml.bak

npm ci
npx lingui extract --clean
python3 scripts/atlas/untranslated.py

echo
echo "Sonraki adımlar: listelenen metinleri packages/lib/translations/tr/web.po'da çevir,"
echo "ATLAS.md'deki sürüm satırını güncelle, commit + push (${NEW_BRANCH}) → atlas-image derler."
