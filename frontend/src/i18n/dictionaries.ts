import type { Locale } from "./config";

export type Dictionary = {
  app_name: string;
  tagline: string;
  nav: {
    home: string;
    quran: string;
    hadith: string;
    tafsir: string;
    search: string;
  };
  search: {
    placeholder: string;
    button: string;
    no_results: string;
    results_for: string;
    filters: string;
    all: string;
    quran: string;
    hadith: string;
    tafsir: string;
    match_exact: string;
    match_fuzzy: string;
    searching: string;
    prompt: string;
  };
  quran: {
    title: string;
    surahs: string;
    verses: string;
    revelation_makkah: string;
    revelation_madinah: string;
    translation: string;
    tafsir: string;
    show_tafsir: string;
    hide_tafsir: string;
    select_translation: string;
  };
  hadith: {
    title: string;
    collections: string;
    books: string;
    hadiths: string;
    book: string;
    number: string;
    grade: string;
    narrator: string;
    isnad_note: string;
    sahih: string;
    sahih_note: string;
  };
  tafsir: {
    title: string;
    intro: string;
    by_ibn_kathir: string;
    select_surah: string;
  };
  common: {
    theme_light: string;
    theme_dark: string;
    language: string;
    loading: string;
    provenance: string;
    source: string;
    verified: string;
    back: string;
    read: string;
    view: string;
  };
  home: {
    hero_title: string;
    hero_sub: string;
    card_quran: string;
    card_quran_desc: string;
    card_hadith: string;
    card_hadith_desc: string;
    card_tafsir: string;
    card_tafsir_desc: string;
    authenticity_title: string;
    authenticity_desc: string;
    ticker: string[];
  };
};

const en: Dictionary = {
  app_name: "Elaaj bi Dua",
  tagline: "An authenticated corpus of Quran, Hadith & Tafsir",
  nav: { home: "Home", quran: "Quran", hadith: "Hadith", tafsir: "Tafsir", search: "Search" },
  search: {
    placeholder: "Search the Quran, Hadith, and Tafsir…",
    button: "Search",
    no_results: "No results found.",
    results_for: "Results for",
    filters: "Filters",
    all: "All",
    quran: "Quran",
    hadith: "Hadith",
    tafsir: "Tafsir",
    match_exact: "exact",
    match_fuzzy: "similar",
    searching: "Searching…",
    prompt: "Enter a word or phrase to search the corpus.",
  },
  quran: {
    title: "The Noble Quran",
    surahs: "Surahs",
    verses: "verses",
    revelation_makkah: "Makkah",
    revelation_madinah: "Madinah",
    translation: "Translation",
    tafsir: "Tafsir",
    show_tafsir: "Show Tafsir",
    hide_tafsir: "Hide Tafsir",
    select_translation: "Translation",
  },
  hadith: {
    title: "Hadith Collections",
    collections: "Collections",
    books: "Books",
    hadiths: "Hadiths",
    book: "Book",
    number: "No.",
    grade: "Grading",
    narrator: "Narrator",
    isnad_note: "Full chain of narration preserved as transmitted.",
    sahih: "Ṣaḥīḥ · authentic",
    sahih_note: "Graded authentic - from the two Ṣaḥīḥ collections.",
  },
  tafsir: {
    title: "Tafsir Ibn Kathir",
    intro: "Classical Quranic exegesis, aligned verse by verse.",
    by_ibn_kathir: "By Hafiz Ibn Kathir",
    select_surah: "Select a Surah",
  },
  common: {
    theme_light: "Light",
    theme_dark: "Dark",
    language: "Language",
    loading: "Loading…",
    provenance: "Provenance",
    source: "Source",
    verified: "Verified",
    back: "Back",
    read: "Read",
    view: "View",
  },
  home: {
    hero_title: "Guidance, rooted in authentic sources.",
    hero_sub: "Elaaj bi Dua is built to help you find the duas, remedies, and guidance the Quran and Sunnah teach. It rests on a fully authenticated corpus of the Quran, Sahih al-Bukhari and Muslim, and Tafsir Ibn Kathir, preserved exactly as transmitted.",
    card_quran: "The Noble Quran",
    card_quran_desc: "All 114 surahs with translations and aligned tafsir.",
    card_hadith: "Sahih al-Bukhari & Muslim",
    card_hadith_desc: "Both complete, with the full chain of narration for each hadith.",
    card_tafsir: "Tafsir Ibn Kathir",
    card_tafsir_desc: "Classical commentary on every verse, in Arabic, Urdu and English.",
    authenticity_title: "Authenticated at every step",
    authenticity_desc: "Every verse, hadith, and commentary is preserved byte-for-byte from its source and checksummed - nothing altered.",
    ticker: [
      "The complete Quran, all 6,236 verses",
      "Sahih al-Bukhari and Sahih Muslim",
      "Tafsir Ibn Kathir in Arabic, Urdu and English",
      "Every text preserved faithfully to its source",
      "Search the corpus across three languages",
    ],
  },
};

