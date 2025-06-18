#!/usr/bin/env python3
"""
Backfill aller LinkedIn-Newsletter-Ausgaben:
  1. Geht seitenweise durch das Archiv (?page=1,2,…)
  2. Sammelt eindeutige Artikel-Links
  3. Ruft jeden Artikel ab, wandelt HTML → Markdown
  4. Schreibt unter _posts/YYYY-MM-DD-slug.md
  ⚠︎  Nur einmal manuell ausführen (workflow_dispatch)
"""
import re, pathlib, datetime, time, requests, html2text, frontmatter
from bs4 import BeautifulSoup
from dateutil import parser as dtparse

NEWSLETTER_ID = "7039205695174397952"
ARCHIVE_URL   = f"https://www.linkedin.com/newsletters/{NEWSLETTER_ID}/"
HEADERS       = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}
DST           = pathlib.Path("_posts")
DST.mkdir(exist_ok=True)

# ---------- Helfer ---------- #
def slugify(text: str) -> str:
    text = text.lower()
    subs = {"ä":"ae", "ö":"oe", "ü":"ue", "ß":"ss"}
    for k, v in subs.items():
        text = text.replace(k, v)
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")

def get_publish_date(html: str, url: str) -> datetime.datetime:
    soup = BeautifulSoup(html, "lxml")
    # 1) meta og:article:published_time (ISO)
    meta = soup.find("meta", {"property": "og:article:published_time"})
    if meta and meta.get("content"):
        return dtparse.parse(meta["content"])
    # 2) time tag
    time_tag = soup.find("time")
    if time_tag and time_tag.get("datetime"):
        return dtparse.parse(time_tag["datetime"])
    # 3) Fallback aus URL /yyyy/mm/dd/
    m = re.search(r"/(20\d{2})/(\d{2})/(\d{2})/", url)
    if m:
        y, mth, d = map(int, m.groups())
        return datetime.datetime(y, mth, d)
    return datetime.datetime.now(datetime.timezone.utc)

# ---------- 1. Alle Artikel-Links einsammeln ---------- #
links = set()
page  = 1
while True:
    url = ARCHIVE_URL + f"?page={page}"
    r   = requests.get(url, headers=HEADERS, timeout=15)
    if r.status_code != 200:
        print("Archive fetch failed:", r.status_code, url)
        break
    soup = BeautifulSoup(r.text, "lxml")
    cards = soup.select("a[href*='/pulse/']")  # Newsletter-Cards verlinken auf /pulse/
    if not cards:
        break  # keine weiteren Seiten
    for a in cards:
        href = a.get("href").split("?")[0]
        if href.startswith("https://www.linkedin.com/pulse/"):
            links.add(href)
    print(f"Seite {page}: {len(cards)} Links gefunden")
    page += 1
    time.sleep(1)                               # Rate-Limit

print("Gesamt-Links:", len(links))

# ---------- 2. Jeden Artikel verarbeiten ---------- #
for url in sorted(links):
    html = requests.get(url, headers=HEADERS, timeout=15).text
    soup = BeautifulSoup(html, "lxml")
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else "Ohne Titel"
    pub   = get_publish_date(html, url)
    slug  = slugify(title)
    md    = DST / f"{pub:%Y-%m-%d}-{slug}.md"
    if md.exists():
        print("skip", md)
        continue

    body_md = html2text.html2text(html)
    post = frontmatter.Post(
        body_md,
        layout="post",
        title=title,
        date=pub.isoformat(),
        linkedin_url=url,
        license="CC BY 4.0",
    )
    md.write_text(frontmatter.dumps(post), encoding="utf-8")
    print("written", md)
    time.sleep(0.5)                             # höfliche Pause
