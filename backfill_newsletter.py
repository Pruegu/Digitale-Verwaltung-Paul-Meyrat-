import re, time, pathlib, datetime, requests, html2text, frontmatter, backoff
from bs4 import BeautifulSoup
from dateutil import parser as dtparse

NEWSLETTER_ID = "7039205695174397952"
ARCHIVE_URL   = f"https://www.linkedin.com/newsletters/{NEWSLETTER_ID}/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/126.0",
    "Accept-Language": "en-US,en;q=0.9",
}
DST = pathlib.Path("_posts"); DST.mkdir(exist_ok=True)

def slugify(txt):
    return re.sub(r"[^a-z0-9]+", "-", txt.lower()).strip("-")

@backoff.on_exception(backoff.expo,
                      (requests.exceptions.RequestException,),
                      max_tries=5, jitter=None)
def get(url, **kw):
    kw.setdefault("headers", HEADERS)
    kw.setdefault("timeout", 20)
    r = requests.get(url, **kw)
    # LinkedIn Bot-Block liefert 999 – retry nach Delay
    if r.status_code == 999:
        raise requests.exceptions.HTTPError("LinkedIn anti-bot (999)")
    r.raise_for_status()
    return r

# ---------- 1) Alle Archivseiten durchgehen ---------- #
links, page = set(), 1
while True:
    arch = get(ARCHIVE_URL + f"?page={page}")
    soup = BeautifulSoup(arch.text, "lxml")
    cards = soup.select("a[href*='/pulse/']")
    if not cards:
        break
    for a in cards:
        href = a["href"].split("?")[0]
        if "/pulse/" in href:
            links.add(href)
    page += 1
    time.sleep(0.7)                     # kleiner Delay

print(f"Gefundene Artikel-Links: {len(links)}")

# ---------- 2) Einzelartikel verarbeiten ------------- #
def extract_date(html, url):
    soup = BeautifulSoup(html, "lxml")
    m = soup.find("meta", property="og:article:published_time")
    if m: return dtparse.parse(m["content"])
    t = soup.find("time")
    if t and t.get("datetime"): return dtparse.parse(t["datetime"])
    m = re.search(r"/(20\d{2})/(\d{2})/(\d{2})/", url)
    if m: return datetime.datetime(int(m[1]), int(m[2]), int(m[3]))
    return datetime.datetime.now(datetime.timezone.utc)

for url in sorted(links):
    try:
        html = get(url).text
    except Exception as e:
        print("❌  skip", url, "-", e)
        continue

    soup = BeautifulSoup(html, "lxml")
    title = soup.find("h1").get_text(" ", strip=True)
    pub   = extract_date(html, url)
    mdpth = DST / f"{pub:%Y-%m-%d}-{slugify(title)}.md"
    if mdpth.exists(): continue

    md_body = html2text.html2text(html)
    post = frontmatter.Post(
        md_body,
        layout="post",
        title=title,
        date=pub.isoformat(),
        linkedin_url=url,
        license="CC BY 4.0",
    )
    mdpth.write_text(frontmatter.dumps(post), encoding="utf-8")
    print("✔  written", mdpth)
    time.sleep(0.5)
