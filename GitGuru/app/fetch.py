from pathlib import Path
import time
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
DOCUMENT_URLS = [
    "https://docs.github.com/en/get-started/start-your-journey/about-github-and-git",
    "https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository",
    "https://docs.github.com/en/get-started/using-git/about-git",
]

def fetch_documents():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    success = 0
    with requests.Session() as session:
        session.headers.update({"User-Agent": "GitGuru educational project"})
        for i, url in enumerate(DOCUMENT_URLS, 1):
            try:
                response = session.get(url, timeout=(5, 20))
                response.raise_for_status()
                if "html" not in response.headers.get("Content-Type", "").lower():
                    print(f"Skipped non-HTML response: {url}")
                    continue
                (RAW_DIR / f"github_docs_{i}.html").write_text(response.text, encoding="utf-8")
                print(f"Downloaded document {i}")
                success += 1
                time.sleep(0.5)
            except requests.Timeout:
                print(f"Timeout: {url}")
            except requests.HTTPError as exc:
                print(f"HTTP error: {exc}")
            except requests.RequestException as exc:
                print(f"Network error: {exc}")
            except OSError as exc:
                print(f"File error: {exc}")
    print(f"Downloaded {success} of {len(DOCUMENT_URLS)} documents.")

if __name__ == "__main__":
    fetch_documents()