const ur: Dictionary = {
  app_name: "علاج بالدعاء",
  tagline: "قرآن، حدیث اور تفسیر کا مستند ذخیرہ",
  nav: { home: "ہوم", quran: "قرآن", hadith: "حدیث", tafsir: "تفسیر", search: "تلاش" },
  search: {
    placeholder: "قرآن، حدیث اور تفسیر میں تلاش کریں…",
    button: "تلاش کریں",
    no_results: "کوئی نتیجہ نہیں ملا۔",
    results_for: "نتائج برائے",
    filters: "چھانٹیں",
    all: "سب",
    quran: "قرآن",
    hadith: "حدیث",
    tafsir: "تفسیر",
    match_exact: "عین مطابق",
    match_fuzzy: "ملتا جلتا",
    searching: "تلاش جاری ہے…",
    prompt: "ذخیرے میں تلاش کے لیے کوئی لفظ یا فقرہ لکھیں۔",
  },
  quran: {
    title: "قرآنِ مجید",
    surahs: "سورتیں",
    verses: "آیات",
    revelation_makkah: "مکی",
    revelation_madinah: "مدنی",
    translation: "ترجمہ",
    tafsir: "تفسیر",
    show_tafsir: "تفسیر دکھائیں",
    hide_tafsir: "تفسیر چھپائیں",
    select_translation: "ترجمہ",
  },
  hadith: {
    title: "احادیث کے مجموعے",
    collections: "مجموعے",
    books: "کتب",
    hadiths: "احادیث",
    book: "کتاب",
    number: "نمبر",
    grade: "درجہ",
    narrator: "راوی",
    isnad_note: "سند بعینہٖ اسی طرح محفوظ ہے جس طرح منتقل ہوئی۔",
    sahih: "صحیح",
    sahih_note: "صحیحین سے ماخوذ، درجہ: صحیح۔",
  },
  tafsir: {
    title: "تفسیرِ ابنِ کثیر",
    intro: "قرآن کی کلاسیکی تفسیر، آیت بہ آیت۔",
    by_ibn_kathir: "از حافظ ابنِ کثیر",
    select_surah: "سورت منتخب کریں",
  },
  common: {
    theme_light: "روشن",
    theme_dark: "تاریک",
    language: "زبان",
    loading: "لوڈ ہو رہا ہے…",
    provenance: "ماخذ",
    source: "مأخذ",
    verified: "تصدیق شدہ",
    back: "واپس",
    read: "پڑھیں",
    view: "دیکھیں",
  },
  home: {
    hero_title: "رہنمائی، مستند مآخذ سے۔",
    hero_sub: "علاج بالدعاء اس لیے بنایا گیا ہے کہ آپ قرآن و سنت کی سکھائی ہوئی دعائیں، علاج اور رہنمائی تلاش کر سکیں۔ اس کی بنیاد قرآن، صحیح بخاری و مسلم اور تفسیرِ ابنِ کثیر کے مکمل مستند ذخیرے پر ہے، جو بعینہٖ اسی طرح محفوظ ہے جس طرح منتقل ہوا۔",
    card_quran: "قرآنِ مجید",
    card_quran_desc: "تمام ۱۱۴ سورتیں، ترجمے اور تفسیر کے ساتھ۔",
    card_hadith: "صحیح بخاری و مسلم",
    card_hadith_desc: "دونوں مکمل، ہر حدیث کی مکمل سند کے ساتھ۔",
    card_tafsir: "تفسیرِ ابنِ کثیر",
    card_tafsir_desc: "ہر آیت کی کلاسیکی تفسیر، عربی، اردو اور انگریزی میں۔",
    authenticity_title: "ہر مرحلے پر مستند",
    authenticity_desc: "ہر آیت، حدیث اور تفسیر اپنے ماخذ سے حرف بہ حرف محفوظ اور تصدیق شدہ ہے؛ کسی چیز میں کوئی تبدیلی نہیں کی گئی۔",
    ticker: [
      "مکمل قرآن، تمام ۶۲۳۶ آیات",
      "صحیح بخاری اور صحیح مسلم",
      "تفسیرِ ابنِ کثیر عربی، اردو اور انگریزی میں",
      "ہر متن اپنے ماخذ سے بعینہٖ محفوظ",
      "تین زبانوں میں پورے ذخیرے میں تلاش",
    ],
  },
};

