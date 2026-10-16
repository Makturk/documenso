# Atlas Solo — Documenso kopyası

Upstream: documenso/documenso **v2.16.0** (canlıdaki sürümle aynı → veritabanı şeması değişmez,
geri dönüş güvenli). Değişiklikler (`atlas/v2.16.0-tr` dalı):

1. **Türkçe dil** (`tr`): `packages/lib/constants/locales.ts` + `i18n.ts`;
   `packages/lib/translations/tr/web.po` — imza sayfası ve müşteriye görünen ~450 metin Türkçe,
   kalanlar İngilizce (en kopyası).
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
Yeni sürüme geçerken: dalı yeni etiketin üzerine yeniden kur, 4 değişikliği uygula,
`lingui extract` sonrası `tr/web.po`'daki yeni imza sayfası metinlerini çevir. Veritabanı göçü
olan sürümde geri dönüş eski imajla mümkün değildir → önce yedek.
