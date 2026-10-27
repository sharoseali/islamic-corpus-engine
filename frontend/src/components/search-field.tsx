"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useI18n } from "./providers";
import { ElaajLoader } from "./elaaj-loader";
import { API_BASE } from "@/lib/api";
import type { Locale } from "@/i18n/config";

// Search input with an on-screen Urdu/Arabic keyboard and voice input, for
// users who have no Urdu or Arabic keyboard installed.

type KeyboardLayout = "ur" | "ar" | "en";
type VoiceLang = "ur" | "ar" | "en";
type VoiceState = "idle" | "listening" | "recording" | "transcribing";

// Keys follow alphabetical order, which is easier to scan than a
// typewriter layout for users who do not already know one. They flow
// into a grid whose column count adapts to the screen width.
const LAYOUTS: Record<KeyboardLayout, string[]> = {
  ur: [
    "ا", "آ", "ب", "پ", "ت", "ٹ", "ث", "ج", "چ", "ح", "خ", "د", "ڈ", "ذ", "ر",
    "ڑ", "ز", "ژ", "س", "ش", "ص", "ض", "ط", "ظ", "ع", "غ", "ف", "ق", "ک", "گ",
    "ل", "م", "ن", "ں", "و", "ہ", "ھ", "ء", "ی", "ے", "ئ", "ؤ", "ۃ", "ۓ", "۔",
    "۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹", "۰", "،", "؟",
  ],
  ar: [
    "ا", "أ", "إ", "آ", "ب", "ت", "ث", "ج", "ح", "خ", "د", "ذ", "ر", "ز", "س",
    "ش", "ص", "ض", "ط", "ظ", "ع", "غ", "ف", "ق", "ك", "ل", "م", "ن", "ه", "و",
    "ي", "ى", "ة", "ء", "ؤ", "ئ", "َ", "ُ", "ِ", "ّ", "ْ",
    "ً", "ٌ", "ٍ", "١", "٢", "٣", "٤", "٥", "٦", "٧", "٨", "٩", "٠",
    "،", "؟",
  ],
  en: [
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
    "q", "w", "e", "r", "t", "y", "u", "i", "o", "p",
    "a", "s", "d", "f", "g", "h", "j", "k", "l", "'",
    "z", "x", "c", "v", "b", "n", "m", ",", ".", "?",
  ],
};

// Latin keys read left to right; Urdu and Arabic right to left.
const LAYOUT_DIR: Record<KeyboardLayout, "rtl" | "ltr"> = { ur: "rtl", ar: "rtl", en: "ltr" };

// Harakat render on a dotted circle so the key is visible on its own.
const isMark = (k: string) => /[ً-ْ]/.test(k);

const SPEECH_LOCALE: Record<VoiceLang, string> = {
  ur: "ur-PK",
  ar: "ar-SA",
  en: "en-US",
};

// Content exists in ar/ur/en only, so Turkish users speak Arabic by default.
const DEFAULT_VOICE: Record<Locale, VoiceLang> = { ur: "ur", ar: "ar", en: "en", tr: "ar" };
// The keyboard opens in the UI language; Turkish uses the Latin layout.
const DEFAULT_LAYOUT: Record<Locale, KeyboardLayout> = { ur: "ur", ar: "ar", en: "en", tr: "en" };

const VOICE_LABEL: Record<VoiceLang, string> = { ur: "اردو", ar: "العربية", en: "English" };

// Server transcription caps a clip at this length.
const MAX_RECORDING_MS = 20000;

// Minimal typing for the Web Speech API, which TypeScript's DOM lib omits.
type Recognition = {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  maxAlternatives: number;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }> & { isFinal: boolean }> }) => void) | null;
  onerror: ((e: { error: string }) => void) | null;
  onend: (() => void) | null;
};

