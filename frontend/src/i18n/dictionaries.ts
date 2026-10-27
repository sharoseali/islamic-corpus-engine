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
    match_partial: string;
    match_semantic: string;
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
  input_tools: {
    recording: string;
    transcribing: string;
    voice_failed: string;
    keyboard: string;
    keyboard_urdu: string;
    keyboard_arabic: string;
    keyboard_english: string;
    voice: string;
    voice_stop: string;
    listening: string;
    voice_lang: string;
    voice_unsupported: string;
    voice_insecure: string;
    voice_denied: string;
    voice_no_speech: string;
    close: string;
    space: string;
    backspace: string;
    clear: string;
  };
  results: {
    all_results: string;
    search_in_quran: string;
    search_in_hadith: string;
    search_in_tafsir: string;
    order_mushaf: string;
    order_relevance: string;
    load_more: string;
    no_more: string;
    matched_in_arabic: string;
    matched_in_translation: string;
    by_meaning: string;
    by_meaning_extra: string;
    open_reader: string;
    open_tafsir: string;
    sahih_collection: string;
    ayat_count: string;
    root: string;
    word_form: string;
    by_root: string;
    by_word_form: string;
    words_count: string;
    topics: string;
    hadith_count: string;
    passages_count: string;
    showing: string;
    exact_word_matches: string;
    languages: string;
  };
  reader: {
    ayat_range: string;
    jump_to_ayah: string;
    previous: string;
    next: string;
    back_to_top: string;
    highlighted_from_search: string;
    go: string;
    page_label: string;
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
    match_partial: "related",
    match_semantic: "by meaning",
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
  input_tools: {
    recording: "Recording… tap the mic again to finish",
    transcribing: "Writing out your words…",
    voice_failed: "Could not turn the recording into text. Please try again.",
    keyboard: "On-screen keyboard",
    keyboard_urdu: "Urdu",
    keyboard_arabic: "Arabic",
    keyboard_english: "English",
    voice: "Speak to search",
    voice_stop: "Stop listening",
    listening: "Listening… speak now",
    voice_lang: "Voice language",
    voice_unsupported: "This browser cannot record audio. Please use a current version of Chrome, Edge, Firefox or Safari.",
    voice_insecure: "Voice input needs a secure connection. Open the site on localhost or over HTTPS.",
    voice_denied: "Microphone access was blocked. Allow it in your browser settings.",
    voice_no_speech: "No speech was heard. Please try again.",
    close: "Close",
    space: "Space",
    backspace: "Backspace",
    clear: "Clear",
  },
  results: {
    all_results: "All results",
    search_in_quran: "Search in the Quran",
    search_in_hadith: "Search in Hadith",
    search_in_tafsir: "Search in Tafsir",
    order_mushaf: "Mushaf order",
    order_relevance: "Relevance",
    load_more: "Load more",
    no_more: "End of results",
    matched_in_arabic: "matched in Arabic",
    matched_in_translation: "matched in translation",
    by_meaning: "by meaning",
    by_meaning_extra: "more by meaning",
    root: "Root",
    word_form: "Word form",
    by_root: "by root",
    by_word_form: "word form",
    words_count: "words",
    topics: "Topics (Quran themes, English)",
    open_reader: "Open in reader",
    open_tafsir: "Read tafsir",
    sahih_collection: "Sahih collection",
    ayat_count: "ayat",
    hadith_count: "hadith",
    passages_count: "passages",
    showing: "Showing",
    exact_word_matches: "exact word matches",
    languages: "Languages",
  },
  reader: {
    ayat_range: "Ayat {from} to {to} of {total}",
    jump_to_ayah: "Go to ayah",
    previous: "Previous",
    next: "Next",
    back_to_top: "Back to top",
    highlighted_from_search: "Highlighted: matches for “{q}”",
    go: "Go",
    page_label: "Page {page} of {pages}",
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
    match_partial: "جزوی مطابقت",
    match_semantic: "معنوی مطابقت",
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
  input_tools: {
    recording: "ریکارڈنگ جاری ہے… ختم کرنے کے لیے مائیک دوبارہ دبائیں",
    transcribing: "آپ کے الفاظ لکھے جا رہے ہیں…",
    voice_failed: "ریکارڈنگ کو تحریر میں نہیں بدلا جا سکا۔ دوبارہ کوشش کریں۔",
    keyboard: "آن اسکرین کی بورڈ",
    keyboard_urdu: "اردو",
    keyboard_arabic: "عربی",
    keyboard_english: "انگریزی",
    voice: "بول کر تلاش کریں",
    voice_stop: "سننا بند کریں",
    listening: "سن رہا ہے… اب بولیں",
    voice_lang: "آواز کی زبان",
    voice_unsupported: "یہ براؤزر آواز ریکارڈ نہیں کر سکتا۔ کروم، ایج، فائرفاکس یا سفاری کا تازہ ورژن استعمال کریں۔",
    voice_insecure: "آواز سے تلاش کے لیے محفوظ کنکشن ضروری ہے۔ سائٹ localhost یا HTTPS پر کھولیں۔",
    voice_denied: "مائیکروفون کی اجازت نہیں ملی۔ براؤزر کی ترتیبات میں اجازت دیں۔",
    voice_no_speech: "کوئی آواز سنائی نہیں دی۔ دوبارہ کوشش کریں۔",
    close: "بند کریں",
    space: "خالی جگہ",
    backspace: "مٹائیں",
    clear: "سب صاف کریں",
  },
  results: {
    all_results: "تمام نتائج",
    search_in_quran: "قرآن میں تلاش کریں",
    search_in_hadith: "حدیث میں تلاش کریں",
    search_in_tafsir: "تفسیر میں تلاش کریں",
    order_mushaf: "مصحف کی ترتیب",
    order_relevance: "مطابقت",
    load_more: "مزید دکھائیں",
    no_more: "نتائج ختم",
    matched_in_arabic: "عربی متن میں ملا",
    matched_in_translation: "ترجمے میں ملا",
    by_meaning: "معنی کے اعتبار سے",
    by_meaning_extra: "مزید معنوی نتائج",
    root: "مادہ",
    word_form: "لفظی صورت",
    by_root: "مادے سے",
    by_word_form: "لفظی صورت",
    words_count: "الفاظ",
    topics: "موضوعات (قرآنی مضامین، انگریزی)",
    open_reader: "قرآن میں کھولیں",
    open_tafsir: "تفسیر پڑھیں",
    sahih_collection: "صحیح مجموعہ",
    ayat_count: "آیات",
    hadith_count: "احادیث",
    passages_count: "اقتباسات",
    showing: "دکھائے جا رہے ہیں",
    exact_word_matches: "لفظی مطابقت",
    languages: "زبانیں",
  },
  reader: {
    ayat_range: "آیت {from} تا {to}، کل {total}",
    jump_to_ayah: "آیت پر جائیں",
    previous: "پچھلا",
    next: "اگلا",
    back_to_top: "اوپر جائیں",
    highlighted_from_search: "نمایاں: “{q}” کے مطابق الفاظ",
    go: "جائیں",
    page_label: "صفحہ {page} از {pages}",
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
    match_partial: "مطابقة جزئية",
    match_semantic: "مطابقة بالمعنى",
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
  input_tools: {
    recording: "جارٍ التسجيل… اضغط على الميكروفون مرة أخرى للإنهاء",
    transcribing: "جارٍ تحويل كلامك إلى نص…",
    voice_failed: "تعذّر تحويل التسجيل إلى نص. حاول مرة أخرى.",
    keyboard: "لوحة المفاتيح على الشاشة",
    keyboard_urdu: "الأردية",
    keyboard_arabic: "العربية",
    keyboard_english: "الإنجليزية",
    voice: "ابحث بالصوت",
    voice_stop: "إيقاف الاستماع",
    listening: "جارٍ الاستماع… تحدّث الآن",
    voice_lang: "لغة الصوت",
    voice_unsupported: "هذا المتصفح لا يستطيع تسجيل الصوت. استخدم إصدارًا حديثًا من Chrome أو Edge أو Firefox أو Safari.",
    voice_insecure: "الإدخال الصوتي يحتاج إلى اتصال آمن. افتح الموقع عبر localhost أو HTTPS.",
    voice_denied: "تم حظر الوصول إلى الميكروفون. اسمح به من إعدادات المتصفح.",
    voice_no_speech: "لم يُسمع أي كلام. حاول مرة أخرى.",
    close: "إغلاق",
    space: "مسافة",
    backspace: "حذف",
    clear: "مسح الكل",
  },
  results: {
    all_results: "كل النتائج",
    search_in_quran: "ابحث في القرآن",
    search_in_hadith: "ابحث في الحديث",
    search_in_tafsir: "ابحث في التفسير",
    order_mushaf: "ترتيب المصحف",
    order_relevance: "الأكثر صلة",
    load_more: "عرض المزيد",
    no_more: "نهاية النتائج",
    matched_in_arabic: "وردت في النص العربي",
    matched_in_translation: "وردت في الترجمة",
    by_meaning: "بالمعنى",
    by_meaning_extra: "المزيد بالمعنى",
    root: "الجذر",
    word_form: "صيغة الكلمة",
    by_root: "بالجذر",
    by_word_form: "بالصيغة",
    words_count: "كلمة",
    topics: "الموضوعات (مواضيع الآيات، بالإنجليزية)",
    open_reader: "افتح في المصحف",
    open_tafsir: "اقرأ التفسير",
    sahih_collection: "مجموعة صحيحة",
    ayat_count: "آية",
    hadith_count: "حديث",
    passages_count: "مقطع",
    showing: "يُعرض",
    exact_word_matches: "مطابقة لفظية",
    languages: "اللغات",
  },
  reader: {
    ayat_range: "الآيات {from} إلى {to} من {total}",
    jump_to_ayah: "الانتقال إلى آية",
    previous: "السابق",
    next: "التالي",
    back_to_top: "العودة للأعلى",
    highlighted_from_search: "مميّز: الكلمات المطابقة لـ “{q}”",
    go: "انتقل",
    page_label: "الصفحة {page} من {pages}",
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
    match_partial: "kısmi eşleşme",
    match_semantic: "anlamca ilgili",
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
  input_tools: {
    recording: "Kaydediliyor… bitirmek için mikrofona tekrar dokunun",
    transcribing: "Sözleriniz yazıya dökülüyor…",
    voice_failed: "Kayıt yazıya dönüştürülemedi. Lütfen tekrar deneyin.",
    keyboard: "Ekran klavyesi",
    keyboard_urdu: "Urduca",
    keyboard_arabic: "Arapça",
    keyboard_english: "İngilizce",
    voice: "Sesle ara",
    voice_stop: "Dinlemeyi durdur",
    listening: "Dinleniyor… şimdi konuşun",
    voice_lang: "Ses dili",
    voice_unsupported: "Bu tarayıcı ses kaydedemiyor. Lütfen Chrome, Edge, Firefox veya Safari'nin güncel bir sürümünü kullanın.",
    voice_insecure: "Sesli giriş güvenli bağlantı gerektirir. Siteyi localhost veya HTTPS üzerinden açın.",
    voice_denied: "Mikrofon erişimi engellendi. Tarayıcı ayarlarından izin verin.",
    voice_no_speech: "Ses algılanmadı. Lütfen tekrar deneyin.",
    close: "Kapat",
    space: "Boşluk",
    backspace: "Sil",
    clear: "Temizle",
  },
  results: {
    all_results: "Tüm sonuçlar",
    search_in_quran: "Kur'an'da ara",
    search_in_hadith: "Hadiste ara",
    search_in_tafsir: "Tefsirde ara",
    order_mushaf: "Mushaf sırası",
    order_relevance: "İlgililik",
    load_more: "Daha fazla",
    no_more: "Sonuçların sonu",
    matched_in_arabic: "Arapça metinde bulundu",
    matched_in_translation: "çeviride bulundu",
    by_meaning: "anlamca",
    by_meaning_extra: "anlamca daha fazla",
    root: "Kök",
    word_form: "Kelime biçimi",
    by_root: "kökten",
    by_word_form: "kelime biçimi",
    words_count: "kelime",
    topics: "Konular (ayet temaları, İngilizce)",
    open_reader: "Okuyucuda aç",
    open_tafsir: "Tefsiri oku",
    sahih_collection: "Sahih koleksiyon",
    ayat_count: "ayet",
    hadith_count: "hadis",
    passages_count: "bölüm",
    showing: "Gösterilen",
    exact_word_matches: "kelime eşleşmesi",
    languages: "Diller",
  },
  reader: {
    ayat_range: "{total} ayetten {from}-{to} arası",
    jump_to_ayah: "Ayete git",
    previous: "Önceki",
    next: "Sonraki",
    back_to_top: "Başa dön",
    highlighted_from_search: "Vurgulanan: “{q}” eşleşmeleri",
    go: "Git",
    page_label: "Sayfa {page}/{pages}",
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
