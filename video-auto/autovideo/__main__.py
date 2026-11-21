"""Dòng lệnh: python -m autovideo "chủ đề" [tuỳ chọn]."""
from __future__ import annotations

import argparse
import sys

from .config import Settings
from .pipeline import make_video
from .script import STYLES


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="autovideo",
        description="Tự động làm video ngắn dọc tiếng Việt từ A-Z: kịch bản, giọng đọc, hình, phụ đề, nhạc.",
    )
    p.add_argument("topic", nargs="?", default="", help="Chủ đề hoặc gợi ý nội dung")
    p.add_argument("--style", default="tai-chinh", choices=sorted(STYLES), help="Phong cách nội dung")
    p.add_argument("--duration", type=int, default=60, help="Thời lượng mục tiêu (giây)")
    p.add_argument("--tin-moi", action="store_true", help="Tự lấy tin mới nhất từ báo và chọn tin viral")
    p.add_argument("--script", help="Dùng kịch bản JSON có sẵn, bỏ qua bước Claude")
    p.add_argument("--batch", help="File .txt mỗi dòng một chủ đề, làm hàng loạt")
    p.add_argument("--so-luong", type=int, default=1, help="Số video làm liên tiếp khi dùng --tin-moi")
    p.add_argument("--visual", choices=["pexels", "ai", "card"], help="Nguồn hình (ghi đè .env)")
    p.add_argument("--voice", help="Giọng đọc, vd vi-VN-NamMinhNeural (ghi đè .env)")
    p.add_argument("--tts", choices=["edge", "espeak"], help="Bộ đọc (ghi đè .env)")
    args = p.parse_args(argv)

    s = Settings.load()
    if args.visual:
        s.visual_source = args.visual
    if args.voice:
        s.tts_voice = args.voice
    if args.tts:
        s.tts_engine = args.tts

    jobs: list[str] = []
    if args.batch:
        with open(args.batch, encoding="utf-8") as fh:
            jobs = [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]
    elif args.tin_moi:
        jobs = [args.topic] * max(1, args.so_luong)
    else:
        if not args.topic and not args.script:
            p.error("Cần nhập chủ đề, hoặc dùng --tin-moi, --script, --batch")
        jobs = [args.topic]

    failed = 0
    for n, topic in enumerate(jobs, 1):
        if len(jobs) > 1:
            print(f"\n=== Video {n}/{len(jobs)}: {topic or 'tin mới'} ===")
        try:
            extra = ""
            if args.tin_moi and n > 1:
                extra = f" (video thứ {n}: chọn tin KHÁC các video trước)"
            make_video(s, topic + extra if extra else topic, args.style, args.duration,
                       args.tin_moi, args.script)
        except Exception as exc:
            failed += 1
            print(f"LỖI: {exc}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
