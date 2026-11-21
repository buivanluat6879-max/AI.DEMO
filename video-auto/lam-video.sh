#!/usr/bin/env bash
# Chạy hệ thống: ./lam-video.sh "chủ đề" [tuỳ chọn]   hoặc   ./lam-video.sh --tin-moi
cd "$(dirname "$0")"
exec .venv/bin/python -m autovideo "$@"
