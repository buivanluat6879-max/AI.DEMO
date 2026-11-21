"""Lấy tin mới từ RSS các báo kinh tế Việt Nam để làm nguyên liệu kịch bản."""
from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET

import requests

FEEDS: dict[str, list[str]] = {
    "tai-chinh": [
        "https://vnexpress.net/rss/kinh-doanh.rss",
        "https://cafef.vn/tai-chinh-ngan-hang.rss",
    ],
    "chung-khoan": [
        "https://cafef.vn/thi-truong-chung-khoan.rss",
        "https://vnexpress.net/rss/kinh-doanh.rss",
    ],
    "bat-dong-san": [
        "https://cafef.vn/bat-dong-san.rss",
        "https://vnexpress.net/rss/bat-dong-san.rss",
    ],
    "kinh-doanh": [
        "https://vnexpress.net/rss/kinh-doanh.rss",
        "https://cafef.vn/doanh-nghiep.rss",
    ],
}
FEEDS["tin-tuc"] = FEEDS["kinh-doanh"]

_TAG = re.compile(r"<[^>]+>")


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(_TAG.sub(" ", text or ""))).strip()


def fetch_headlines(style: str, limit: int = 15) -> list[dict]:
    """Trả về danh sách tin {title, summary, link, published} mới nhất."""
    items: list[dict] = []
    seen: set[str] = set()
    for url in FEEDS.get(style, FEEDS["kinh-doanh"]):
        try:
            resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0 autovideo"})
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
        except Exception as exc:  # mạng lỗi hoặc RSS hỏng: bỏ qua nguồn đó
            print(f"  [tin] bỏ qua {url}: {exc}")
            continue
        for node in root.iter("item"):
            title = _clean(node.findtext("title", ""))
            if not title or title in seen:
                continue
            seen.add(title)
            items.append(
                {
                    "title": title,
                    "summary": _clean(node.findtext("description", ""))[:400],
                    "link": (node.findtext("link") or "").strip(),
                    "published": (node.findtext("pubDate") or "").strip(),
                }
            )
    return items[:limit]
