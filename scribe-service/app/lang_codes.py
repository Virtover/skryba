"""Language code converter to MBART-50 codes.

Converts labels like 'english' or 'en' to MBART-50 language codes like 'en_XX'.
Best-effort: if unknown, defaults to 'en_XX'.
"""

from typing import Dict


_MAP: Dict[str, str] = {
    # Core mappings from the user's 'from' list
    "arabic": "ar_AR", "ar": "ar_AR",
    "bulgarian": "bg_BG", "bg": "bg_BG",  # not in provided list, but valid for mbart50
    "german": "de_DE", "de": "de_DE",
    "modern greek": "el_GR", "greek": "el_GR", "el": "el_GR",  # not in provided list, valid for mbart50
    "english": "en_XX", "en": "en_XX",
    "spanish": "es_XX", "es": "es_XX",
    "french": "fr_XX", "fr": "fr_XX",
    "hindi": "hi_IN", "hi": "hi_IN",
    "italian": "it_IT", "it": "it_IT",
    "japanese": "ja_XX", "ja": "ja_XX",
    "dutch": "nl_XX", "nl": "nl_XX",
    "polish": "pl_PL", "pl": "pl_PL",
    "portuguese": "pt_XX", "pt": "pt_XX",
    "russian": "ru_RU", "ru": "ru_RU",
    "swahili": "sw_KE", "sw": "sw_KE",
    "thai": "th_TH", "th": "th_TH",
    "turkish": "tr_TR", "tr": "tr_TR",
    "urdu": "ur_PK", "ur": "ur_PK",
    "vietnamese": "vi_VN", "vi": "vi_VN",
    "chinese": "zh_CN", "zh": "zh_CN",
    # Also allow already-correct mbart codes to pass through
    "ar_ar": "ar_AR", "de_de": "de_DE", "en_xx": "en_XX", "es_xx": "es_XX",
    "fr_xx": "fr_XX", "hi_in": "hi_IN", "it_it": "it_IT", "ja_xx": "ja_XX",
    "nl_xx": "nl_XX", "pl_pl": "pl_PL", "pt_xx": "pt_XX", "ru_ru": "ru_RU",
    "sw_ke": "sw_KE", "th_th": "th_TH", "tr_tr": "tr_TR", "ur_pk": "ur_PK",
    "vi_vn": "vi_VN", "zh_cn": "zh_CN", "el_gr": "el_GR", "bg_bg": "bg_BG",
}


def to_mbart50(label: str) -> str:
    """Convert an input language label/code to an MBART-50 language code.

    Accepts names like 'english', 'modern greek', or 2-letter codes like 'en', 'el'.
    If label is already in MBART format, it will be normalized.
    Defaults to 'en_XX' if unknown.
    """
    if not label:
        return "en_XX"
    norm = label.strip().lower().replace("-", "_")
    return _MAP.get(norm, "en_XX")
