from backend.app.scraping.reddit import parse_atom

FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <author><name>/u/someone</name></author>
    <category term="LocalLLaMA" label="r/LocalLLaMA"/>
    <content type="html">&lt;table&gt;&lt;tr&gt;&lt;td&gt;&lt;!-- SC_OFF --&gt;&lt;div class="md"&gt;&lt;p&gt;Hello local models&lt;/p&gt;&lt;/div&gt;&lt;!-- SC_ON --&gt; submitted by /u/someone&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;</content>
    <id>t3_abc123</id>
    <link href="https://www.reddit.com/r/LocalLLaMA/comments/abc123/x/"/>
    <updated>2026-11-10T14:40:00+00:00</updated>
    <published>2026-11-10T14:37:40+00:00</published>
    <title>A post title</title>
  </entry>
  <entry>
    <id>t3_nolink</id>
    <title></title>
  </entry>
</feed>"""


def test_parse_atom_maps_fields_and_skips_incomplete_entries():
    items = parse_atom(FEED)
    assert len(items) == 1
    it = items[0]
    assert it.source == "reddit"
    assert it.external_id == "abc123"
    assert it.title == "A post title"
    assert it.author == "someone"
    assert it.url.endswith("/comments/abc123/x/")
    assert it.extra == {"subreddit": "LocalLLaMA"}
    assert it.content == "Hello local models"
    assert it.published_at.isoformat() == "2026-11-10T14:37:40+00:00"
