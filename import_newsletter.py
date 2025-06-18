import re, pathlib, datetime, feedparser, requests, html2text, frontmatter
from dateutil import parser as dtparse

FEED_URL = "https://linkedinrss.cns.me/7039205695174397952"
DST      = pathlib.Path("_posts")
DST.mkdir(parents=True, exist_ok=True)              # stellt _posts/ sicher

# ---------------- Hilfsfunktionen ---------------- #

def slugify(text: str) -> str:
    """Erzeuge URL-freundlichen Slug."""
    text = text.lower()
    # Umlaute vereinfachen (ä→ae, ö→oe, ü→ue, ß→ss) – optional
    subs = {"ä":"ae", "ö":"oe", "ü":"ue", "ß":"ss"}
    for k, v in subs.items():
        text = text.replace(k, v)
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")

def get_publish_date(entry) -> datetime.datetime:
    """Robuster Versuch, ein Veröffentlichungs­datum zu finden."""
    if getattr(entry, "published_parsed", None):
        return datetime.datetime(*entry.published_parsed[:6], tzinfo=datetime.timezone.utc)

    for key in ("published", "updated", "created"):
        raw = getattr(entry, key, None)
        if raw:
            try:
                return dtparse.parse(raw)
            except (ValueError, TypeError):
                pass

    m = re.search(r"/(20\d{2})/(\d{2})/(\d{2})/", entry.link)
    if m:
        y, mth, d = map(int, m.groups())
        return datetime.datetime(y, mth, d, tzinfo=datetime.timezone.utc)

    # Fallback: jetzt-Zeit (UTC, tz-aware → keine Deprecation)
    return datetime.datetime.now(datetime.timezone.utc)

# --------------- Haupt­verarbeitung ------------- #

feed = feedparser.parse(FEED_URL)

for e in feed.entries:
    pub  = get_publish_date(e)
    slug = slugify(e.title)
    md_path = DST / f"{pub:%Y-%m-%d}-{slug}.md"
    if md_path.exists():
        continue                                     # schon importiert

    html = requests.get(e.link, timeout=15).text
    md_body = html2text.html2text(html)

    post = frontmatter.Post(
        md_body,
        layout="post",
        title=e.title,
        date=pub.isoformat(),
        linkedin_url=e.link,
        license="CC BY 4.0",
    )
    md_path.write_text(frontmatter.dumps(post), encoding="utf-8")
    print("written", md_path)
