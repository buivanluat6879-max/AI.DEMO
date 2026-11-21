"""Chạy trọn quy trình: kịch bản → giọng đọc → hình → phụ đề → video."""
from __future__ import annotations

import json
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path

from PIL import ImageFont

from . import news as news_mod
from .config import Settings
from .media import require_ffmpeg
from .render import final_render, scene_clip, thumbnail
from .script import generate_script, load_script
from .subtitles import build_ass
from .tts import synthesize
from .visuals import font_path, get_visual


def slugify(text: str, limit: int = 50) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:limit].strip("-") or "video"


def make_video(
    settings: Settings,
    topic: str = "",
    style: str = "tai-chinh",
    duration: int = 60,
    use_news: bool = False,
    script_file: str | None = None,
) -> Path:
    require_ffmpeg()
    t0 = time.time()

    print("1/5 Viết kịch bản...")
    if script_file:
        data = load_script(script_file)
    else:
        headlines = news_mod.fetch_headlines(style) if use_news else None
        if use_news and not headlines:
            raise RuntimeError("Không lấy được tin mới nào từ RSS. Kiểm tra mạng hoặc nhập chủ đề.")
        data = generate_script(settings, topic, style, duration, headlines)
    print(f"    {data['title']} ({len(data['scenes'])} cảnh)")

    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    outdir = settings.output_dir / f"{stamp}-{slugify(data['title'])}"
    work = outdir / "work"
    work.mkdir(parents=True, exist_ok=True)
    (outdir / "script.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print("2/5 Tạo giọng đọc...")
    audios, durs = [], []
    for i, scene in enumerate(data["scenes"]):
        wav = work / f"voice{i:02d}.wav"
        durs.append(synthesize(scene["voice"], wav, settings))
        audios.append(wav)
    print(f"    tổng {sum(durs):.1f} giây")

    print(f"3/5 Lấy hình ảnh ({settings.visual_source})...")
    used: set = set()
    visuals = []
    for i, scene in enumerate(data["scenes"]):
        v = get_visual(scene, i, work, settings, used)
        # Thẻ chữ không có highlight thì đã vẽ headline ở giữa, khỏi lặp lại phía trên
        scene["_card_shows_headline"] = v["card"] and not scene.get("highlight")
        visuals.append(v)

    print("4/5 Dựng từng cảnh...")
    clips = [scene_clip(v, d, i, work / f"clip{i:02d}.mp4", settings)
             for i, (v, d) in enumerate(zip(visuals, durs))]

    print("5/5 Ghép video, phụ đề, nhạc nền...")
    fp = font_path(settings)
    font_name = ImageFont.truetype(fp, 20).getname()[0]
    ass = build_ass(data["scenes"], durs, font_name, settings.brand, settings.width, settings.height)
    video = final_render(clips, audios, ass, fp, work, outdir / "video.mp4", settings)
    thumbnail(video, outdir / "thumbnail.jpg")

    tags = " ".join(data.get("hashtags", []))
    caption = f"{data['title']}\n\n{data.get('caption', '')}\n\n{tags}\n"
    if data.get("sources"):
        caption += "\nNguồn: " + ", ".join(data["sources"]) + "\n"
    (outdir / "caption.txt").write_text(caption, encoding="utf-8")

    print(f"Xong sau {time.time() - t0:.0f} giây: {video}")
    return video
