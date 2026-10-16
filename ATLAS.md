# Atlas Solo — Documenso kopyası

Upstream: documenso/documenso **v2.16.0** (canlıdaki sürümle aynı → veritabanı şeması değişmez,
geri dönüş güvenli). Değişiklikler (`atlas/v2.16.0-tr` dalı):

1. **Türkçe dil** (`tr`): `packages/lib/constants/locales.ts` + `i18n.ts`;
   `packages/lib/translations/tr/web.po` — imza sayfası ve müşteriye görünen ~450 metin Türkçe,
   kalanlar İngilizce (en kopyası). Eksikleri `scripts/atlas/untranslated.py` listeler.
2. **`?lang=xx`**: imza bağlantısındaki dil parametresi çereze ve tarayıcı diline üstün gelir
   (`apps/remix/app/root.tsx` + sunucu çizimi `apps/remix/app/entry.server.tsx`). Atlas davet
   e-postası bağlantıya müşterinin dilini ekler.
3. **Gönderen firma adı**: belge `externalId` = `atlas-sender:<URI kodlu ad>` ise imza sayfası
   başlığı "<Firma> sizi bu belgeyi imzalamaya davet etti" olur
   (`document-signing-page-view-v1.tsx`). Tüm firmalar tek Documenso ekibinden gönderdiği için.
4. Upstream iş akışları kaldırıldı; `.github/workflows/atlas-image.yml` imajı GHCR'ye derler.

Lisans: AGPL-3.0 (upstream) — bu depo herkese açık kaynak olarak durur.

## Canlıya alma / geri dönüş (166.1.94.181, `/opt/documenso/compose.yml`)
- Yeni: `image: ghcr.io/makturk/documenso:atlas-<sha>` → `docker compose up -d documenso`
  (yalnız Documenso konteyneri; aynı kutudaki diğer servislere dokunulmaz).
- Geri dönüş: `image: documenso/documenso@sha256:945bd2c04306bd5d78def0c4ceafdffb6b0a106cd6a2543db5acda9a6424b2d9`
  (2026-07-21 derlemesi, v2.16.0 — değişiklik öncesi canlı imaj) → `docker compose up -d documenso`.

## Upstream güncelleme
```bash
scripts/atlas/upgrade.sh v2.21.0        # yeni dal + Atlas commit'leri + katalog + eksik çeviri listesi
python3 scripts/atlas/untranslated.py   # (her zaman) imza sayfasında Türkçesi eksik metinler
```
Eksikleri `packages/lib/translations/tr/web.po`'da çevir → push → `atlas-image` derler.
Canlıya almadan önce 166'da deneme konteyneri (aynı ağ, `127.0.0.1:3901`, `ssh -L` tüneli) ile
imza sayfasını aç; sonra `compose.yml` image satırı + `docker compose up -d --no-deps documenso`.
⚠️ Yeni sürüm veritabanı göçü içeriyorsa eski imaja geri dönüş mümkün değildir → önce
`documenso-production-database-1` yedeği (pg_dump).

## Ayarlar (`/opt/documenso/.env`)
- `NEXT_PUBLIC_DISABLE_SIGNUP=true` — Documenso'da hesap açma kapalı; imza tamamlandı sayfasındaki
  "hesap aç" paneli görünmez (yedek: `.env.bak-2026-10-16-pre-disable-signup`).