function getRecognitionCtor(): (new () => Recognition) | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as {
    SpeechRecognition?: new () => Recognition;
    webkitSpeechRecognition?: new () => Recognition;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

// Tidy a spoken transcript into a clean search query: collapse whitespace
// and drop trailing sentence punctuation that speech engines append.
function cleanTranscript(text: string): string {
  return text.replace(/\s+/g, " ").replace(/[.,!?؟۔،]+$/u, "").trim();
}

export function SearchField({
  value,
  onChange,
  onSubmit,
  variant,
  autoFocus,
  placeholder,
}: {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  variant: "hero" | "page";
  autoFocus?: boolean;
  placeholder?: string;
}) {
  const { locale, dict } = useI18n();
  const t = dict.input_tools;
  const inputRef = useRef<HTMLInputElement>(null);
  const dockRef = useRef<HTMLDivElement>(null);
  const recRef = useRef<Recognition | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const stopTimerRef = useRef<number | null>(null);
  // Browsers such as Brave expose the Web Speech API but cannot reach its
  // service; after a "network" error, record and transcribe on our server.
  const useServerRef = useRef(false);
  // Text already in the box when dictation started; speech is appended to it.
  const baseRef = useRef("");

  const [kbOpen, setKbOpen] = useState(false);
  const [layout, setLayout] = useState<KeyboardLayout>(DEFAULT_LAYOUT[locale]);
  const [voiceLang, setVoiceLang] = useState<VoiceLang>(DEFAULT_VOICE[locale]);
  const [voice, setVoice] = useState<VoiceState>("idle");
  const [voiceMsg, setVoiceMsg] = useState<string | null>(null);

  useEffect(
    () => () => {
      recRef.current?.abort();
      if (recorderRef.current?.state === "recording") recorderRef.current.stop();
    },
    [],
  );

  // The keyboard is docked to the bottom of the screen. Pad the page by its
  // height so nothing ends up hidden behind it, and keep the input visible.
  useEffect(() => {
    if (!kbOpen || !dockRef.current) return;
    const dock = dockRef.current;
    const body = document.body;
    const prev = body.style.paddingBottom;
    const ro = new ResizeObserver(() => {
      body.style.paddingBottom = `${dock.offsetHeight + 12}px`;
    });
    ro.observe(dock);
    inputRef.current?.scrollIntoView({ block: "center", behavior: "smooth" });
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setKbOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => {
      ro.disconnect();
      body.style.paddingBottom = prev;
      window.removeEventListener("keydown", onKey);
    };
  }, [kbOpen]);

  // Insert at the caret (or replace the selection) and keep focus in the box.
  const insert = (text: string) => {
    const el = inputRef.current;
    const start = el?.selectionStart ?? value.length;
    const end = el?.selectionEnd ?? value.length;
    onChange(value.slice(0, start) + text + value.slice(end));
    requestAnimationFrame(() => {
      el?.focus();
      el?.setSelectionRange(start + text.length, start + text.length);
    });
  };

  const backspace = () => {
    const el = inputRef.current;
    const start = el?.selectionStart ?? value.length;
    const end = el?.selectionEnd ?? value.length;
    if (start === end && start === 0) return;
    // Remove the whole selection, or one code point before the caret.
    const from = start === end ? start - (Array.from(value.slice(0, start)).pop()?.length ?? 1) : start;
    onChange(value.slice(0, from) + value.slice(end));
    requestAnimationFrame(() => {
      el?.focus();
      el?.setSelectionRange(from, from);
    });
  };

  // --- Voice: browser speech engine (live text) ---------------------------

  const startBrowserSpeech = (Ctor: new () => Recognition) => {
    const rec = new Ctor();
    rec.lang = SPEECH_LOCALE[voiceLang];
    rec.interimResults = true;
    rec.continuous = false;
    rec.maxAlternatives = 1;
    let fellBack = false;

    rec.onresult = (e) => {
      let text = "";
      for (let i = 0; i < e.results.length; i++) text += e.results[i][0].transcript;
      const last = e.results[e.results.length - 1];
      onChange(baseRef.current + (last?.isFinal ? cleanTranscript(text) : text));
    };
    rec.onerror = (e) => {
      if (e.error === "network" || e.error === "service-not-allowed" || e.error === "language-not-supported") {
        useServerRef.current = true;
        fellBack = true;
      } else if (e.error === "not-allowed") setVoiceMsg(t.voice_denied);
      else if (e.error === "no-speech") setVoiceMsg(t.voice_no_speech);
      else if (e.error !== "aborted") setVoiceMsg(t.voice_failed);
    };
    rec.onend = () => {
      recRef.current = null;
      if (fellBack) {
        void startServerRecording();
        return;
      }
      setVoice("idle");
      inputRef.current?.focus();
    };

    recRef.current = rec;
    setVoice("listening");
    rec.start();
  };

  // --- Voice: record, then transcribe on our server (any browser) --------

  const startServerRecording = async () => {
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setVoice("idle");
      setVoiceMsg(t.voice_unsupported);
      return;
    }
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setVoice("idle");
      setVoiceMsg(t.voice_denied);
      return;
    }

    const recorder = new MediaRecorder(stream);
    const chunks: Blob[] = [];
    recorder.ondataavailable = (e) => {
      if (e.data.size) chunks.push(e.data);
    };
    recorder.onstop = async () => {
      stream.getTracks().forEach((tr) => tr.stop());
      if (stopTimerRef.current) window.clearTimeout(stopTimerRef.current);
      recorderRef.current = null;
      const blob = new Blob(chunks, { type: recorder.mimeType || "audio/webm" });
      if (blob.size < 1000) {
        setVoice("idle");
        setVoiceMsg(t.voice_no_speech);
        return;
      }
      setVoice("transcribing");
      try {
        const form = new FormData();
        form.append("audio", blob, "speech");
        const res = await fetch(`${API_BASE}/speech/transcribe?lang=${voiceLang}`, {
          method: "POST",
          body: form,
        });
        if (!res.ok) throw new Error(String(res.status));
        const data: { text: string } = await res.json();
        const text = cleanTranscript(data.text ?? "");
        if (text) onChange(baseRef.current + text);
        else setVoiceMsg(t.voice_no_speech);
      } catch {
        setVoiceMsg(t.voice_failed);
      } finally {
        setVoice("idle");
        inputRef.current?.focus();
      }
    };

    recorderRef.current = recorder;
    recorder.start();
    setVoice("recording");
    stopTimerRef.current = window.setTimeout(() => {
      if (recorder.state === "recording") recorder.stop();
    }, MAX_RECORDING_MS);
  };

  const startVoice = () => {
    setVoiceMsg(null);
    if (!window.isSecureContext) {
      setVoiceMsg(t.voice_insecure);
      return;
    }
    baseRef.current = value.trim() ? value.trim() + " " : "";
    const Ctor = getRecognitionCtor();
    if (Ctor && !useServerRef.current) startBrowserSpeech(Ctor);
    else void startServerRecording();
  };

  const stopVoice = () => {
    recRef.current?.stop();
    if (recorderRef.current?.state === "recording") recorderRef.current.stop();
  };

  const runSubmit = () => {
    if (voice === "listening") stopVoice();
    setKbOpen(false);
    onSubmit();
  };

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    runSubmit();
  };

  // Keep focus in the input when a tool button is pressed.
  const keepFocus = (e: React.MouseEvent) => e.preventDefault();

  const hero = variant === "hero";
  const busy = voice !== "idle";
  const status =
    voice === "listening" ? t.listening : voice === "recording" ? t.recording : voice === "transcribing" ? t.transcribing : null;

  return (
    <form onSubmit={submit} className={`search-field search-field--${variant}`}>
      <div className="search-field__row">
        <div className="search-field__box">
          <input
            ref={inputRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={status ?? placeholder ?? dict.search.placeholder}
            aria-label={dict.search.button}
            autoFocus={autoFocus}
            // With the on-screen keyboard open, suppress the phone's own keyboard.
            inputMode={kbOpen ? "none" : "search"}
            dir="auto"
            className="search-field__input"
          />
          <button
            type="button"
            className={`search-field__tool${kbOpen ? " is-active" : ""}`}
            onMouseDown={keepFocus}
            onClick={() => setKbOpen((v) => !v)}
            aria-label={t.keyboard}
            aria-pressed={kbOpen}
            title={t.keyboard}
          >
            <KeyboardIcon />
          </button>
          <button
            type="button"
            className={`search-field__tool${voice === "listening" || voice === "recording" ? " is-listening" : ""}`}
            onMouseDown={keepFocus}
            onClick={voice === "idle" ? startVoice : stopVoice}
            disabled={voice === "transcribing"}
            aria-label={busy ? t.voice_stop : t.voice}
            aria-pressed={busy}
            title={busy ? t.voice_stop : t.voice}
          >
            {voice === "transcribing" ? <span className="search-field__spinner" aria-hidden /> : <MicIcon />}
          </button>
          {hero && (
            <button type="submit" className="search-field__submit" aria-label={dict.search.button}>
              <SearchIcon />
              <span className="search-field__submit-label">{dict.search.button}</span>
            </button>
          )}
        </div>
        {!hero && (
          <button type="submit" className="search-field__submit" aria-label={dict.search.button}>
            <SearchIcon />
            <span className="search-field__submit-label">{dict.search.button}</span>
          </button>
        )}
      </div>

      <div className="search-field__voice-bar">
        <span className="search-field__voice-label">{t.voice_lang}:</span>
        {(Object.keys(VOICE_LABEL) as VoiceLang[]).map((l) => (
          <button
            key={l}
            type="button"
            onMouseDown={keepFocus}
            onClick={() => setVoiceLang(l)}
            className={`search-field__chip${voiceLang === l ? " is-active" : ""}`}
            aria-pressed={voiceLang === l}
            disabled={busy}
          >
            {VOICE_LABEL[l]}
          </button>
        ))}
        {status && (
          <span className="search-field__listening" role="status">
            <span className="search-field__pulse" aria-hidden />
            {status}
          </span>
        )}
      </div>

      {voice === "transcribing" && <ElaajLoader size="sm" label={t.transcribing} />}

      {voiceMsg && (
        <p className="search-field__msg" role="alert">
          {voiceMsg}
        </p>
      )}

      {/* Portalled to <body>: an animated ancestor would otherwise become the
          containing block and pin the "fixed" dock mid-page. */}
      {kbOpen && createPortal(
        <div ref={dockRef} className="osk" role="group" aria-label={t.keyboard} onMouseDown={keepFocus}>
          <div className="osk__inner">
            <div className="osk__head">
              <div className="osk__tabs">
                {(["ur", "ar", "en"] as KeyboardLayout[]).map((l) => (
                  <button
                    key={l}
                    type="button"
                    onClick={() => setLayout(l)}
                    className={`search-field__chip${layout === l ? " is-active" : ""}`}
                    aria-pressed={layout === l}
                  >
                    {l === "ur" ? t.keyboard_urdu : l === "ar" ? t.keyboard_arabic : t.keyboard_english}
                  </button>
                ))}
              </div>
              <button type="button" className="search-field__chip" onClick={() => setKbOpen(false)}>
                {t.close} ✕
              </button>
            </div>

            <div className={`osk__grid osk__grid--${layout}`} dir={LAYOUT_DIR[layout]}>
              {LAYOUTS[layout].map((k) => (
                <button key={k} type="button" className="osk__key" onClick={() => insert(k)}>
                  {isMark(k) ? "◌" + k : k}
                </button>
              ))}
            </div>
            <div className="osk__fn" dir={LAYOUT_DIR[layout]}>
              <button type="button" className="osk__key osk__key--wide" onClick={() => insert(" ")}>
                {t.space}
              </button>
              <button type="button" className="osk__key osk__key--fn" onClick={backspace} aria-label={t.backspace}>
                ⌫
              </button>
              <button type="button" className="osk__key osk__key--fn" onClick={() => onChange("")}>
                {t.clear}
              </button>
              <button type="button" className="osk__key osk__key--go" onClick={runSubmit}>
                {dict.search.button}
              </button>
            </div>
          </div>
        </div>,
        document.body,
      )}
    </form>
  );
}

function SearchIcon() {
  return (
    <svg className="search-field__submit-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <circle cx="11" cy="11" r="6.5" />
      <path d="m20 20-4.2-4.2" />
    </svg>
  );
}

function MicIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <rect x="9" y="3" width="6" height="11" rx="3" />
      <path d="M5 11a7 7 0 0 0 14 0" />
      <path d="M12 18v3" />
    </svg>
  );
}

function KeyboardIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <rect x="2.5" y="6" width="19" height="12" rx="2" />
      <path d="M6.5 10h.01M10 10h.01M13.5 10h.01M17 10h.01M6.5 13.5h.01M17 13.5h.01M9.5 14h5" />
    </svg>
  );
}
