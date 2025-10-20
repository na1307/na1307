#!/usr/bin/env python3
"""
Fetches latest entries from an RSS/Atom feed and replaces the block between
<!-- BLOG-POSTS:START --> and <!-- BLOG-POSTS:END --> in the target README file.

Usage:
  python scripts/update_rss.py --feed-url FEED_URL --target README.ko.md --count 3 --summary-length 100
"""
import argparse
import feedparser
import html
import re
from datetime import datetime

MARKER_START = "<!-- BLOG-POSTS:START -->"
MARKER_END = "<!-- BLOG-POSTS:END -->"

def strip_tags(html_text):
    # very small sanitizer to remove HTML tags for summary
    text = re.sub(r'<[^>]+>', '', html_text or '')
    return html.unescape(text).strip()

def format_entry(entry, summary_length):
    title = entry.get('title', 'No title')
    link = entry.get('link', '')
    published = entry.get('published', '') or entry.get('updated', '')
    # Try to format published date as YYYY-MM-DD if possible
    try:
        parsed = entry.get('published_parsed') or entry.get('updated_parsed')
        if parsed:
            published_dt = datetime(*parsed[:6])
            published = published_dt.strftime('%Y-%m-%d')
    except Exception:
        pass

    summary = entry.get('summary', '') or entry.get('description', '')
    summary = strip_tags(summary)
    if summary_length and len(summary) > summary_length:
        summary = summary[:summary_length-3].rstrip() + "..."
    md = f"- [{title}]({link})"
    if published:
        md += f" — {published}"
    if summary:
        md += f"\n  \n  {summary}"
    return md

def build_posts_section(entries, count, summary_length):
    lines = []
    for e in entries[:count]:
        lines.append(format_entry(e, summary_length))
    if not lines:
        return "(No recent posts found.)"
    return "\n\n".join(lines)

def replace_block(content, new_block):
    start_idx = content.find(MARKER_START)
    end_idx = content.find(MARKER_END)
    if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
        raise RuntimeError("Markers not found or in wrong order in target file.")
    before = content[:start_idx + len(MARKER_START)]
    after = content[end_idx:]
    return before + "\n" + new_block + "\n" + after

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feed-url", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--count", type=int, default=3)
    ap.add_argument("--summary-length", type=int, default=100)
    args = ap.parse_args()

    feed = feedparser.parse(args.feed_url)
    if feed.bozo:
        print(f"Warning: problem parsing feed: {feed.bozo_exception}")

    posts_md = build_posts_section(feed.entries, args.count, args.summary_length)

    with open(args.target, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        new_content = replace_block(content, posts_md)
    except RuntimeError as e:
        print(f"Error: {e}")
        return 2

    if new_content != content:
        with open(args.target, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated {args.target} with latest {args.count} posts from {args.feed_url}")
    else:
        print("No changes needed.")

if __name__ == "__main__":
    main()