const ar: Dictionary = {
  app_name: "علاج بالدعاء",
  tagline: "مجموعة موثّقة من القرآن والحديث والتفسير",
  nav: { home: "الرئيسية", quran: "القرآن", hadith: "الحديث", tafsir: "التفسير", search: "بحث" },
  search: {
    placeholder: "ابحث في القرآن والحديث والتفسير…",
    button: "بحث",
    no_results: "لا توجد نتائج.",
    results_for: "نتائج البحث عن",
    filters: "تصفية",
    all: "الكل",
    quran: "القرآن",
    hadith: "الحديث",
    tafsir: "التفسير",
    match_exact: "مطابق",
    match_fuzzy: "مشابه",
    searching: "جارٍ البحث…",
    prompt: "أدخل كلمة أو عبارة للبحث في المدونة.",
  },
  quran: {
    title: "القرآن الكريم",
    surahs: "السور",
    verses: "آيات",
    revelation_makkah: "مكية",
    revelation_madinah: "مدنية",
    translation: "الترجمة",
    tafsir: "التفسير",
    show_tafsir: "إظهار التفسير",
    hide_tafsir: "إخفاء التفسير",
    select_translation: "الترجمة",
  },
  hadith: {
    title: "مجموعات الحديث",
    collections: "المجموعات",
    books: "الكتب",
    hadiths: "الأحاديث",
    book: "كتاب",
    number: "رقم",
    grade: "الدرجة",
    narrator: "الراوي",
    isnad_note: "السند محفوظ بالكامل كما ورد.",
    sahih: "صحيح",
    sahih_note: "من الصحيحين - درجته صحيح.",
  },
  tafsir: {
    title: "تفسير ابن كثير",
    intro: "تفسير كلاسيكي للقرآن، آية بآية.",
    by_ibn_kathir: "للحافظ ابن كثير",
    select_surah: "اختر سورة",
  },
  common: {
    theme_light: "فاتح",
    theme_dark: "داكن",
    language: "اللغة",
    loading: "جارٍ التحميل…",
    provenance: "المصدر",
    source: "المصدر",
    verified: "موثّق",
    back: "رجوع",
    read: "اقرأ",
    view: "عرض",
  },
  home: {
    hero_title: "هدايةٌ من مصادرَ موثوقة.",
    hero_sub: "صُمّم علاج بالدعاء ليعينك على إيجاد ما علّمه القرآن والسنة من أدعية وعلاج وهداية. ويقوم على مدوّنة موثّقة كاملة من القرآن وصحيح البخاري ومسلم وتفسير ابن كثير، محفوظة كما وردت تمامًا.",
    card_quran: "القرآن الكريم",
    card_quran_desc: "جميع السور الـ١١٤ مع الترجمات والتفسير.",
    card_hadith: "صحيح البخاري ومسلم",
    card_hadith_desc: "كلاهما كامل، مع السند الكامل لكل حديث.",
    card_tafsir: "تفسير ابن كثير",
    card_tafsir_desc: "تفسير كلاسيكي لكل آية، بالعربية والأردية والإنجليزية.",
    authenticity_title: "موثّق في كل خطوة",
    authenticity_desc: "كل آية وحديث وتفسير محفوظ حرفيًا من مصدره وموثّق - لم يُغيَّر شيء.",
    ticker: [
      "القرآن كامل، جميع الآيات الـ٦٢٣٦",
      "صحيح البخاري وصحيح مسلم",
      "تفسير ابن كثير بالعربية والأردية والإنجليزية",
      "كل نص محفوظ بأمانة إلى مصدره",
      "بحث في المدونة بثلاث لغات",
    ],
  },
};

