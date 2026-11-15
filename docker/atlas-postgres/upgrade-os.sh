#!/bin/sh
# Debian paketlerini yükseltir; kurulu PostgreSQL / libpq paketlerini sabit tutar
# (sürüm imaj etiketiyle — PG_TAG — belirlenir, apt ile kaymaz).
set -eu

pinned=$(dpkg-query -W -f='${db:Status-Abbrev} ${Package}\n' \
  | awk '$1 == "ii" && $2 ~ /^(postgresql|libpq)/ { print $2 }')

if [ -n "$pinned" ]; then
  # shellcheck disable=SC2086
  apt-mark hold $pinned >/dev/null
fi

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y --no-install-recommends

if [ -n "$pinned" ]; then
  # shellcheck disable=SC2086
  apt-mark unhold $pinned >/dev/null
fi

rm -rf /var/lib/apt/lists/*
