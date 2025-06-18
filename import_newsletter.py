import feedparser, requests, html2text, frontmatter, pathlib, datetime, re

FEED = "https://linkedinrss.cns.me/7039205695174397952"
DST  = pathlib.Path("_posts")

def slugify(txt):
    return re.sub(r"[^a-z0-9]+", "-", txt.lower()).strip("-")

feed = feedparser.parse(FEED)
for entry in feed.entries:
    published = datetime.datetime(*entry.published_parsed[:6])
    title = entry.title
    slug  = slugify(title)
    mdfile = DST / f"{published:%Y-%m-%d}-{slug}.md"
    if mdfile.exists():                   # schon importiert
        continue

    html = requests.get(entry.link).text
    body_md = html2text.html2text(html)

    post = frontmatter.Post(
        body_md,
        **{
            "layout": "post",
            "title": title,
            "date": published.isoformat(),
            "linkedin_url": entry.link,
            "license": "CC BY 4.0"
        }
    )
    mdfile.write_text(frontmatter.dumps(post))