const tr: Dictionary = {
  app_name: "Elaaj bi Dua",
  tagline: "Kur'an, Hadis ve Tefsir'in doğrulanmış külliyatı",
  nav: { home: "Ana Sayfa", quran: "Kur'an", hadith: "Hadis", tafsir: "Tefsir", search: "Ara" },
  search: {
    placeholder: "Kur'an, Hadis ve Tefsir'de ara…",
    button: "Ara",
    no_results: "Sonuç bulunamadı.",
    results_for: "Arama sonuçları",
    filters: "Filtreler",
    all: "Tümü",
    quran: "Kur'an",
    hadith: "Hadis",
    tafsir: "Tefsir",
    match_exact: "birebir",
    match_fuzzy: "benzer",
    searching: "Aranıyor…",
    prompt: "Külliyatta aramak için bir kelime veya ifade girin.",
  },
  quran: {
    title: "Kur'an-ı Kerim",
    surahs: "Sureler",
    verses: "ayet",
    revelation_makkah: "Mekki",
    revelation_madinah: "Medeni",
    translation: "Meal",
    tafsir: "Tefsir",
    show_tafsir: "Tefsiri Göster",
    hide_tafsir: "Tefsiri Gizle",
    select_translation: "Meal",
  },
  hadith: {
    title: "Hadis Külliyatları",
    collections: "Külliyatlar",
    books: "Kitaplar",
    hadiths: "Hadisler",
    book: "Kitap",
    number: "No.",
    grade: "Derece",
    narrator: "Ravi",
    isnad_note: "İsnad zinciri nakledildiği gibi korunmuştur.",
    sahih: "Sahih · sahih",
    sahih_note: "Sahihayn'dan - sahih derecesinde.",
  },
  tafsir: {
    title: "Tefsir İbn Kesir",
    intro: "Klasik Kur'an tefsiri, ayet ayet.",
    by_ibn_kathir: "Hafız İbn Kesir",
    select_surah: "Bir Sure seçin",
  },
  common: {
    theme_light: "Açık",
    theme_dark: "Koyu",
    language: "Dil",
    loading: "Yükleniyor…",
    provenance: "Kaynak",
    source: "Kaynak",
    verified: "Doğrulandı",
    back: "Geri",
    read: "Oku",
    view: "Görüntüle",
  },
  home: {
    hero_title: "Rehberlik, güvenilir kaynaklardan.",
    hero_sub: "Elaaj bi Dua, Kur'an ve Sünnet'in öğrettiği duaları, çareleri ve rehberliği bulmanıza yardımcı olmak için tasarlandı. Kur'an, Sahih-i Buhari ve Müslim ile Tefsir İbn Kesir'in eksiksiz, nakledildiği gibi korunmuş doğrulanmış külliyatına dayanır.",
    card_quran: "Kur'an-ı Kerim",
    card_quran_desc: "114 surenin tamamı, meal ve tefsir ile.",
    card_hadith: "Sahih-i Buhari ve Müslim",
    card_hadith_desc: "İkisi de eksiksiz, her hadis için tam isnad ile.",
    card_tafsir: "Tefsir İbn Kesir",
    card_tafsir_desc: "Her ayet için klasik tefsir; Arapça, Urduca ve İngilizce.",
    authenticity_title: "Her adımda doğrulanmış",
    authenticity_desc: "Her ayet, hadis ve tefsir kaynağından birebir korunur ve sağlaması yapılır - hiçbir şey değiştirilmez.",
    ticker: [
      "Kur'an'ın tamamı, 6.236 ayet",
      "Sahih-i Buhari ve Sahih-i Müslim",
      "Tefsir İbn Kesir; Arapça, Urduca ve İngilizce",
      "Her metin kaynağına sadık korunur",
      "Külliyatta üç dilde arama",
    ],
  },
};

const DICTIONARIES: Record<Locale, Dictionary> = { en, ur, ar, tr };

export function getDictionary(locale: Locale): Dictionary {
  return DICTIONARIES[locale] ?? DICTIONARIES.en;
}
