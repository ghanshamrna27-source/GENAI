# GitGuru — Day 01 to Day 03

## Project card
- **Product:** GitGuru
- **User:** Students, beginners, and developers learning Git and GitHub.
- **Problem:** Beginners struggle with commands, repositories, commits, branches, merging, and troubleshooting.
- **Data source:** Official Git and GitHub documentation. Day 03 fetches public GitHub Docs pages.

## Setup (Windows PowerShell)
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Day 01
```powershell
python day01_intro.py
python day01_menu.py
```

## Day 02
```powershell
python main.py
```
The CLI lists records, searches keywords, counts categories, and finds records by ID.

## Day 03
Download three public documentation pages:
```powershell
python -m app.fetch
```
Convert the downloaded HTML into `data/records.json`:
```powershell
python -m app.ingest
```
Run the CLI:
```powershell
python main.py
```

## Record fields
`id`, `category`, `title`, `keyword`, `question`, `answer`, `source_url`.

The sample records make GitGuru usable before fetching. Day 03 needs an internet connection. Respect source-site terms and rate limits.
