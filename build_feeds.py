"""Release queued pins into per-board RSS feeds once their publish time has passed.

Runs inside the site repository (GitHub Actions, hourly) and locally from site.py.
Reads feeds/queue.json, writes feeds/<board-slug>.xml. Pinterest auto-publish polls these feeds.
Standard library only.
"""
import datetime as dt
import json
import pathlib
from email.utils import format_datetime
from xml.sax.saxutils import escape

HERE = pathlib.Path(__file__).parent
FEEDS = HERE / "feeds"


def main():
    queue = json.loads((FEEDS / "queue.json").read_text(encoding="utf-8"))
    now = dt.datetime.now(dt.timezone.utc)
    for board in queue["boards"]:
        due = [i for i in queue["items"] if i["board_slug"] == board["slug"]
               and dt.datetime.fromisoformat(i["publish_at_utc"]) <= now]
        due = sorted(due, key=lambda i: i["publish_at_utc"], reverse=True)[:25]  # newest 25 is plenty for polling
        items = "".join(
            f"""
<item><title>{escape(i["title"])}</title><link>{escape(i["link"])}</link>
<description>{escape(i["description"])}</description>
<guid isPermaLink="false">{escape(i["id"])}</guid>
<pubDate>{format_datetime(dt.datetime.fromisoformat(i["publish_at_utc"]))}</pubDate>
<enclosure url="{escape(i["image"])}" type="image/png" length="{i["image_bytes"]}"/>
<media:content url="{escape(i["image"])}" medium="image" type="image/png"/></item>""" for i in due)
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/" xmlns:atom="http://www.w3.org/2005/Atom">
<channel><title>{escape(queue["brand"])}: {escape(board["name"])}</title><link>{escape(queue["site_url"])}</link>
<description>{escape(board["name"])} from {escape(queue["brand"])}</description><language>en</language>
<atom:link href="{escape(queue["site_url"])}feeds/{board["slug"]}.xml" rel="self" type="application/rss+xml"/>{items}
</channel></rss>
"""
        path = FEEDS / f"{board['slug']}.xml"
        if not path.exists() or path.read_text(encoding="utf-8") != xml:
            path.write_text(xml, encoding="utf-8")
            print(f"{path.name}: {len(due)} item(s)")


if __name__ == "__main__":
    main()
