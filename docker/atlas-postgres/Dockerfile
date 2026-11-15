# Atlas — Documenso veritabanı imajı (resmi postgres + güvenlik tazelemesi).
#
# Neden: resmi `postgres:15.x-trixie` imajındaki `gosu` (1.19/1.20 resmi ikilileri dahil) eski
# Go stdlib (1.24.6) ile derleniyor → trivy 1 kritik + 24 yüksek. Ayrıca imaj, Debian güvenlik
# düzeltmesi çıkmış paketleri (ör. zlib1g) ancak bir sonraki resmi yeniden derlemede alıyor.
# Burada: gosu aynı sürümün kaynağından güncel Go ile derlenir; Debian paketleri yükseltilir
# (PostgreSQL paketleri sabit tutulur → ana/ara sürüm bu imajla değişmez).
#
# Ana sürüm DEĞİŞMEZ: PG_TAG yalnız aynı ana sürümün (15.x) yama etiketleriyle güncellenir.
ARG PG_TAG=15.20-trixie
ARG GO_TAG=1.27-trixie

FROM golang:${GO_TAG} AS gosu
# tianon/gosu 1.20 etiketinin commit'i (etiket taşınırsa derleme bozulur → bilinçli güncelle).
ARG GOSU_REF=1.20
ARG GOSU_COMMIT=29b939aa5bd4dc588af765b8248f6e39150d2565
RUN git clone -q --depth 1 -b "$GOSU_REF" https://github.com/tianon/gosu /src \
 && cd /src \
 && test "$(git rev-parse HEAD)" = "$GOSU_COMMIT" \
 && CGO_ENABLED=0 go build -trimpath -ldflags="-d -s -w" -o /out/gosu . \
 && /out/gosu --version

FROM postgres:${PG_TAG}
COPY upgrade-os.sh /usr/local/sbin/atlas-upgrade-os.sh
RUN sh /usr/local/sbin/atlas-upgrade-os.sh && rm /usr/local/sbin/atlas-upgrade-os.sh
COPY --from=gosu /out/gosu /usr/local/bin/gosu
RUN set -eux; chmod 0755 /usr/local/bin/gosu; gosu --version; gosu nobody true; postgres --version
