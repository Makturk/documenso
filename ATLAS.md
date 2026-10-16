# Atlas Solo — Documenso kopyası

Upstream: documenso/documenso **v2.20.0**. Değişiklikler (`atlas/v2.20.0-tr` dalı):

1. **Türkçe dil** (`tr`): `packages/lib/constants/locales.ts` + `i18n.ts`;
   `packages/lib/translations/tr/web.po` — imza sayfası, e-imza bilgilendirmesi, imzalı PDF'e eklenen
   imza sertifikası + denetim kaydı ve müşteriye görünen diğer metinler Türkçe (~720 metin);
   kalanlar (Documenso'nun kendi yönetim ekranları) İngilizce (en kopyası). Eksikleri
   `scripts/atlas/untranslated.py` listeler.
2. **`?lang=xx`**: imza bağlantısındaki dil parametresi çereze ve tarayıcı diline üstün gelir
   (`apps/remix/app/root.tsx` + sunucu çizimi `apps/remix/app/entry.server.tsx`). Atlas davet
   e-postası bağlantıya müşterinin dilini ekler.
3. **Gönderen firma adı**: belge `externalId` = `atlas-sender:<URI kodlu ad>` ise imza sayfası
   başlığı "<Firma> sizi bu belgeyi imzalamaya davet etti" olur
   (`document-signing-page-view-v1.tsx`). Tüm firmalar tek Documenso ekibinden gönderdiği için.
4. ~~Güvenlik yaması GHSA-3494-9j87-fj64~~ — v2.16.0 dalında geçici `atlas-admin-guard.ts` vardı;
   v2.20.0'a geçişte kaldırıldı, upstream #3351 (`/admin` rotalarında `adminMiddleware`) kapatıyor.
5. Upstream iş akışları kaldırıldı. Bizimkiler:
   - `.github/workflows/atlas-image.yml` — `atlas/**` dalına her push'ta imajı GHCR'ye derler.
   - `.github/workflows/atlas-upstream-check.yml` — ayda bir (her ayın 1'i) upstream'i kontrol eder;
     yeni sürüm ya da bizi etkileyen güvenlik duyurusu varsa `upstream-guncelleme` etiketli issue
     açar (sürüm notu özeti, Atlas commit'lerinin yeni sürüme deneme cherry-pick'i, ortak değişen
     dosyalar, yeni veritabanı göçleri, yeni çevrilecek metinler). Elle: Actions → Run workflow.
     Zamanlanmış iş yalnız **varsayılan daldan** koşar → depo varsayılan dalı güncel atlas dalı olmalı.

Lisans: AGPL-3.0 (upstream) — bu depo herkese açık kaynak olarak durur (canlı imajın kaynağı).

## Canlı düzen (166.1.94.181, `/opt/documenso/`)
- `compose.yml`: proje `documenso-production`; servisler `database` (postgres:15, kendi birimi) +
  `documenso` (imaj satırının yanında yorum olarak geri dönüş imajı). Traefik (`dokploy-network`)
  `imza.atlassolo.com` → konteyner 3000. Aynı kutuda başka servisler var (reBildir, asistan,
  Supabase) → **yalnız `documenso` servisine dokun**, her zaman `--no-deps`.
- `.env`: Documenso ayarları. `NEXT_PUBLIC_DISABLE_SIGNUP=true` — hesap açma kapalı; imza
  tamamlandı sayfasındaki "hesap aç" paneli görünmez (yedek: `.env.bak-2026-10-16-pre-disable-signup`).
- Canlı (2026-10-16): `ghcr.io/makturk/documenso:atlas-b85c01246f17` (GHSA yaması + sertifika Türkçe +
  çeviri ikinci kontrolü). Önceki: `atlas-309fa942672c`. Yedek: `/root/documenso-2026-10-16-pre-b85c012.dump`.
- İlk Atlas öncesi imaj (v2.16.0, 2026-07-21 derlemesi):
  `documenso/documenso@sha256:945bd2c04306bd5d78def0c4ceafdffb6b0a106cd6a2543db5acda9a6424b2d9`

## Upstream güncelleme (aylık issue geldiğinde)

Önce issue'yu oku: **güvenlik duyurusu** varsa bekletme; yoksa birkaç sürümü toplu taşımak da olur.
"Yeni veritabanı göçü" sayısı > 0 ise geri dönüş yedekten yapılır (adım 5).

**1. Upstream'i birleştir** (yerel kopya `~/Projects/atlas-documenso`):
```bash
git checkout atlas/v2.16.0-tr && git pull
scripts/atlas/upgrade.sh v2.21.0
```
Betik `atlas/v2.21.0-tr` dalını upstream etiketinden açar, Atlas commit'lerini üstüne taşır (bizim
sildiğimiz upstream iş akışlarındaki çakışmaları kendisi çözer), `ATLAS_BASE_TAG` ve imaj etiketini
günceller, çeviri kataloğunu yeniden çıkarır ve eksik müşteri metinlerini listeler. Gerçek çakışmada
durur: çöz → `git cherry-pick --continue` → kalan commit'leri elle `git cherry-pick`.
Issue'daki "ortak değişen dosyalar"a (bugün `root.tsx`, `entry.server.tsx`,
`document-signing-page-view-v1.tsx`) özellikle bak: `?lang=` ve firma adı hâlâ çalışıyor mu.

**2. Çevir**: `python3 scripts/atlas/untranslated.py` → listelenenleri
`packages/lib/translations/tr/web.po`'da çevir (yer tutucular `{x}`, `<0>…</0>` aynen kalır), tekrar
çalıştır → `0 çevrilmemiş`. ATLAS.md'nin ilk satırındaki sürümü güncelle. Commit.

