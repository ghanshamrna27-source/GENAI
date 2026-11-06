from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from app.models import Record

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUTPUT = ROOT / "data" / "records.json"

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "nav", "footer", "header"}:
            self.skip += 1
    def handle_endtag(self, tag):
        if tag in {"script", "style", "nav", "footer", "header"} and self.skip:
            self.skip -= 1
    def handle_data(self, data):
        if not self.skip and data.strip():
            self.parts.append(" ".join(data.split()))

def ingest_documents():
    files = sorted(RAW_DIR.glob("*.html"))
    if not files:
        print("No raw HTML found. Run: python -m app.fetch")
        return
    result = []
    for record_id, path in enumerate(files, 1):
        try:
            html = path.read_text(encoding="utf-8", errors="replace")
            parser = TextExtractor()
            parser.feed(html)
            text = unescape(" ".join(parser.parts))
            title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
            title = unescape(re.sub(r"<[^>]+>", "", title_match.group(1))).strip() if title_match else path.stem
            if not text:
                raise ValueError("Document contained no readable text")
            category = "GitHub" if any(w in (title + text[:1000]).lower() for w in ("github", "repository")) else "Git"
            keyword = re.sub(r"[^a-z0-9 ]", "", title.lower()).split()
            record = Record(record_id, category, title[:180], keyword[0] if keyword else "git",
                            f"What should a beginner know about {title}?", text[:700], "")
            result.append(record.to_dict())
            print(f"Processed {path.name}")
        except (OSError, ValueError, TypeError, KeyError) as exc:
            print(f"Skipped bad file {path.name}: {exc}")
    try:
        OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Saved {len(result)} record(s) to {OUTPUT}")
    except OSError as exc:
        print(f"Could not save output: {exc}")

if __name__ == "__main__":
    ingest_documents()
