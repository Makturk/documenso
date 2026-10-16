// Atlas Solo — GHSA-3494-9j87-fj64 (yüksek) yaması, v2.16.0 için.
//
// Açık: yönetici sayfalarının veri yükleyicileri (loader) oturum kontrolünü yalnız `_layout`
// loader'ında yapıyordu; React Router tek-istek veri çağrısı (`/admin/users.data?_routes=…`)
// yalnız istenen route'un loader'ını çalıştırdığı için girişsiz istek tüm kullanıcı ad/e-postalarını
// döndürüyordu. Upstream v2.18.0'da React Router middleware'e geçerek kapattı (#3351, büyük
// yeniden yapılandırma). Bu yama aynı kuralı Hono katmanında uygular: `/admin` altındaki HER istek
// (sayfa + `.data`) yönetici oturumu yoksa ana sayfaya yönlendirilir. Upstream v2.18.0+ üzerine
// taşınırken bu dosya ve router.ts'teki tek satır kaldırılabilir (upstream düzeltmesi yeterli).
import { getOptionalSession } from '@documenso/auth/server/lib/utils/get-session';
import { isAdmin } from '@documenso/lib/utils/is-admin';
import type { Context, Next } from 'hono';

const basePath = (process.env.NEXT_PUBLIC_BASE_PATH ?? '').replace(/\/$/, '').toLowerCase();

/** `/admin`, `/admin/...`, `/admin.data` (React Router eşleşmesi büyük/küçük harf duyarsız). */
export const isAdminPath = (rawPath: string): boolean => {
  let path = rawPath.toLowerCase();

  try {
    path = decodeURIComponent(path).toLowerCase();
  } catch {
    // Bozuk kodlama — ham yol üzerinden karar ver.
  }

  if (basePath && path.startsWith(basePath)) {
    path = path.slice(basePath.length) || '/';
  }

  path = path.replace(/\/{2,}/g, '/');

  return path === '/admin' || path.startsWith('/admin/') || path.startsWith('/admin.');
};

export const atlasAdminGuard = async (c: Context, next: Next) => {
  if (!isAdminPath(c.req.path)) {
    return next();
  }

  const { user } = await getOptionalSession(c);

  if (!user || !isAdmin(user)) {
    return c.redirect(basePath ? `${basePath}/` : '/', 302);
  }

  return next();
};
