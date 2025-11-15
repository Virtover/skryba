const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function scribeFile(file: File, summaryLang: string): Promise<Blob> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/scribe-file/${summaryLang}`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Failed to scribe file: ${response.statusText}`);
  }

  return response.blob();
}

export async function scribeUrl(url: string, summaryLang: string): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/scribe-url/${summaryLang}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    throw new Error(`Failed to scribe URL: ${response.statusText}`);
  }

  return response.blob();
}

export const LANGUAGE_CODES = [
  { code: 'ar_AR', label: 'Arabic' },
  { code: 'cs_CZ', label: 'Czech' },
  { code: 'de_DE', label: 'German' },
  { code: 'en_XX', label: 'English' },
  { code: 'es_XX', label: 'Spanish' },
  { code: 'et_EE', label: 'Estonian' },
  { code: 'fi_FI', label: 'Finnish' },
  { code: 'fr_XX', label: 'French' },
  { code: 'gu_IN', label: 'Gujarati' },
  { code: 'hi_IN', label: 'Hindi' },
  { code: 'it_IT', label: 'Italian' },
  { code: 'ja_XX', label: 'Japanese' },
  { code: 'kk_KZ', label: 'Kazakh' },
  { code: 'ko_KR', label: 'Korean' },
  { code: 'lt_LT', label: 'Lithuanian' },
  { code: 'lv_LV', label: 'Latvian' },
  { code: 'my_MM', label: 'Burmese' },
  { code: 'ne_NP', label: 'Nepali' },
  { code: 'nl_XX', label: 'Dutch' },
  { code: 'ro_RO', label: 'Romanian' },
  { code: 'ru_RU', label: 'Russian' },
  { code: 'si_LK', label: 'Sinhala' },
  { code: 'tr_TR', label: 'Turkish' },
  { code: 'vi_VN', label: 'Vietnamese' },
  { code: 'zh_CN', label: 'Chinese' },
  { code: 'af_ZA', label: 'Afrikaans' },
  { code: 'az_AZ', label: 'Azerbaijani' },
  { code: 'bn_IN', label: 'Bengali' },
  { code: 'fa_IR', label: 'Persian' },
  { code: 'he_IL', label: 'Hebrew' },
  { code: 'hr_HR', label: 'Croatian' },
  { code: 'id_ID', label: 'Indonesian' },
  { code: 'ka_GE', label: 'Georgian' },
  { code: 'km_KH', label: 'Khmer' },
  { code: 'mk_MK', label: 'Macedonian' },
  { code: 'ml_IN', label: 'Malayalam' },
  { code: 'mn_MN', label: 'Mongolian' },
  { code: 'mr_IN', label: 'Marathi' },
  { code: 'pl_PL', label: 'Polish' },
  { code: 'ps_AF', label: 'Pashto' },
  { code: 'pt_XX', label: 'Portuguese' },
  { code: 'sv_SE', label: 'Swedish' },
  { code: 'sw_KE', label: 'Swahili' },
  { code: 'ta_IN', label: 'Tamil' },
  { code: 'te_IN', label: 'Telugu' },
  { code: 'th_TH', label: 'Thai' },
  { code: 'tl_XX', label: 'Tagalog' },
  { code: 'uk_UA', label: 'Ukrainian' },
  { code: 'ur_PK', label: 'Urdu' },
  { code: 'xh_ZA', label: 'Xhosa' },
  { code: 'gl_ES', label: 'Galician' },
  { code: 'sl_SI', label: 'Slovene' },
];
