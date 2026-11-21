"""Viết kịch bản video ngắn bằng Claude, trả về JSON có cấu trúc."""
from __future__ import annotations

import json

from .config import Settings

STYLES: dict[str, str] = {
    "tai-chinh": "chuyên gia tài chính cá nhân và đầu tư, giải thích dòng tiền, lãi suất, tỷ giá, vàng một cách dễ hiểu cho người đi làm",
    "chung-khoan": "chuyên gia chứng khoán, phân tích thị trường, nhóm ngành, dòng tiền khối ngoại, nhắc rủi ro rõ ràng, không hô mua bán",
    "bat-dong-san": "chuyên gia bất động sản, quy hoạch và hạ tầng, nói về giá, pháp lý, chu kỳ, cơ hội và rủi ro theo khu vực",
    "kinh-doanh": "người dẫn bản tin kinh doanh, kể chuyện doanh nghiệp, thương vụ, bài học kinh doanh ngắn gọn, có số liệu",
    "tin-tuc": "người dẫn bản tin kinh tế nhanh, trung lập, đi thẳng vào sự kiện và tác động tới túi tiền người xem",
}

SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Tiêu đề video, tối đa 70 ký tự, gây tò mò"},
        "scenes": {
            "type": "array",
            "description": "Các cảnh theo thứ tự. Cảnh 1 là câu hook 3 giây đầu.",
            "items": {
                "type": "object",
                "properties": {
                    "voice": {"type": "string", "description": "Lời đọc của cảnh, 1-2 câu, viết số và ký hiệu thành chữ để giọng đọc chuẩn"},
                    "headline": {"type": "string", "description": "Chữ lớn trên màn hình, tối đa 7 từ"},
                    "highlight": {"type": "string", "description": "Con số hoặc từ khoá nổi bật nhất của cảnh (vd '+15%', '2.000 tỷ'), để trống nếu không có"},
                    "visual_query": {"type": "string", "description": "2-4 từ khoá TIẾNG ANH để tìm video stock minh hoạ, cụ thể và dễ quay (vd 'city skyline night', 'counting money hands')"},
                    "image_prompt": {"type": "string", "description": "Prompt TIẾNG ANH để tạo ảnh AI dọc 9:16 minh hoạ cảnh, bối cảnh Việt Nam nếu phù hợp, không có chữ trong ảnh"},
                },
                "required": ["voice", "headline", "highlight", "visual_query", "image_prompt"],
                "additionalProperties": False,
            },
        },
        "caption": {"type": "string", "description": "Caption đăng TikTok/Reels/Shorts, 2-3 câu, có câu kêu gọi bình luận"},
        "hashtags": {"type": "array", "items": {"type": "string"}, "description": "5-8 hashtag không dấu, có dấu #"},
        "sources": {"type": "array", "items": {"type": "string"}, "description": "Link nguồn tin đã dùng (nếu có)"},
    },
    "required": ["title", "scenes", "caption", "hashtags", "sources"],
    "additionalProperties": False,
}

SYSTEM = """Bạn là biên kịch video ngắn dọc (TikTok, Reels, YouTube Shorts) tiếng Việt, chuyên tài chính, đầu tư, bất động sản, chứng khoán và tin kinh doanh.

Nguyên tắc:
- 3 giây đầu phải có hook mạnh: một con số gây sốc, một câu hỏi chạm nỗi đau, hoặc một nghịch lý.
- Mỗi cảnh 1-2 câu ngắn, giọng nói chuyện tự nhiên như người thật, xưng "mình" gọi người xem là "bạn".
- Có số liệu cụ thể. Chỉ dùng số liệu có trong tin được cung cấp hoặc kiến thức phổ biến chắc chắn; không bịa số.
- Lời đọc (voice) phải đọc được trơn tru: viết "15 phần trăm" thay vì "15%", "2 nghìn tỷ đồng" thay vì "2.000 tỷ", "đô la Mỹ" thay vì "USD" nếu dễ đọc hơn.
- Cảnh cuối là kết luận và kêu gọi theo dõi hoặc bình luận.
- Không đưa lời khuyên mua bán cụ thể; nhắc rủi ro khi nói về đầu tư.
- Không dùng emoji trong voice và headline."""


def _target_words(duration: int) -> int:
    # Giọng đọc tiếng Việt khoảng 3 âm tiết mỗi giây
    return int(duration * 3)


def generate_script(
    settings: Settings,
    topic: str,
    style: str = "tai-chinh",
    duration: int = 60,
    news: list[dict] | None = None,
) -> dict:
    if not settings.anthropic_api_key:
        raise RuntimeError(
            "Chưa có ANTHROPIC_API_KEY trong file .env. Lấy key tại https://console.anthropic.com "
            "hoặc dùng --script <file.json> để chạy với kịch bản có sẵn."
        )
    import anthropic

    persona = STYLES.get(style, STYLES["tin-tuc"])
    n_scenes = max(4, min(14, round(duration / 6)))
    parts = [
        f"Vai trò giọng đọc: {persona}.",
        f"Thời lượng mục tiêu: khoảng {duration} giây, tổng lời đọc khoảng {_target_words(duration)} chữ, chia thành {n_scenes} cảnh.",
    ]
    if topic:
        parts.append(f"Chủ đề / gợi ý nội dung: {topic}")
    if news:
        lines = [f"- {n['title']}: {n['summary']} ({n['link']})" for n in news]
        parts.append(
            "Tin mới nhất hôm nay:\n" + "\n".join(lines) +
            "\n\nChọn MỘT tin (hoặc một nhóm tin cùng chủ đề) có khả năng viral nhất với người Việt quan tâm tiền bạc, rồi viết kịch bản dựa trên tin đó. Ghi link vào sources."
        )
    parts.append("Viết kịch bản theo đúng schema JSON.")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.beta.messages.create(
        model=settings.claude_model,
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=SYSTEM,
        output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": "\n\n".join(parts)}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("Claude từ chối viết kịch bản cho chủ đề này. Hãy đổi chủ đề.")
    text = next((b.text for b in response.content if b.type == "text"), "")
    data = json.loads(text)
    data["style"] = style
    return data


def load_script(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    for scene in data["scenes"]:
        scene.setdefault("headline", "")
        scene.setdefault("highlight", "")
        scene.setdefault("visual_query", "")
        scene.setdefault("image_prompt", scene.get("visual_query", ""))
    data.setdefault("caption", data.get("title", ""))
    data.setdefault("hashtags", [])
    data.setdefault("sources", [])
    return data
