# Bộ agent "Bản tin AI đột phá" hằng ngày

Mỗi agent chạy trong **một phiên riêng**, theo lịch riêng (giờ Việt Nam, Asia/Ho_Chi_Minh). Báo cáo cuối sẵn sàng trước 7:00.

| Giờ | Phiên | Việc | Kết quả |
| --- | --- | --- | --- |
| 6:03 | Agent Marketing | Nghiên cứu | `runs/YYYY-MM-DD/marketing.md` |
| 6:07 | Agent Kinh doanh & Bán hàng | Nghiên cứu | `runs/YYYY-MM-DD/sales.md` |
| 6:11 | Agent Doanh nghiệp | Nghiên cứu | `runs/YYYY-MM-DD/enterprise.md` |
| 6:41 | Agent Tổng hợp | Gộp 3 file, viết báo cáo, tạo poster + Word, gửi email | `report.md`, `poster.png`, `ban-tin-ai-YYYY-MM-DD.docx`, email tới mrbeanvn21@gmail.com |

Các phiên trao đổi qua thư mục chung của dự án: `/mnt/project-files/ai-daily-report/runs/YYYY-MM-DD/`.
Ngôn ngữ: tiếng Việt.

## Agent 1 – Marketing (6:03)
Phạm vi: content/video/hình ảnh bằng AI, GEO/AI search visibility, quảng cáo & cá nhân hoá, KOL/creator, martech, mạng xã hội.
Nguồn gợi ý: agilebrandguide.com (Yesterday's Marketing Technology & AI News), martech.org, adage.com, thông cáo báo chí (prnewswire, globenewswire, businesswire).

## Agent 2 – Kinh doanh & Bán hàng (6:07)
Phạm vi: AI sales agent/SDR, CRM + AI (Salesforce, HubSpot, plugin ChatGPT/Copilot/Claude), chăm sóc khách hàng, thương mại điện tử & agentic commerce, gọi vốn lớn của startup sales AI.
Nguồn gợi ý: unite.ai, techcrunch.com, venturebeat.com, blog chính thức OpenAI/Anthropic/Google/Microsoft/Salesforce, agilebrandguide.com.

## Agent 3 – Doanh nghiệp (6:11)
Phạm vi: nền tảng agent doanh nghiệp, quản trị/bảo mật agent, triển khai thực tế có số liệu, mô hình mới có ý nghĩa cho doanh nghiệp, hạ tầng.
Nguồn gợi ý: aiagentstore.ai/ai-agent-news/this-week, aiagentsdirectory.com/news, newsroom IBM/Microsoft/AWS/Google Cloud/Databricks, riorundown.substack.com.

### Quy tắc chung cho 3 agent nghiên cứu
- Chỉ lấy tin trong 48 giờ gần nhất (thứ Hai: 72 giờ). Không lặp lại tin đã có trong file hôm qua.
- Mở trang gốc trước khi lấy số liệu, không dựa vào đoạn trích kết quả tìm kiếm.
- Ghi tối đa 6 mục: tên ứng dụng, công ty, ngày, điểm đột phá cụ thể (có số liệu nếu có), URL nguồn, ghi chú nếu số liệu do công ty tự công bố. Thêm 1 câu nhận định xu hướng.
- Tiêu chí "đột phá": làm được việc mới, có số liệu kết quả thật, do công ty lớn tung ra, hoặc áp dụng ngay được cho doanh nghiệp Việt Nam.
- Không viết báo cáo cuối, không gửi email.

## Agent 4 – Tổng hợp & gửi (6:41)
1. Đọc 3 file kết quả của ngày. Thiếu file nào thì tự nghiên cứu nhanh mảng đó và ghi chú lại.
2. Gộp, loại trùng, chọn 4–6 mục mạnh nhất mỗi mảng.
3. **Tư vấn giải pháp cho từng mảng:** sau bảng tin của mỗi mảng, viết `### Tư vấn giải pháp: <Mảng> nên làm gì` gồm 3 giải pháp + 1 dòng "Chỉ số theo dõi". Mỗi giải pháp: `- **Tên việc ngắn (thời hạn):** làm gì, làm thế nào, công cụ gợi ý`, bám vào tin trong ngày và làm được cho doanh nghiệp Việt Nam vừa và nhỏ. Tên việc in đậm dưới 60 ký tự (poster dùng phần này).
4. Lưu `runs/YYYY-MM-DD/report.md` đúng khung (script poster đọc theo các tiêu đề này):
   - `# Bản tin AI đột phá – DD/MM/YYYY`
   - `## Tóm tắt nhanh`: 5 điểm nổi bật (danh sách đánh số)
   - `## 1. AI cho Marketing`: dòng "Nhận định: ..." + bảng Ứng dụng | Đơn vị | Ngày | Điểm đột phá + `### Tư vấn giải pháp`
   - `## 2. AI cho Kinh doanh & Bán hàng`, `## 3. AI cho Doanh nghiệp`: như trên
   - `## 4. Gợi ý hành động cho doanh nghiệp Việt Nam`: 3–4 gạch đầu dòng, dòng đầu là việc quan trọng nhất
   - `## Nguồn tham khảo`
   Có Claude Docs thì tạo thêm Doc cùng nội dung.
5. Chạy `python3 tools/make_outputs.py runs/YYYY-MM-DD` để tạo:
   - `poster.png`: poster tóm tắt (1080px ngang): 5 điểm nổi bật, các ứng dụng chính và ô "Nên làm gì" của từng mảng, việc nên làm ngay.
   - `ban-tin-ai-YYYY-MM-DD.docx`: báo cáo Word chi tiết, có phụ lục ghi chép đầy đủ của 3 agent nghiên cứu.
6. Gửi email tới mrbeanvn21@gmail.com: poster hiển thị trong thư, toàn bộ báo cáo kèm tư vấn giải pháp, đính kèm poster.png và file Word. Gửi thông báo đẩy về điện thoại.
7. Câu ngắn, có số liệu, không emoji. Ghi rõ khi số liệu do công ty tự công bố.

## Công cụ
- `tools/make_outputs.py`: đọc `report.md` (+ 3 file của agent), tạo poster PNG (HTML + Playwright) và file Word (pandoc + python-docx). Cần: pandoc, python-docx, Node + Playwright, font Inter.
- `tools/screenshot.js`: chụp HTML thành PNG.
- Bản chạy được của 2 file này nằm ở `/mnt/project-files/ai-daily-report/tools/`.
