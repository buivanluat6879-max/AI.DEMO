"""Dựng video dọc 9:16 bằng ffmpeg."""
from __future__ import annotations

import random
import shutil
from pathlib import Path

from .config import Settings
from .media import run

ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]


def scene_clip(visual: dict, dur: float, idx: int, out: Path, s: Settings) -> Path:
    W, H, fps = s.width, s.height, s.fps
    if visual["type"] == "video":
        vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={fps},setsar=1"
        run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(visual["path"]), "-t", f"{dur:.3f}",
             "-vf", vf, "-an", *ENC, str(out)])
        return out
    frames = max(1, int(round(dur * fps)))
    # Hiệu ứng Ken Burns: phóng to dần, hướng trôi thay đổi theo cảnh
    zoom_in = idx % 2 == 0
    z = "min(1+0.10*on/{n},1.10)".format(n=frames) if zoom_in else "max(1.10-0.10*on/{n},1.0)".format(n=frames)
    dx = random.Random(idx).choice(["iw/2-(iw/zoom/2)", "(iw-iw/zoom)*on/{n}".format(n=frames)])
    vf = (
        f"scale={W * 2}:{H * 2}:force_original_aspect_ratio=increase,crop={W * 2}:{H * 2},"
        f"zoompan=z='{z}':x='{dx}':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={fps},setsar=1"
    )
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(visual["path"]), "-frames:v", str(frames),
         "-vf", vf, *ENC, str(out)])
    return out


def _concat(files: list[Path], out: Path, workdir: Path, extra: list[str]) -> Path:
    lst = workdir / f"{out.stem}_list.txt"
    lst.write_text("".join(f"file '{f.name}'\n" for f in files), encoding="utf-8")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst.name, *extra, out.name], cwd=workdir)
    return out


def _pick_bgm(s: Settings) -> Path | None:
    if not s.bgm_path:
        return None
    p = Path(s.bgm_path).expanduser()
    if p.is_dir():
        tracks = [t for t in p.iterdir() if t.suffix.lower() in {".mp3", ".m4a", ".wav", ".aac"}]
        return random.choice(tracks) if tracks else None
    return p if p.exists() else None


def final_render(clips: list[Path], audios: list[Path], ass_text: str, font_file: str,
                 workdir: Path, out: Path, s: Settings) -> Path:
    video = _concat(clips, workdir / "video_raw.mp4", workdir, ["-c", "copy"])
    voice = _concat(audios, workdir / "voice.wav", workdir, ["-c", "copy"])

    fonts = workdir / "fonts"
    fonts.mkdir(exist_ok=True)
    shutil.copy(font_file, fonts / Path(font_file).name)
    (workdir / "subs.ass").write_text(ass_text, encoding="utf-8")

    cmd = ["ffmpeg", "-y", "-i", video.name, "-i", voice.name]
    bgm = _pick_bgm(s)
    if bgm:
        cmd += ["-stream_loop", "-1", "-i", str(bgm.resolve())]
        fc = (
            "[0:v]ass=subs.ass:fontsdir=fonts[v];"
            f"[2:a]volume={s.bgm_volume},afade=t=in:d=1[b];"
            "[1:a][b]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]"
        )
    else:
        fc = "[0:v]ass=subs.ass:fontsdir=fonts[v];[1:a]anull[a]"
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", str(out.resolve())]
    run(cmd, cwd=workdir)
    return out


def thumbnail(video: Path, out: Path) -> Path:
    run(["ffmpeg", "-y", "-ss", "0.8", "-i", str(video), "-frames:v", "1", "-q:v", "2", str(out)])
    return out
