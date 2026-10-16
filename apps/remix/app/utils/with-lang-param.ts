import { APP_I18N_OPTIONS, type SupportedLanguageCodes } from '@documenso/lib/constants/i18n';

/**
 * Atlas Solo: imza bağlantısındaki `?lang=xx` parametresini kendi içimizdeki bir yönlendirmeye taşır.
 *
 * Loader yönlendirince kök loader'ın dil çerezi yanıta yazılmaz; parametre düşerse çerezi olmayan
 * müşteri hedef sayfayı (tamamlandı / reddedildi / süresi doldu / bekleniyor) tarayıcı dilinde görür.
 * Yalnız desteklenen bir dil kodu taşınır; geçersiz değer yok sayılır.
 */
export const withLangParam = (request: Request, path: string) => {
  const lang = new URL(request.url).searchParams.get('lang');

  if (!lang || !APP_I18N_OPTIONS.supportedLangs.includes(lang as SupportedLanguageCodes)) {
    return path;
  }

  return `${path}${path.includes('?') ? '&' : '?'}lang=${encodeURIComponent(lang)}`;
};
