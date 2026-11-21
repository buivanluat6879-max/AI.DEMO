"""Tạo phụ đề ASS: chữ chạy theo giọng đọc + tiêu đề cảnh phía trên."""
from __future__ import annotations

import re

from .tts import PAUSE

MAX_WORDS = 5  # số chữ tối đa mỗi dòng phụ đề
NUM = re.compile(r"\d")


def _ts(sec: float) -> str:
    sec = max(0.0, sec)
    h = int(sec // 3600)
    m = int(sec % 3600 // 60)
    s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _esc(text: str) -> str:
    return text.replace("\\", "/").replace("{", "(").replace("}", ")").replace("\n", " ")


def _chunks(text: str) -> list[str]:
    """Chia lời đọc thành cụm ngắn, ưu tiên ngắt ở dấu câu."""
    out, cur = [], []
    for word in text.split():
        cur.append(word)
        if len(cur) >= MAX_WORDS or word[-1] in ".,!?;:":
            out.append(" ".join(cur))
            cur = []
    if cur:
        out.append(" ".join(cur))
    return out


def _colorize(chunk: str) -> str:
    """Tô vàng các từ có chữ số hoặc từ khoá tiền tệ."""
    words = []
    for w in _esc(chunk).split():
        if NUM.search(w) or w.lower().strip(".,!?") in {"tỷ", "triệu", "nghìn", "phần", "trăm", "%"}:
            words.append(r"{\c&H00D7FF&}" + w + r"{\c&HFFFFFF&}")
        else:
            words.append(w)
    return " ".join(words)


def build_ass(scenes: list[dict], durations: list[float], font_name: str, brand: str,
              width: int = 1080, height: int = 1920) -> str:
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{font_name},78,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,6,2,2,70,70,520,1
Style: Head,{font_name},66,&H00FFFFFF,&H00FFFFFF,&H00000000,&H3C1A0F00,-1,0,0,0,100,100,0,0,3,18,0,8,80,80,250,1
Style: Brand,{font_name},40,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,-1,0,0,0,100,100,1,0,3,10,0,7,50,50,90,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events: list[str] = []
    total = sum(durations)
    if brand:
        events.append(f"Dialogue: 2,{_ts(0)},{_ts(total)},Brand,,0,0,0,,{_esc(brand)}")

    t = 0.0
    for scene, dur in zip(scenes, durations):
        speak = max(0.5, dur - PAUSE)
        headline = scene.get("headline", "").strip()
        if headline and not scene.get("_card_shows_headline"):
            fade = r"{\fad(200,150)}"
            events.append(f"Dialogue: 1,{_ts(t)},{_ts(t + dur)},Head,,0,0,0,,{fade}{_esc(headline.upper())}")
        chunks = _chunks(scene["voice"])
        weights = [max(1, len(c)) for c in chunks]
        acc = t
        for chunk, w in zip(chunks, weights):
            seg = speak * w / sum(weights)
            pop = r"{\fscx92\fscy92\t(0,90,\fscx100\fscy100)}"
            events.append(f"Dialogue: 0,{_ts(acc)},{_ts(acc + seg)},Sub,,0,0,0,,{pop}{_colorize(chunk)}")
            acc += seg
        t += dur
    return header + "\n".join(events) + "\n"
