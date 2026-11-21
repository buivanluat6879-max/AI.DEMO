"""Lấy hình minh hoạ cho từng cảnh: video stock Pexels, ảnh AI, hoặc thẻ chữ đồ hoạ."""
from __future__ import annotations

import base64
import random
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

from .config import Settings

FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]

# Bảng màu thẻ chữ: (nền trên, nền dưới, màu nhấn)
PALETTES = [
    ((10, 25, 47), (3, 8, 20), (255, 196, 0)),
    ((6, 40, 34), (2, 12, 10), (0, 230, 140)),
    ((45, 10, 20), (12, 3, 6), (255, 90, 90)),
    ((20, 20, 50), (5, 5, 15), (90, 180, 255)),
]


def font_path(settings: Settings) -> str:
    if settings.font_file and Path(settings.font_file).exists():
        return settings.font_file
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            return p
    raise RuntimeError("Không tìm thấy font hỗ trợ tiếng Việt. Đặt FONT_FILE trong .env")


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def make_card(scene: dict, idx: int, out: Path, settings: Settings) -> Path:
    W, H = settings.width, settings.height
    top, bottom, accent = PALETTES[idx % len(PALETTES)]
    strip = Image.new("RGB", (1, 256))
    for y in range(256):
        t = y / 255
        strip.putpixel((0, y), tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3)))
    img = strip.resize((W, H), Image.BILINEAR)
    d = ImageDraw.Draw(img)
    rnd = random.Random(idx)
    # Hoạ tiết lưới và đường biểu đồ cho cảm giác tài chính
    for gx in range(0, W, 90):
        d.line([(gx, 0), (gx, H)], fill=tuple(min(255, v + 10) for v in top), width=1)
    for gy in range(0, H, 90):
        d.line([(0, gy), (W, gy)], fill=tuple(min(255, v + 10) for v in top), width=1)
    pts, y = [], H * 0.78
    for x in range(-20, W + 60, 60):
        y += rnd.uniform(-70, 55)
        y = max(H * 0.62, min(H * 0.92, y))
        pts.append((x, y))
    d.line(pts, fill=accent, width=8, joint="curve")

    fp = font_path(settings)
    big_text = scene.get("highlight") or scene.get("headline") or ""
    size = 230 if len(big_text) <= 8 else 150 if len(big_text) <= 16 else 110
    font = ImageFont.truetype(fp, size)
    lines = _wrap(d, big_text, font, W - 140)
    line_h = int(size * 1.15)
    y0 = H * 0.42 - line_h * len(lines) / 2
    for i, line in enumerate(lines):
        w = d.textlength(line, font=font)
        d.text(((W - w) / 2, y0 + i * line_h), line, font=font, fill=accent,
               stroke_width=6, stroke_fill=(0, 0, 0))
    img.save(out, quality=92)
    return out


def _download(url: str, out: Path, headers: dict | None = None) -> Path:
    with requests.get(url, stream=True, timeout=60, headers=headers) as r:
        r.raise_for_status()
        with open(out, "wb") as fh:
            for chunk in r.iter_content(1 << 16):
                fh.write(chunk)
    return out


def _pexels(scene: dict, idx: int, workdir: Path, settings: Settings, used: set) -> tuple[str, Path] | None:
    query = scene.get("visual_query") or scene.get("headline")
    if not settings.pexels_api_key or not query:
        return None
    headers = {"Authorization": settings.pexels_api_key}
    r = requests.get(
        "https://api.pexels.com/videos/search",
        params={"query": query, "orientation": "portrait", "per_page": 15, "size": "medium"},
        headers=headers, timeout=20,
    )
    r.raise_for_status()
    for video in r.json().get("videos", []):
        if video["id"] in used or video.get("duration", 0) < 3:
            continue
        files = [f for f in video.get("video_files", [])
                 if f.get("height") and f.get("width") and f["height"] > f["width"] and f["height"] >= 1280]
        if not files:
            continue
        best = min(files, key=lambda f: abs(f["height"] - 1920))
        used.add(video["id"])
        return "video", _download(best["link"], workdir / f"scene{idx:02d}.mp4")
    r = requests.get(
        "https://api.pexels.com/v1/search",
        params={"query": query, "orientation": "portrait", "per_page": 15},
        headers=headers, timeout=20,
    )
    r.raise_for_status()
    for photo in r.json().get("photos", []):
        if photo["id"] in used:
            continue
        used.add(photo["id"])
        return "image", _download(photo["src"]["large2x"], workdir / f"scene{idx:02d}.jpg")
    return None


def _openai_image(scene: dict, idx: int, workdir: Path, settings: Settings) -> tuple[str, Path] | None:
    prompt = scene.get("image_prompt") or scene.get("visual_query")
    if not settings.openai_api_key or not prompt:
        return None
    r = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={"Authorization": f"Bearer {settings.openai_api_key}"},
        json={
            "model": settings.openai_image_model,
            "prompt": prompt + ". Vertical 9:16, photorealistic, cinematic lighting, no text, no watermark.",
            "size": "1024x1536",
            "n": 1,
        },
        timeout=180,
    )
    r.raise_for_status()
    item = r.json()["data"][0]
    out = workdir / f"scene{idx:02d}.png"
    if item.get("b64_json"):
        out.write_bytes(base64.b64decode(item["b64_json"]))
        return "image", out
    return "image", _download(item["url"], out)


def get_visual(scene: dict, idx: int, workdir: Path, settings: Settings, used: set) -> dict:
    """Trả về {type: video|image, path, card: bool}. Luôn có kết quả (rơi về thẻ chữ)."""
    source = settings.visual_source
    try:
        found = None
        if source == "pexels":
            found = _pexels(scene, idx, workdir, settings, used)
        elif source == "ai":
            found = _openai_image(scene, idx, workdir, settings)
        if found:
            return {"type": found[0], "path": found[1], "card": False}
    except requests.HTTPError as exc:
        code = exc.response.status_code if exc.response is not None else 0
        print(f"  [hình] cảnh {idx + 1}: lỗi {code} từ {source}; dùng thẻ chữ")
        if code in (401, 403):
            print("  [hình] Key không hợp lệ, các cảnh còn lại dùng thẻ chữ")
            settings.visual_source = "card"
    except requests.RequestException as exc:
        print(f"  [hình] Không kết nối được {source} ({type(exc).__name__}); các cảnh còn lại dùng thẻ chữ")
        settings.visual_source = "card"
    except Exception as exc:
        print(f"  [hình] cảnh {idx + 1}: {exc}; dùng thẻ chữ")
    path = make_card(scene, idx, workdir / f"scene{idx:02d}_card.jpg", settings)
    return {"type": "image", "path": path, "card": True}
