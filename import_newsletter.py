# .github/scripts/import_newsletter.py 
import os, pathlib, datetime, re, feedparser, requests, html2text, frontmatter

FEED_URL = "https://linkedinrss.cns.me/7039205695174397952"  # RSS-Feed aller Editionen
DST      = pathlib.Path("_posts")
DST.mkdir(parents=True, exist_ok=True)                       # <— sorgt für Ordner

from dateutil import parser as dtparse   # <– neu

def get_publish_date(entry):
    """
    Liefert ein datetime-Objekt, egal welche Felder vorhanden sind.
    Fallback = aktuelle UTC-Zeit (damit Jekyll trotzdem baut).
    """
    # 1️⃣ 'published_parsed' (klassisch)
    if getattr(entry, "published_parsed", None):
        return datetime.datetime(*entry.published_parsed[:6])

    # 2️⃣ ISO-Strings wie entry.published / entry.updated
    for key in ("published", "updated", "created"):
        raw = getattr(entry, key, None)
        if raw:
            try:
                return dtparse.parse(raw)
            except (ValueError, TypeError):
                pass

    # 3️⃣ Versuche Datum aus der URL (…/2024/05/11/…)
    m = re.search(r"/(20\d{2})/(\d{2})/(\d{2})/", entry.link)
    if m:
        y, mth, d = map(int, m.groups())
        return datetime.datetime(y, mth, d)

    # 4️⃣ Ganz zum Schluss: jetzt-Zeit
    return datetime.datetime.utcnow()

# -------------------------------------------------------------------
feed = feedparser.parse(FEED_URL)
for e in feed.entries:
    pub = get_publish_date(e)
    slug = slugify(e.title)
    md_path = DST / f"{pub:%Y-%m-%d}-{slug}.md"
    if md_path.exists():
        continue

    # … Rest unverändert …
