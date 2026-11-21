#!/usr/bin/env bash
# Cài đặt một lần trên Mac: bash setup.sh
set -e
cd "$(dirname "$0")"
if ! command -v ffmpeg >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    brew install ffmpeg
  else
    echo "Cần cài Homebrew trước: https://brew.sh rồi chạy lại." && exit 1
  fi
fi
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
[ -f .env ] || cp .env.example .env
echo ""
echo "Xong. Mở file .env điền ANTHROPIC_API_KEY và PEXELS_API_KEY, rồi chạy:"
echo "  ./lam-video.sh \"Lãi suất tiết kiệm tháng này\""