**3. İmajı derle**: `git push -u origin atlas/v2.21.0-tr` → Actions `atlas-image` (~30–40 dk) →
`ghcr.io/makturk/documenso:atlas-<12 haneli sha>`. Canlıda her zaman bu **değişmez** sha etiketini kullan.

**4. Deneme konteynerinde doğrula** (canlıya dokunmadan, 166'da):
```bash
cd /opt/documenso
IMG=ghcr.io/makturk/documenso:atlas-<sha>
docker pull $IMG
```
- **Göç YOKSA**: canlı veritabanını kullanabilir (şema değişmez):
  ```bash
  docker run -d --name documenso-deneme --env-file .env --network documenso-production_default \
    -v /opt/documenso/cert.p12:/opt/documenso/cert.p12:ro -p 127.0.0.1:3901:3000 $IMG
  ```
- **Göç VARSA**: deneme konteyneri açılışta göçleri çalıştırır → canlı veritabanına BAĞLAMA.
  Yedekten geçici bir veritabanı kur ve onu kullan:
  ```bash
  docker exec documenso-production-database-1 sh -c 'pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB"' > /root/documenso-deneme.dump
  docker run -d --name documenso-deneme-db --network documenso-production_default \
    -e POSTGRES_USER=deneme -e POSTGRES_PASSWORD=deneme -e POSTGRES_DB=deneme postgres:15
  docker exec -i documenso-deneme-db pg_restore -U deneme -d deneme --no-owner < /root/documenso-deneme.dump
  # .env'in kopyasında DATABASE_URL / DIRECT_URL'i documenso-deneme-db'ye çevir → --env-file .env.deneme
  ```
  (`.env` değerlerini ekrana/sohbete basma. `.env` kabukla `source` edilemez (boşluklu değer var);
  veritabanı kullanıcı/adı yukarıdaki gibi konteynerin kendi ortamından okunur.)
- Bilgisayardan: `ssh -L 3901:127.0.0.1:3901 root@166.1.94.181` → `http://localhost:3901`.
  Kontrol: gerçek bir imza bağlantısının yolu `/sign/<token>?lang=tr` (yalnız açıp bak, imzalama) →
  Türkçe + başlıkta firma adı; `curl -s -o /dev/null -w '%{http_code}' 'http://localhost:3901/admin/users.data?_routes=routes%2F_authenticated%2B%2Fadmin%2B%2Fusers._index'`
  → 302 (girişsiz yönetici verisi yok); konteyner günlüğünde hata yok (`docker logs documenso-deneme`).
- Bitince: `docker rm -f documenso-deneme documenso-deneme-db; rm -f /root/documenso-deneme.dump .env.deneme`

**5. Canlıya al**:
```bash
cd /opt/documenso
docker exec documenso-production-database-1 sh -c 'pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB"' > /root/documenso-$(date +%F).dump   # göç varsa ŞART
cp compose.yml compose.yml.bak-$(date +%F)
# compose.yml → documenso.image: yeni sha etiketi; yorumdaki "geri dönüş" = bir önceki çalışan imaj
docker compose up -d --no-deps documenso
docker logs -f --since 2m documenso-production-documenso-1   # "Server listening"; hata yok
```
Sonra `https://imza.atlassolo.com` + yukarıdaki iki kontrol (Türkçe imza sayfası, `/admin` probu 302).
Atlas'tan (demo kiracı) test adresine bir belge gönderip imzala → imzalı PDF + sertifika Türkçe mi.

**6. Geri dönüş**:
- Göç YOKSA: `compose.yml` imaj satırını yorumdaki önceki imaja çevir → `docker compose up -d --no-deps documenso`.
- Göç VARSA: eski imaj yeni şemayla çalışmayabilir → önce `docker compose stop documenso`, yedeği geri yükle
  (`docker exec -i documenso-production-database-1 sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists' < /root/documenso-<tarih>.dump`),
  sonra eski imaj + `up -d --no-deps documenso`. Yedekten sonra imzalanan belgeler kaybolur → hızlı karar ver.

**7. Kapat**:
```bash
gh repo edit Makturk/documenso --default-branch atlas/v2.21.0-tr   # aylık kontrol yeni daldan koşsun
```
Issue'yu kapat (hangi sha canlıda, göç vardı mı). Atlas tarafında `src/lib/esign/documenso.ts`
yorumundaki sürüm notunu güncelle.

## Türkçe'yi upstream'e verme
Upstream çevirileri **Crowdin** ile yönetiyor (`crowdin.yml`; kaynak `en/web.po`). Yeni dili
bakımcılar ekliyor; istekler oylamayla öne çıkıyor:
[documenso/documenso#3321](https://github.com/documenso/documenso/issues/3321) (Türkçe yorumu
var; eski istek #3142 bu konuya taşındı). Yol: Türkçe yorumuna 👍 + çevirimizi teklif eden yorum →
Türkçe Crowdin'e eklenince `tr` dosyası Crowdin'e yüklenir. Temiz kopya (İngilizce yer tutucular
boşaltılmış) üret:
```bash
python3 scripts/atlas/export_tr_for_upstream.py /tmp/documenso-tr.po
```
Türkçe upstream'e girerse: `upgrade.sh` sonrası `tr/web.po` çakışmasında upstream'inkini temel al,
bizim müşteri metinlerimizi üstüne koy; uzun vadede yalnız `?lang=` + firma adı + (gerekirse)
yamalar bizde kalır → bakım yükü küçülür.
