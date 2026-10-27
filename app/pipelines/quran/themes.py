"""Ayah themes importer: QUL "Ayah theme" (SQLite) -> quran.ayah_themes.

The archive is downloaded from qul.tarteel.ai (Developer Resources > Ayah
theme, "Ayah by Ayah", English) into corpus/original/qul/topics/. Each row
names a theme for a range of ayat of one surah. Rows whose range does not
exist in the canonical text are refused.

Run:  python -m app.pipelines.quran.themes
"""

import io
import json
import sqlite3
import tempfile
import zipfile
from pathlib import Path

from sqlalchemy import delete, select

from app.models.quran import AyahTheme, Chapter
from app.pipelines.common.importer import BaseImporter

ARCHIVE_BASE = "qul/topics"
FILE_NAME = "ayah-themes.db.zip"
RESOURCE_PAGE = "https://qul.tarteel.ai/resources/ayah-theme"


class AyahThemesImporter(BaseImporter):
    source_key = "qul"
    source_name = "Quranic Universal Library (QUL), Tarteel AI"
    source_base_url = "https://qul.tarteel.ai"
    source_attribution = "Ayah themes, distributed by QUL"
    importer_name = "quran.ayah_themes"
    importer_version = "1.0.0"

    def __init__(self, session, corpus_root="corpus", files_dir: str | Path | None = None):
        super().__init__(session, corpus_root)
        self.files_dir = Path(files_dir) if files_dir else self.archive.original / ARCHIVE_BASE

    def execute(self) -> dict:
        verses_count = dict(self.session.execute(select(Chapter.id, Chapter.verses_count)).all())
        if len(verses_count) != 114:
            raise RuntimeError("Canonical Quran incomplete - run the Quran importer first.")
        content = (self.files_dir / FILE_NAME).read_bytes()
        artifact = self.archive_bytes(
            f"{ARCHIVE_BASE}/{FILE_NAME}",
            content,
            endpoint=RESOURCE_PAGE,
            request_params={"resource": "Ayah theme", "file": FILE_NAME, "format": "sqlite"},
        )
        rows = self._read_sqlite(content)

        bad = [
            r for r in rows
            if int(r[1]) not in verses_count
            or not 1 <= int(r[2]) <= int(r[3]) <= verses_count[int(r[1])]
        ]
        if bad:
            raise RuntimeError(f"{len(bad)} theme rows point outside the Quran, e.g. {bad[:3]}")

        self.session.execute(delete(AyahTheme))
        self.session.execute(
            AyahTheme.__table__.insert(),
            [
                {
                    "id": i,
                    "chapter_id": int(surah),
                    "ayah_from": int(a_from),
                    "ayah_to": int(a_to),
                    "theme": theme.strip(),
                    "keywords": (keywords or "").strip() or None,
                    "total_ayahs": int(total) if total not in (None, "") else None,
                    "raw_artifact_id": artifact.id,
                }
                for i, (theme, surah, a_from, a_to, keywords, total) in enumerate(rows, start=1)
            ],
        )
        self.run.notes = "QUL Ayah theme resource (English). Licence: as stated on the QUL resource page."
        return {
            "themes": len(rows),
            "surahs_covered": len({int(r[1]) for r in rows}),
            "ayat_covered": sum(int(r[3]) - int(r[2]) + 1 for r in rows),
        }

    @staticmethod
    def _read_sqlite(content: bytes) -> list[tuple]:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            members = [m for m in zf.namelist() if m.endswith(".db")]
            if len(members) != 1:
                raise RuntimeError(f"expected one .db in the archive, found {members}")
            db_bytes = zf.read(members[0])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.db"
            path.write_bytes(db_bytes)
            con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
            try:
                return con.execute(
                    "SELECT theme, surah_number, ayah_from, ayah_to, keywords, total_ayahs "
                    "FROM themes ORDER BY CAST(surah_number AS INTEGER), CAST(ayah_from AS INTEGER)"
                ).fetchall()
            finally:
                con.close()


def _main() -> None:
    from app.db.session import SessionLocal

    with SessionLocal() as session:
        run = AyahThemesImporter(session).run_import()
        print(json.dumps({"run_id": run.id, "status": run.status, "stats": run.stats}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _main()
