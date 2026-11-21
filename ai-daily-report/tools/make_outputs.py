#!/usr/bin/env python3
"""Tạo poster PNG tóm tắt và file Word chi tiết từ bản tin AI hằng ngày.

Cách dùng:
  python3 make_outputs.py /mnt/project-files/ai-daily-report/runs/YYYY-MM-DD

Thư mục cần có report.md (báo cáo tổng hợp). Nếu có marketing.md, sales.md,
enterprise.md thì được đưa vào phụ lục của file Word.
Kết quả: poster.png và ban-tin-ai-YYYY-MM-DD.docx trong cùng thư mục.
Cần: pandoc, python-docx, node + playwright.
"""
import html, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def strip_md(s):
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    s = s.replace("**", "").replace("__", "")
    return s.strip()


def parse_report(text):
    data = {"title": "", "date": "", "highlights": [], "areas": [], "actions": []}
    m = re.search(r"^#\s+(.+)$", text, re.M)
    if m:
        data["title"] = strip_md(m.group(1))
        d = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", data["title"])
        data["date"] = d.group(1) if d else ""
    sections = re.split(r"^##\s+", text, flags=re.M)[1:]
    for sec in sections:
        head, _, body = sec.partition("\n")
        head = strip_md(head)
        if head.lower().startswith("tóm tắt"):
            data["highlights"] = [strip_md(x) for x in re.findall(r"^\s*\d+\.\s+(.+)$", body, re.M)][:5]
        elif re.match(r"^[123]\.", head):
            trend = ""
            tm = re.search(r"^Nhận định[^:]*:\s*(.+)$", body, re.M)
            if tm:
                trend = strip_md(tm.group(1))
            items = []
            for line in body.splitlines():
                if line.startswith("|") and not re.match(r"^\|\s*-", line):
                    cells = [c.strip() for c in line.strip().strip("|").split("|")]
                    if len(cells) >= 2 and cells[0].lower() not in ("ứng dụng",):
                        items.append({"name": strip_md(cells[0]), "org": strip_md(cells[1])})
            advice = []
            am = re.search(r"^###\s+Tư vấn giải pháp.*?$(.*?)(?=^###\s|\Z)", body, re.M | re.S)
            if am:
                for b in re.findall(r"^\s*[-*]\s+(.+)$", am.group(1), re.M):
                    bm = re.match(r"\*\*(.+?)\*\*", b)
                    label = (bm.group(1) if bm else strip_md(b)).rstrip(": ").strip()
                    if not label.lower().startswith("chỉ số"):
                        advice.append(label)
            data["areas"].append({"name": re.sub(r"^[123]\.\s*", "", head), "trend": trend, "items": items, "advice": advice})
        elif head.startswith("4.") or head.lower().startswith("gợi ý"):
            data["actions"] = [strip_md(x) for x in re.findall(r"^\s*[-*]\s+(.+)$", body, re.M)]
    return data


def first_sentence(s, limit=150):
    s = s.split(": ", 1)[0] if len(s) > limit and ": " in s[:60] else s
    if len(s) <= limit:
        return s
    cut = s[:limit].rsplit(" ", 1)[0]
    return cut + "…"


