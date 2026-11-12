"""Build the site into _site/.

    python build.py            build for publishing
    python build.py --drafts   also include posts marked draft: true
    python build.py --preview  write links as .../index.html so pages open from disk

Pages are Jinja templates in pages/. Posts are Markdown files in learn/<track>/.
Course details live in data/courses.yml and site settings in site.yml.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import os
import posixpath
import re
import shutil
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode
from mdit_py_plugins.anchors import anchors_plugin

ROOT = Path(__file__).parent
OUT = ROOT / "_site"
FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.S)

md = MarkdownIt("commonmark", {"typographer": False}).enable("table")
md.use(anchors_plugin, min_level=2, max_level=3, permalink=False)


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def split_front_matter(text: str) -> tuple[dict, str]:
    match = FRONT_MATTER.match(text)
    if not match:
        return {}, text
    return yaml.safe_load(match.group(1)) or {}, match.group(2)


def reading_minutes(text: str) -> int:
    return max(1, round(len(text.split()) / 220))


def external_links_new_tab(rendered: str) -> str:
    return re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" rel="noopener"', rendered)


def headings(markdown_text: str, level: str = "h2") -> list[str]:
    """Plain-text headings of one level, for the on-page contents list."""
    tree = SyntaxTreeNode(md.parse(markdown_text))
    found = []
    for node in tree.walk():
        if node.type == "heading" and node.tag == level:
            found.append("".join(c.content for c in node.children[0].children if c.content))
    return found


class Site:
    def __init__(self, drafts: bool, preview: bool):
        self.drafts = drafts
        self.preview = preview
        self.config = load_yaml(ROOT / "site.yml")
        self.courses = load_yaml(ROOT / "data" / "courses.yml")
        self.tracks = load_yaml(ROOT / "data" / "tracks.yml")
        self.pages: list[dict] = []  # everything written, for the sitemap
        self.env = Environment(
            loader=FileSystemLoader([ROOT / "pages", ROOT / "templates"]),
            undefined=StrictUndefined,
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.env.filters["markdown"] = lambda s: md.render(s or "")
        self.env.filters["inline_md"] = lambda s: md.renderInline(s or "")
        self.env.filters["longdate"] = lambda d: f"{d.day} {d.strftime('%B %Y')}"

    # ---- URLs -------------------------------------------------------------
    def rel(self, current: str, target: str) -> str:
        """A link from the page at `current` to the site path `target`."""
        if re.match(r"^(https?:|mailto:|tel:|#)", target):
            return target
        anchor = ""
        if "#" in target:
            target, anchor = target.split("#", 1)
            anchor = "#" + anchor
        current_dir = current if current.endswith("/") else posixpath.dirname(current) + "/"
        link = posixpath.relpath(target, current_dir)
        if target.endswith("/"):
            link = "./" if link == "." else link + "/"
            if self.preview:
                link += "index.html"
        return link + anchor

    def absolute(self, path: str) -> str:
        return self.config["url"].rstrip("/") + path

    # ---- Writing ----------------------------------------------------------
    def write(self, url_path: str, text: str, listed: bool = True, **meta):
        target = OUT / url_path.lstrip("/")
        if url_path.endswith("/"):
            target = target / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        if listed:
            self.pages.append({"path": url_path, **meta})

    def render(self, template: str, url_path: str, listed: bool = True, root_links: bool = False, **context):
        context.setdefault("lang", "en")
        context.setdefault("alternate", None)
        page = {"path": url_path, "url": self.absolute(url_path)}
        text = self.env.get_template(template).render(
            site=self.config,
            courses=self.courses,
            tracks=self.tracks,
            posts=self.posts,
            page=page,
            year=dt.date.today().year,
            url=(lambda target: target) if root_links else (lambda target: self.rel(url_path, target)),
            absolute=self.absolute,
            **context,
        )
        self.write(url_path, text, listed=listed)

    # ---- Content ----------------------------------------------------------
    def load_posts(self):
        posts = []
        track_ids = {t["id"] for t in self.tracks}
        for path in sorted((ROOT / "learn").glob("*/*.md")):
            meta, body = split_front_matter(path.read_text(encoding="utf-8"))
            if meta.get("draft") and not self.drafts:
                continue
            track = meta.get("track", path.parent.name)
            if track not in track_ids:
                raise SystemExit(f"{path}: unknown track '{track}'. Add it to data/tracks.yml.")
            slug = re.sub(r"^\d+-", "", path.stem)
            posts.append({
                **meta,
                "track": track,
                "slug": slug,
                "path": f"/learn/{track}/{slug}/",
                "body": body,
                "html": external_links_new_tab(md.render(body)),
                "minutes": reading_minutes(body),
                "contents": headings(body, "h2"),
                "order": meta.get("series_order", 999),
                "tags": meta.get("tags", []),
            })
        posts.sort(key=lambda p: (p["track"], p["order"], p["title"]))
        self.posts = posts
        for track in self.tracks:
            track["posts"] = [p for p in posts if p["track"] == track["id"]]
            track["path"] = f"/learn/{track['id']}/"
            for i, post in enumerate(track["posts"]):
                is_series = post["order"] != 999
                post["prev"] = track["posts"][i - 1] if is_series and i > 0 else None
                post["next"] = track["posts"][i + 1] if is_series and i + 1 < len(track["posts"]) else None
                post["track_name"] = track["name"]

    def build(self):
        if OUT.exists():
            shutil.rmtree(OUT)
        shutil.copytree(ROOT / "static", OUT)
        self.load_posts()

        # Plain pages: pages/<name>.html -> /<name>/, pages/index.html -> /
        for template in sorted((ROOT / "pages").glob("*.html")):
            name = template.stem
            if name == "404":
                # The 404 page is served at any address, so its links start from the site root.
                self.render("404.html", "/404.html", listed=False, root_links=True)
            else:
                self.render(template.name, "/" if name == "index" else f"/{name}/")

        # Courses, in English and Arabic
        for lang, prefix in (("en", "/courses/"), ("ar", "/ar/courses/")):
            other = "/ar/courses/" if lang == "en" else "/courses/"
            self.render("courses_index.html", prefix, lang=lang, alternate=other)
            for course in self.courses["courses"]:
                self.render(
                    "course.html", f"{prefix}{course['id']}/",
                    lang=lang, course=course, c=course[lang],
                    alternate=f"{other}{course['id']}/",
                )

        # Free learning
        self.render("learn_index.html", "/learn/")
        for track in self.tracks:
            self.render("track.html", track["path"], track=track)
        for post in self.posts:
            self.render("post.html", post["path"], post=post)

        self.write_sitemap()
        self.write_feed()
        (OUT / ".nojekyll").write_text("", encoding="utf-8")
        print(f"Built {len(self.pages)} pages and {len(self.posts)} posts into {OUT}")

    def write_sitemap(self):
        rows = "\n".join(
            f"  <url><loc>{html.escape(self.absolute(p['path']))}</loc></url>" for p in self.pages
        )
        self.write(
            "/sitemap.xml",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{rows}\n</urlset>\n",
            listed=False,
        )
        self.write(
            "/robots.txt",
            f"User-agent: *\nAllow: /\n\nSitemap: {self.absolute('/sitemap.xml')}\n",
            listed=False,
        )

    def write_feed(self):
        entries = []
        for post in sorted(self.posts, key=lambda p: (p["date"], -p["order"]), reverse=True):
            stamp = f"{post['date'].isoformat()}T00:00:00Z"
            entries.append(
                "  <entry>\n"
                f"    <title>{html.escape(post['title'])}</title>\n"
                f"    <link href=\"{html.escape(self.absolute(post['path']))}\"/>\n"
                f"    <id>{html.escape(self.absolute(post['path']))}</id>\n"
                f"    <updated>{stamp}</updated>\n"
                f"    <summary>{html.escape(post.get('description', ''))}</summary>\n"
                "  </entry>"
            )
        updated = max((p["date"] for p in self.posts), default=dt.date.today())
        self.write(
            "/feed.xml",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<feed xmlns="http://www.w3.org/2005/Atom">\n'
            f"  <title>{html.escape(self.config['name'])}: free learning</title>\n"
            f"  <link href=\"{self.absolute('/learn/')}\"/>\n"
            f"  <link rel=\"self\" href=\"{self.absolute('/feed.xml')}\"/>\n"
            f"  <id>{self.absolute('/')}</id>\n"
            f"  <updated>{updated.isoformat()}T00:00:00Z</updated>\n"
            f"  <author><name>{html.escape(self.config['name'])}</name></author>\n"
            + "\n".join(entries)
            + "\n</feed>\n",
            listed=False,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--drafts", action="store_true", help="include posts marked draft: true")
    parser.add_argument("--preview", action="store_true", help="write links as .../index.html")
    args = parser.parse_args()
    Site(drafts=args.drafts, preview=args.preview).build()
