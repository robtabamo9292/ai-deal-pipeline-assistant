from io import BytesIO
from textwrap import wrap

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 36
NAVY = HexColor("#172033")
SLATE = HexColor("#475467")
LIGHT = HexColor("#F2F4F7")
BORDER = HexColor("#D0D5DD")
WHITE = HexColor("#FFFFFF")


def _clean(value, fallback="Not provided"):
    text = " ".join(str(value or "").split())
    return text if text and text.lower() != "unknown" else fallback


def _draw_wrapped(
    pdf,
    text,
    x,
    y,
    width_chars=88,
    size=8,
    leading=10,
    max_lines=5,
):
    pdf.setFont("Helvetica", size)
    pdf.setFillColor(NAVY)
    lines = wrap(_clean(text), width=width_chars)[:max_lines]
    for line in lines:
        pdf.drawString(x, y, line)
        y -= leading
    return y


def _draw_list(pdf, items, x, y, width_chars=48, max_items=3):
    for item in (items or ["No evidence provided."])[:max_items]:
        lines = wrap(_clean(item), width=width_chars)[:3]
        pdf.setFillColor(NAVY)
        pdf.circle(x + 2, y + 2, 1.5, fill=1, stroke=0)
        for index, line in enumerate(lines):
            pdf.setFont("Helvetica", 7.5)
            pdf.drawString(x + 10, y - index * 9, line)
        y -= max(14, len(lines) * 9 + 3)
    return y


def memo_to_pdf_bytes(memo) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle(f"{_clean(memo.company_name)} Investment Brief")

    pdf.setFillColor(NAVY)
    pdf.rect(0, PAGE_HEIGHT - 88, PAGE_WIDTH, 88, fill=1, stroke=0)
    pdf.setFillColor(WHITE)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(MARGIN, PAGE_HEIGHT - 48, _clean(memo.company_name))
    pdf.setFont("Helvetica", 8)
    pdf.drawString(
        MARGIN,
        PAGE_HEIGHT - 66,
        f"{_clean(memo.sector)} | {_clean(memo.subsector)} | {_clean(memo.stage)}",
    )

    metrics = [
        ("EVIDENCE", f"{memo.opportunity_score}/100"),
        ("STATUS", _clean(memo.priority)),
        ("CONFIDENCE", f"{memo.confidence_score}/100"),
    ]
    x = 330
    for label, value in metrics:
        pdf.setFillColor(WHITE)
        pdf.roundRect(x, PAGE_HEIGHT - 70, 76, 44, 6, fill=1, stroke=0)
        pdf.setFillColor(SLATE)
        pdf.setFont("Helvetica-Bold", 6)
        pdf.drawCentredString(x + 38, PAGE_HEIGHT - 42, label)
        pdf.setFillColor(NAVY)
        pdf.setFont("Helvetica-Bold", 8 if label == "STATUS" else 11)
        pdf.drawCentredString(x + 38, PAGE_HEIGHT - 58, value[:20])
        x += 82

    y = PAGE_HEIGHT - 112
    pdf.setFillColor(NAVY)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(MARGIN, y, "Screening Summary")
    y = _draw_wrapped(
        pdf,
        memo.executive_summary,
        MARGIN,
        y - 14,
        width_chars=106,
        max_lines=5,
    )
    y -= 6
    pdf.setStrokeColor(BORDER)
    pdf.line(MARGIN, y, PAGE_WIDTH - MARGIN, y)
    y -= 18

    left_x = MARGIN
    right_x = 316
    pdf.setFont("Helvetica-Bold", 9)
    pdf.setFillColor(NAVY)
    pdf.drawString(left_x, y, "Investment Case")
    pdf.drawString(right_x, y, "Key Risks")
    left_y = _draw_list(pdf, memo.investment_thesis, left_x, y - 14, 52)
    right_y = _draw_list(pdf, memo.key_risks, right_x, y - 14, 52)
    y = min(left_y, right_y) - 8

    box_height = 72
    pdf.setFillColor(LIGHT)
    pdf.roundRect(
        MARGIN,
        y - box_height,
        PAGE_WIDTH - 2 * MARGIN,
        box_height,
        6,
        fill=1,
        stroke=0,
    )
    pdf.setFillColor(NAVY)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(MARGIN + 12, y - 16, "Evidence Snapshot")
    _draw_wrapped(
        pdf,
        memo.traction_and_customers,
        MARGIN + 12,
        y - 30,
        width_chars=104,
        max_lines=4,
    )
    y -= box_height + 18

    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(MARGIN, y, "Priority Diligence Questions")
    _draw_list(pdf, memo.diligence_questions, MARGIN, y - 14, 108, 4)

    pdf.setStrokeColor(BORDER)
    pdf.line(MARGIN, 46, PAGE_WIDTH - MARGIN, 46)
    pdf.setFillColor(SLATE)
    pdf.setFont("Helvetica", 6.5)
    footer = (
        f"Methodology: {_clean(memo.score_methodology)} | "
        f"Path: {_clean(memo.analysis_path)} | Model: {_clean(memo.model_name)} | "
        f"Prompt: {_clean(memo.prompt_version)} | Generated: {_clean(memo.generated_at)}"
    )
    pdf.drawString(MARGIN, 34, footer[:150])
    pdf.drawString(MARGIN, 23, _clean(memo.source_limitations)[:165])

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()