POSTER_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{width:1080px;font-family:'Inter',sans-serif;background:#0B1B33;color:#F2F5FA}
.wrap{padding:56px 60px 44px}
.kicker{font-size:20px;letter-spacing:3px;text-transform:uppercase;color:#7FB2FF;font-weight:600}
h1{font-size:62px;line-height:1.05;font-weight:800;margin-top:10px}
.date{font-size:28px;color:#C9D6EA;margin-top:10px;font-weight:500}
.hl{margin-top:34px;display:flex;flex-direction:column;gap:12px}
.card{display:flex;gap:18px;align-items:flex-start;background:#132A4D;border-radius:16px;padding:16px 20px}
.num{flex:0 0 44px;height:44px;border-radius:50%;background:#2F7BF6;color:#fff;font-weight:800;font-size:22px;display:flex;align-items:center;justify-content:center}
.card p{font-size:21px;line-height:1.38;color:#E8EEF8}
.areas{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:30px}
.area{border-radius:16px;padding:18px 18px 16px;background:#10233F;border-top:6px solid var(--c)}
.area h2{font-size:22px;font-weight:800;color:var(--c);line-height:1.2}
.area ul{list-style:none;margin-top:12px;display:flex;flex-direction:column;gap:10px}
.area li{font-size:17px;line-height:1.3;font-weight:600}
.area li span{display:block;font-weight:400;color:#9FB2CF;font-size:15px}
.adv{margin-top:14px;padding-top:12px;border-top:1px solid #2A4268}
.adv b{display:block;font-size:14px;letter-spacing:1.5px;text-transform:uppercase;color:var(--c)}
.adv ol{margin:8px 0 0 20px;display:flex;flex-direction:column;gap:6px}
.adv li{font-size:15.5px;line-height:1.3;color:#E8EEF8;font-weight:500}
.act{margin-top:24px;background:#F2B53A;color:#1A1300;border-radius:16px;padding:18px 22px}
.act b{display:block;font-size:17px;letter-spacing:2px;text-transform:uppercase}
.act p{font-size:20px;line-height:1.35;margin-top:6px;font-weight:500}
.foot{margin-top:22px;font-size:15px;color:#7F93B3;display:flex;justify-content:space-between}
"""

COLORS = ["#FF7A6B", "#3FD0B5", "#B79CFF"]


def build_poster_html(d):
    e = html.escape
    cards = "".join(
        f'<div class="card"><div class="num">{i+1}</div><p>{e(first_sentence(h, 165))}</p></div>'
        for i, h in enumerate(d["highlights"]))
    areas = ""
    for i, a in enumerate(d["areas"][:3]):
        lis = "".join(f'<li>{e(first_sentence(it["name"], 60))}<span>{e(first_sentence(it["org"], 40))}</span></li>'
                      for it in a["items"][:3])
        adv = "".join(f"<li>{e(first_sentence(x, 70))}</li>" for x in a.get("advice", [])[:3])
        adv_html = f'<div class="adv"><b>Nên làm gì</b><ol>{adv}</ol></div>' if adv else ""
        areas += f'<div class="area" style="--c:{COLORS[i % 3]}"><h2>{e(re.sub(r"^AI cho ", "", a["name"]))}</h2><ul>{lis}</ul>{adv_html}</div>'
    act = d["actions"][0] if d["actions"] else ""
    act_html = f'<div class="act"><b>Việc nên làm ngay</b><p>{e(first_sentence(act, 190))}</p></div>' if act else ""
    return f"""<!doctype html><html lang="vi"><head><meta charset="utf-8"><style>{POSTER_CSS}</style></head>
<body><div class="wrap">
<div class="kicker">Bản tin AI đột phá</div>
<h1>AI cho Marketing,<br>Kinh doanh &amp; Doanh nghiệp</h1>
<div class="date">{e(d["date"])} · 5 điểm nổi bật</div>
<div class="hl">{cards}</div>
<div class="areas">{areas}</div>
{act_html}
<div class="foot"><span>Chi tiết, số liệu và nguồn: xem file Word đính kèm</span><span>Số liệu phần lớn do công ty tự công bố</span></div>
</div></body></html>"""


def make_poster(d, out_png):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(build_poster_html(d))
        tmp = f.name
    subprocess.run(["node", os.path.join(HERE, "screenshot.js"), tmp, out_png, "1080", "1350"], check=True)
    os.unlink(tmp)


def make_docx(run_dir, report_text, d, out_docx):
    parts = [report_text.rstrip()]
    appendix = [("marketing.md", "Marketing"), ("sales.md", "Kinh doanh & Bán hàng"), ("enterprise.md", "Doanh nghiệp")]
    extra = []
    for fn, label in appendix:
        p = os.path.join(run_dir, fn)
        if os.path.exists(p):
            t = open(p, encoding="utf-8").read()
            t = re.sub(r"^#\s+.*\n", "", t, count=1)          # bỏ tiêu đề gốc
            t = re.sub(r"^(#{2,5})\s", lambda m: "#" + m.group(1) + " ", t, flags=re.M)  # hạ cấp heading
            extra.append(f"## Ghi chép của Agent {label}\n\n{t.strip()}")
    if extra:
        parts.append("# Phụ lục: ghi chép chi tiết của từng agent nghiên cứu\n\n" + "\n\n".join(extra))
    md = "\n\n".join(parts) + "\n"
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(md)
        tmp = f.name
    subprocess.run(["pandoc", "-f", "gfm", tmp, "-o", out_docx], check=True)
    os.unlink(tmp)
    style_docx(out_docx)


def style_docx(path):
    from docx import Document
    from docx.shared import Pt, RGBColor, Cm
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    doc = Document(path)
    for sec in doc.sections:
        sec.left_margin = sec.right_margin = Cm(2)
        sec.top_margin = sec.bottom_margin = Cm(2)
    def set_font(style, size=None, color=None, bold=None):
        style.font.name = "Arial"
        rpr = style.element.get_or_add_rPr()
        rfonts = rpr.find(qn("w:rFonts"))
        if rfonts is None:
            rfonts = OxmlElement("w:rFonts"); rpr.append(rfonts)
        for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
            rfonts.set(qn(a), "Arial")
        for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            if rfonts.get(qn(a)) is not None:
                del rfonts.attrib[qn(a)]
        if size: style.font.size = Pt(size)
        if color: style.font.color.rgb = RGBColor.from_string(color)
        if bold is not None: style.font.bold = bold
    by_name = {(st.name or "").lower(): st for st in doc.styles}
    for n in ("normal", "body text", "first paragraph", "compact"):
        if n in by_name: set_font(by_name[n], 10.5)
    for n, sz, col in (("title", 22, "0B1B33"), ("heading 1", 18, "0B1B33"), ("heading 2", 14, "1F5FD1"), ("heading 3", 12, "1F5FD1"), ("heading 4", 11, "333333")):
        if n in by_name: set_font(by_name[n], sz, col, True)
    if "hyperlink" in by_name:
        by_name["hyperlink"].font.color.rgb = RGBColor.from_string("1F5FD1")
    for t in doc.tables:
        tblPr = t._tbl.tblPr
        borders = OxmlElement("w:tblBorders")
        for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
            el = OxmlElement(f"w:{edge}")
            el.set(qn("w:val"), "single"); el.set(qn("w:sz"), "4"); el.set(qn("w:color"), "B8C4D6")
            borders.append(el)
        tblPr.append(borders)
        for ci, cell in enumerate(t.rows[0].cells):
            tcPr = cell._tc.get_or_add_tcPr()
            shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:fill"), "0B1B33")
            tcPr.append(shd)
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.color.rgb = RGBColor(255, 255, 255); r.font.bold = True
        widths = [Cm(3.8), Cm(3.0), Cm(2.2), Cm(8.0)] if len(t.columns) == 4 else None
        if widths:
            layout = OxmlElement("w:tblLayout"); layout.set(qn("w:type"), "fixed"); tblPr.append(layout)
            grid = t._tbl.tblGrid
            for gc, w in zip(grid.findall(qn("w:gridCol")), widths):
                gc.set(qn("w:w"), str(int(w.twips)))
        for row in t.rows:
            if widths:
                for cell, w in zip(row.cells, widths):
                    cell.width = w
            for cell in row.cells:
                for p in cell.paragraphs:
                    for r in p.runs:
                        r.font.size = Pt(9.5)
    doc.save(path)


def main():
    run_dir = sys.argv[1]
    report_path = os.path.join(run_dir, "report.md")
    text = open(report_path, encoding="utf-8").read()
    d = parse_report(text)
    day = os.path.basename(os.path.normpath(run_dir))
    png = os.path.join(run_dir, "poster.png")
    docx_path = os.path.join(run_dir, f"ban-tin-ai-{day}.docx")
    make_poster(d, png)
    make_docx(run_dir, text, d, docx_path)
    print(png)
    print(docx_path)


if __name__ == "__main__":
    main()
