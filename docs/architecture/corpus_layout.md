# Corpus Storage Layout

The `corpus/` directory is the **immutable archive** of everything we fetch
from authenticated sources. Files under `corpus/original/` are written once
and never modified - they are the byte-perfect record of what the source
served us (Principle 1: Source Fidelity).

```
corpus/
├── original/                      # raw API responses, byte-for-byte, never edited
│   ├── quran/
│   │   └── quran_foundation/     # source: apis.quran.foundation (quran.com)
│   │       ├── chapters/          # chapters/chapter_001.json … chapter_114.json
│   │       ├── verses/            # verses/chapter_001_page_001.json … (Uthmani text)
│   │       ├── translations/      # translations/<resource_id>/chapter_001.json …
│   │       └── resources/         # lists of available translations/tafsirs
│   ├── hadith/
│   │   └── sunnah_com/           # source: api.sunnah.com
│   │       ├── collections.json   # the /collections listing
│   │       └── <collection>/      # bukhari, muslim, abudawud, tirmidhi, nasai, ibnmajah
│   │           ├── books.json
│   │           └── book_<n>/hadiths_page_<p>.json
│   └── tafsir/
│       └── quran_foundation/
│           └── <tafsir_slug>/     # en-tafisr-ibn-kathir, ur-tafseer-ibn-e-kaseer, …
│               └── <verse_key>.json  (e.g. 2_255.json)
├── manifests/                     # one manifest per import run (JSON)
│   └── <source_key>/<run_id>.json # every file fetched: path, sha256, bytes, endpoint,
│                                  # params, http status, fetched_at - the proof trail
├── normalized/                    # derived, regenerable data (never the source of truth)
├── cache/                         # transient HTTP caching, safe to delete
└── temp/                          # in-progress downloads before checksum + move
```

## Rules

1. **Write-once**: a file in `original/` is never overwritten. Re-imports that
   yield different bytes are written as a new import run and flagged for
   review - differences are surfaced, never silently applied.
2. **Checksum everything**: every file gets a SHA-256 recorded in the run
   manifest AND in `metadata.raw_artifacts` in PostgreSQL. File and database
   must always agree.
3. **Download discipline**: fetch to `temp/`, checksum, then atomically move
   into `original/`. No partial files ever land in the archive.
4. **Provenance chain**: every row in the `quran`, `hadith`, and `tafsir`
   schemas points to the raw artifact it was parsed from
   (`raw_artifact_id`), which points to its import run, which points to its
   source. Any datum in the platform can be traced back to the exact bytes
   the source served, and when.
5. **Write-through cache**: data missing from our corpus may be fetched from
   the source on user demand, but it is *always* persisted through the same
   pipeline (raw file + checksum + manifest + DB row) - next time it is
   served from our own corpus.
```
