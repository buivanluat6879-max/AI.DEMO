# Hệ thống làm video tự động A-Z

Một lệnh ra một video ngắn dọc 9:16 (TikTok, Reels, YouTube Shorts) tiếng Việt, sẵn sàng đăng:

```
Tin mới / chủ đề ──► Kịch bản (Claude) ──► Giọng đọc (Edge TTS) ──► Hình ảnh (Pexels)
                                                                        │
         video.mp4 + caption.txt + thumbnail.jpg ◄── Ghép, phụ đề, nhạc (ffmpeg)
```

| Bước | Công cụ | Chi phí |
|---|---|---|
| Lấy tin mới | RSS VnExpress, CafeF | Miễn phí |
| Viết kịch bản, chọn tin viral | Claude (`claude-opus-5-5`) | Khoảng 1.000-2.000 đồng mỗi video |
| Giọng đọc | Microsoft Edge TTS, giọng HoaiMy (nữ) hoặc NamMinh (nam) | Miễn phí |
| Hình ảnh | Video/ảnh stock Pexels, tự rơi về thẻ chữ đồ hoạ nếu không có | Miễn phí |
| Phụ đề | Chữ chạy theo giọng, số liệu tô vàng, tiêu đề cảnh phía trên | Miễn phí |
| Dựng video | ffmpeg, 1080x1920, 30fps | Miễn phí |

## Cài đặt (một lần, trên Mac)

```bash
cd video-auto
bash setup.sh
```

Sau đó mở file `.env` và điền:
- `ANTHROPIC_API_KEY`: lấy ở https://console.anthropic.com
- `PEXELS_API_KEY`: đăng ký miễn phí ở https://www.pexels.com/api/new/
- `BRAND`: tên kênh của anh (hiện ở góc video), có thể để trống
- Nhạc nền: bỏ vài file mp3 không bản quyền vào thư mục `music/`

## Cách dùng

```bash
# Làm video từ một chủ đề
./lam-video.sh "Lãi suất tiết kiệm tháng 11 tăng hay giảm?"

# Tự đọc báo hôm nay, chọn tin viral nhất và làm video
./lam-video.sh --tin-moi --style chung-khoan

# Làm 3 video từ tin mới trong một lần
./lam-video.sh --tin-moi --style bat-dong-san --so-luong 3

# Làm hàng loạt từ file chủ đề (mỗi dòng một chủ đề)
./lam-video.sh --batch chu-de.txt --duration 45

# Dùng kịch bản tự viết hoặc đã sửa (bỏ qua Claude)
./lam-video.sh --script examples/lai-suat-tiet-kiem.json

# Đổi giọng nam, video 90 giây
./lam-video.sh "Giá vàng" --voice vi-VN-NamMinhNeural --duration 90
```

Phong cách (`--style`): `tai-chinh` (mặc định), `chung-khoan`, `bat-dong-san`, `kinh-doanh`, `tin-tuc`.
Nguồn hình (`--visual`): `pexels` (mặc định), `ai` (ảnh OpenAI, cần `OPENAI_API_KEY`), `card` (chỉ thẻ chữ, không cần key).

## Kết quả

Mỗi video nằm trong `output/<ngày-giờ>-<tiêu-đề>/`:
- `video.mp4`: video hoàn chỉnh để đăng
- `caption.txt`: tiêu đề, caption, hashtag, link nguồn
- `thumbnail.jpg`: ảnh bìa
- `script.json`: kịch bản. Sửa file này rồi chạy lại với `--script` để ra bản mới
- `work/`: file trung gian (có thể xoá)

## Chạy tự động mỗi ngày

Trên Mac, thêm vào `crontab -e` để 6:30 sáng mỗi ngày tự làm 2 video từ tin mới:

```
30 6 * * * cd "/Users/luatai/AI. DEMO/video-auto" && ./lam-video.sh --tin-moi --so-luong 2 >> output/log.txt 2>&1
```

## Khi có lỗi

- Không kết nối được giọng đọc Edge: hệ thống chuyển sang espeak-ng (giọng máy) nếu có cài, nên kiểm tra mạng rồi chạy lại.
- Pexels không có cảnh hợp hoặc key sai: cảnh đó tự dùng thẻ chữ đồ hoạ, video vẫn ra.
- Claude từ chối hoặc hết tiền trong tài khoản: lỗi sẽ in ra rõ, các video khác trong lô vẫn chạy tiếp.

## Bước tiếp theo dự kiến

- Tự đăng lên TikTok, YouTube Shorts, Facebook Reels
- Giọng đọc cao cấp (ElevenLabs, FPT.AI, Viettel AI)
- Video mô hình thôn quê 10 giây bằng Google Flow
