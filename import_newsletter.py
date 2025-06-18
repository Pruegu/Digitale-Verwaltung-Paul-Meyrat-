# .github/scripts/import_newsletter.py 
import os, pathlib, datetime, re, feedparser, requests, html2text, frontmatter

FEED_URL = "https://linkedinrss.cns.me/7039205695174397952"  # RSS-Feed aller Editionen
DST      = pathlib.Path("_posts")
DST.mkdir(parents=True, exist_ok=True)                       # <— sorgt für Ordner

def slug(txt):
    return re.sub(r"[^a-z0-9]+", "-", txt.lower()).strip("-")

feed = feedparser.parse(FEED_URL)
for e in feed.entries:
    pub = datetime.datetime(*e.published_parsed[:6])
    name = DST / f"{pub:%Y-%m-%d}-{slug(e.title)}.md"
    if name.exists():
        continue                                             # schon importiert

    md_body = html2text.html2text(requests.get(e.link).text)
    post = frontmatter.Post(
        md_body,
        layout="post",
        title=e.title,
        date=pub.isoformat(),
        linkedin_url=e.link,
        license="CC BY 4.0",
    )
    name.write_text(frontmatter.dumps(post), encoding="utf-8")
