"""Đọc cấu hình từ file .env và biến môi trường."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_dotenv(path: Path) -> None:
    """Nạp file .env đơn giản (KEY=VALUE), không ghi đè biến đã có."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), value)


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


@dataclass
class Settings:
    anthropic_api_key: str = ""
    claude_model: str = "claude-opus-5-5"

    tts_engine: str = "edge"  # edge | espeak
    tts_voice: str = "vi-VN-HoaiMyNeural"  # giọng nữ; giọng nam: vi-VN-NamMinhNeural
    tts_rate: str = "+8%"

    visual_source: str = "pexels"  # pexels | ai | card
    pexels_api_key: str = ""
    openai_api_key: str = ""
    openai_image_model: str = "gpt-image-1"

    brand: str = ""
    bgm_path: str = ""
    bgm_volume: float = 0.10
    font_file: str = ""
    output_dir: Path = field(default_factory=lambda: ROOT / "output")

    width: int = 1080
    height: int = 1920
    fps: int = 30

    @classmethod
    def load(cls) -> "Settings":
        load_dotenv(ROOT / ".env")
        s = cls()
        s.anthropic_api_key = _env("ANTHROPIC_API_KEY")
        s.claude_model = _env("CLAUDE_MODEL", s.claude_model)
        s.tts_engine = _env("TTS_ENGINE", s.tts_engine).lower()
        s.tts_voice = _env("TTS_VOICE", s.tts_voice)
        s.tts_rate = _env("TTS_RATE", s.tts_rate)
        s.visual_source = _env("VISUAL_SOURCE", s.visual_source).lower()
        s.pexels_api_key = _env("PEXELS_API_KEY")
        s.openai_api_key = _env("OPENAI_API_KEY")
        s.openai_image_model = _env("OPENAI_IMAGE_MODEL", s.openai_image_model)
        s.brand = _env("BRAND")
        s.bgm_path = _env("BGM_PATH")
        s.bgm_volume = float(_env("BGM_VOLUME", str(s.bgm_volume)))
        s.font_file = _env("FONT_FILE")
        out = _env("OUTPUT_DIR")
        if out:
            s.output_dir = Path(out).expanduser()
        return s
