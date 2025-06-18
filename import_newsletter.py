# import_newsletter.py
import pathlib, datetime, re, feedparser, requests, html2text, frontmatter
from dateutil import parser as dtparse

FEED_URL = "https://linkedinrss.cns.me/7039205695174397952"
DST = pathlib.Path("_posts")
DST.mkdir(parents=True, exist_ok=True)            # legt _posts/ an

# ---------- Helfer ---------- #
def slugify(text: str) -> str:
    text = text.lower()
    subs = {"ä":"ae", "ö":"oe", "ü":"ue", "ß":"ss"}
    for k, v in subs.items():
        text = text.replace(k, v)
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")

def get_date(entry) -> datetime.datetime:
    if getattr(entry, "published_parsed", None):
        return datetime.datetime(*entry.published_parsed[:6], tzinfo=datetime.timezone.utc)
    for k in ("published", "updated", "created"):
        raw = getattr(entry, k, None)
        if raw:
            try:
                return dtparse.parse(raw)
            except Exception:
                pass
    m = re.search(r"/(20\d{2})/(\d{2})/(\d{2})/", entry.link)
    if m:
        y, mth, d = map(int, m.groups())
        return datetime.datetime(y, mth, d, tzinfo=datetime.timezone.utc)
    return datetime.datetime.now(datetime.timezone.utc)

# ---------- Verarbeitung ---------- #
feed = feedparser.parse(FEED_URL)
for e in feed.entries:
    pub  = get_date(e)
    slug = slugify(e.title)
    md   = DST / f"{pub:%Y-%m-%d}-{slug}.md"
    if md.exists():
        continue

    html = requests.get(e.link, timeout=15).text
    body = html2text.html2text(html)

    post = frontmatter.Post(
        body,
        layout="post",
        title=e.title,
        date=pub.isoformat(),
        linkedin_url=e.link,
        license="CC BY 4.0",
    )
    md.write_text(frontmatter.dumps(post), encoding="utf-8")
    print("written", md)
