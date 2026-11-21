"""Chuyển lời đọc thành giọng nói tiếng Việt."""
from __future__ import annotations

import asyncio
import shutil
import time
from pathlib import Path

from .config import Settings
from .media import duration, run

PAUSE = 0.25  # giây nghỉ cuối mỗi cảnh


def _edge(text: str, out: Path, settings: Settings) -> None:
    import edge_tts

    async def go() -> None:
        await edge_tts.Communicate(text, settings.tts_voice, rate=settings.tts_rate).save(str(out))

    last: Exception | None = None
    for attempt in range(3):
        try:
            asyncio.run(go())
            if out.exists() and out.stat().st_size > 0:
                return
        except Exception as exc:
            last = exc
            time.sleep(1 + attempt)
    raise RuntimeError(f"edge-tts lỗi: {last}")


def _espeak(text: str, out: Path) -> None:
    exe = shutil.which("espeak-ng") or shutil.which("espeak")
    if not exe:
        raise RuntimeError("Không có espeak-ng để đọc dự phòng")
    run([exe, "-v", "vi", "-s", "160", "-w", str(out), text])


def synthesize(text: str, out_wav: Path, settings: Settings) -> float:
    """Tạo file WAV cho một cảnh, trả về thời lượng (giây) đã gồm khoảng nghỉ."""
    raw = out_wav.with_suffix(".raw.mp3" if settings.tts_engine == "edge" else ".raw.wav")
    if settings.tts_engine == "edge":
        try:
            _edge(text, raw, settings)
        except Exception as exc:
            print(f"  [giọng] {exc}\n  [giọng] Chuyển sang espeak-ng (giọng máy, chỉ để dự phòng) cho phần còn lại")
            settings.tts_engine = "espeak"
            raw = out_wav.with_suffix(".raw.wav")
            _espeak(text, raw)
    else:
        _espeak(text, raw)
    run([
        "ffmpeg", "-y", "-i", str(raw),
        "-af", f"apad=pad_dur={PAUSE}", "-ar", "44100", "-ac", "2", str(out_wav),
    ])
    return duration(out_wav)
