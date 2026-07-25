from __future__ import annotations

from io import BytesIO
from typing import Any, Iterable

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN_X = 36
TOP_MARGIN = 36
CONTENT_WIDTH = PAGE_WIDTH - (2 * MARGIN_X)

NAVY = HexColor("#0B1530")
BLUE = HexColor("#4F6BFF")
LIGHT_BLUE = HexColor("#EEF2FF")
TEXT = HexColor("#172033")
MUTED = HexColor("#61708A")
BORDER = HexColor("#D8DFEB")
GREEN = HexColor("#147D4A")
AMBER = HexColor("#9A6700")
RED = HexColor("#A53030")
WHITE = HexColor("#FFFFFF")


def _clean(value: object, fallback: str = "Not provided") -> str:
    text = str(value or "").strip()
    if not text or text.lower() in {"unknown", "none", "n/a", "not provided"}:
        return fallback
    return " ".join(text.split())


def _clip_at_word(text: str, max_chars: int) -> str:
    """Trim at a word boundary and never cut a word in half."""
    text = _clean(text)
    if len(text) <= max_chars:
        return text
    shortened = text[: max_chars + 1].rsplit(" ", 1)[0]
    if not shortened:
        shortened = text[:max_chars]
    return shortened.rstrip(".,;: ") + "..."


def _unique_items(
    items: Iterable[object],
    limit: int = 3,
    max_chars: int = 145,
) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for item in items or []:
        text = _clean(item, "")
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(_clip_at_word(text, max_chars))
        if len(output) >= limit:
            break
    return output


def _fit_font_size(
    text: str,
    font_name: str,
    max_size: float,
    min_size: float,
    max_width: float,
) -> float:
    """Reduce font size until the full string fits in the available width."""
    size = max_size
    while size > min_size and stringWidth(text, font_name, size) > max_width:
        size -= 0.25
    return max(size, min_size)


def _split_long_word(
    word: str,
    font_name: str,
    font_size: float,
    max_width: float,
) -> list[str]:
    chunks: list[str] = []
    current = ""
    for char in word:
        candidate = current + char
        if current and stringWidth(candidate, font_name, font_size) > max_width:
            chunks.append(current)
            current = char
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def _wrap_lines(
    text: str,
    font_name: str,
    font_size: float,
    max_width: float,
) -> list[str]:
    raw_words = _clean(text).split()
    words: list[str] = []
    for word in raw_words:
        if stringWidth(word, font_name, font_size) > max_width:
            words.extend(_split_long_word(word, font_name, font_size, max_width))
        else:
            words.append(word)

    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join(current + [word])
        if stringWidth(candidate, font_name, font_size) <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def _truncate_lines(
    lines: list[str],
    max_lines: int,
    font_name: str,
    font_size: float,
    max_width: float,
) -> list[str]:
    if len(lines) <= max_lines:
        return lines

    visible = lines[:max_lines]
    last = visible[-1]
    while last and stringWidth(
        last.rstrip(".,;: ") + "...",
        font_name,
        font_size,
    ) > max_width:
        if " " in last:
            last = last.rsplit(" ", 1)[0]
        else:
            last = last[:-1]
    visible[-1] = last.rstrip(".,;: ") + "..."
    return visible


def _draw_wrapped(
    pdf: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    width: float,
    font_name: str = "Helvetica",
    font_size: float = 8.6,
    leading: float = 11,
    max_lines: int = 4,
    color=TEXT,
) -> float:
    lines = _wrap_lines(text, font_name, font_size, width)
    lines = _truncate_lines(lines, max_lines, font_name, font_size, width)

    pdf.setFillColor(color)
    pdf.setFont(font_name, font_size)
    for line in lines:
        pdf.drawString(x, y, line)
        y -= leading
    return y


def _draw_bullets(
    pdf: canvas.Canvas,
    items: list[str],
    x: float,
    y: float,
    width: float,
    max_items: int = 3,
    max_lines_each: int = 2,
) -> float:
    if not items:
        items = ["No supporting evidence was provided in the source notes."]

    for item in items[:max_items]:
        pdf.setFillColor(BLUE)
        pdf.circle(x + 2.5, y + 2.8, 1.8, fill=1, stroke=0)
        y = _draw_wrapped(
            pdf,
            item,
            x + 10,
            y,
            width - 10,
            font_size=8.1,
            leading=10.1,
            max_lines=max_lines_each,
        )
        y -= 2.5
    return y


def _priority_color(priority: str):
    normalized = priority.lower()
    if "ready" in normalized or "advance" in normalized or "high" in normalized:
        return GREEN
    if "pass" in normalized or "decline" in normalized or "low" in normalized:
        return RED
    return AMBER


def _draw_metric_card(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    label: str,
    value: str,
) -> None:
    pdf.setFillColor(WHITE)
    pdf.roundRect(x, y, width, height, 7, fill=1, stroke=0)

    pdf.setFillColor(MUTED)
    pdf.setFont("Helvetica-Bold", 6.5)
    pdf.drawCentredString(x + width / 2, y + height - 16, label)

    clean_value = _clean(value)
    font_size = _fit_font_size(
        clean_value,
        "Helvetica-Bold",
        max_size=11.5 if label != "PRIORITY" else 9.0,
        min_size=6.7,
        max_width=width - 12,
    )
    value_color = _priority_color(clean_value) if label == "PRIORITY" else NAVY
    pdf.setFillColor(value_color)
    pdf.setFont("Helvetica-Bold", font_size)
    pdf.drawCentredString(x + width / 2, y + 13, clean_value)


def _split_evidence_snapshot(value: object) -> list[str]:
    """Convert the memo evidence sentence into the three reference bullets."""
    text = _clean(value, "")
    if not text:
        return [
            "Traction signals: Unknown.",
            "Customer signals: Unknown.",
            "Funding signals: Unknown.",
        ]

    labels = [
        ("Traction:", "Traction signals:"),
        ("Customers:", "Customer signals:"),
        ("Funding:", "Funding signals:"),
    ]
    positions: list[tuple[int, str, str]] = []
    for source, output in labels:
        index = text.find(source)
        if index >= 0:
            positions.append((index, source, output))

    if len(positions) != 3:
        return [text]

    positions.sort(key=lambda item: item[0])
    result: list[str] = []
    for idx, (start, source, output) in enumerate(positions):
        content_start = start + len(source)
        content_end = positions[idx + 1][0] if idx + 1 < len(positions) else len(text)
        content = text[content_start:content_end].strip().rstrip(".")
        result.append(f"{output} {content or 'Unknown'}.")
    return result


def memo_to_pdf_bytes(memo: Any) -> bytes:
    """Create the one-page investment brief in the reference layout."""
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle(f"{_clean(memo.company_name)} Investment Brief")

    # Header: title area on the left, three metric cards on the right.
    header_height = 72
    header_y = PAGE_HEIGHT - TOP_MARGIN - header_height
    pdf.setFillColor(NAVY)
    pdf.roundRect(
        MARGIN_X,
        header_y,
        CONTENT_WIDTH,
        header_height,
        10,
        fill=1,
        stroke=0,
    )

    card_width = 88
    card_gap = 6
    card_height = 48
    metrics_width = (card_width * 3) + (card_gap * 2)
    metrics_start_x = PAGE_WIDTH - MARGIN_X - metrics_width - 8
    title_x = MARGIN_X + 16
    title_width = metrics_start_x - title_x - 14

    company_name = _clean(memo.company_name)
    title_size = _fit_font_size(
        company_name,
        "Helvetica-Bold",
        17,
        11,
        title_width,
    )
    pdf.setFillColor(WHITE)
    pdf.setFont("Helvetica-Bold", title_size)
    pdf.drawString(title_x, header_y + 45, company_name)

    subtitle = (
        f"{_clean(memo.sector)} | "
        f"{_clean(memo.subsector)} | "
        f"{_clean(memo.stage)}"
    )
    _draw_wrapped(
        pdf,
        subtitle,
        title_x,
        header_y + 27,
        title_width,
        font_name="Helvetica",
        font_size=7.8,
        leading=9.2,
        max_lines=2,
        color=HexColor("#D7DEEF"),
    )

    metrics = [
        ("SCORE", f"{memo.opportunity_score}/100"),
        ("PRIORITY", _clean(memo.priority)),
        ("CONFIDENCE", f"{memo.confidence_score}/100"),
    ]
    card_y = header_y + 12
    for idx, (label, value) in enumerate(metrics):
        x = metrics_start_x + idx * (card_width + card_gap)
        _draw_metric_card(pdf, x, card_y, card_width, card_height, label, value)

    y = header_y - 22

    # Company summary.
    pdf.setFillColor(TEXT)
    pdf.setFont("Helvetica-Bold", 10.5)
    pdf.drawString(MARGIN_X, y, "Company Summary")
    y -= 15
    y = _draw_wrapped(
        pdf,
        _clip_at_word(memo.company_overview, 700),
        MARGIN_X,
        y,
        CONTENT_WIDTH,
        font_size=8.6,
        leading=10.7,
        max_lines=5,
    )
    y -= 7

    # Investment case and evidence columns.
    col_gap = 20
    col_width = (CONTENT_WIDTH - col_gap) / 2
    left_x = MARGIN_X
    right_x = MARGIN_X + col_width + col_gap
    section_top = y

    pdf.setFont("Helvetica-Bold", 10.5)
    pdf.setFillColor(TEXT)
    pdf.drawString(left_x, section_top, "Investment Case")
    left_y = section_top - 15
    thesis = _unique_items(memo.investment_thesis, limit=3, max_chars=300)
    left_y = _draw_bullets(
        pdf,
        thesis,
        left_x,
        left_y,
        col_width,
        max_lines_each=4,
    )

    pdf.setFont("Helvetica-Bold", 10.5)
    pdf.setFillColor(TEXT)
    pdf.drawString(right_x, section_top, "Evidence & Business Model")
    right_y = section_top - 15
    evidence = _split_evidence_snapshot(memo.traction_and_customers)
    right_y = _draw_bullets(
        pdf,
        _unique_items(evidence, limit=3, max_chars=145),
        right_x,
        right_y,
        col_width,
    )

    y = min(left_y, right_y) - 3
    pdf.setStrokeColor(BORDER)
    pdf.line(MARGIN_X, y, PAGE_WIDTH - MARGIN_X, y)
    y -= 18

    # Risks and diligence.
    section_top = y
    pdf.setFont("Helvetica-Bold", 10.5)
    pdf.setFillColor(TEXT)
    pdf.drawString(left_x, section_top, "Key Risks")
    left_y = section_top - 15
    left_y = _draw_bullets(
        pdf,
        _unique_items(memo.key_risks, limit=3, max_chars=135),
        left_x,
        left_y,
        col_width,
    )

    pdf.setFont("Helvetica-Bold", 10.5)
    pdf.setFillColor(TEXT)
    pdf.drawString(right_x, section_top, "Priority Diligence")
    right_y = section_top - 15
    right_y = _draw_bullets(
        pdf,
        _unique_items(memo.diligence_questions, limit=3, max_chars=135),
        right_x,
        right_y,
        col_width,
    )

    y = min(left_y, right_y) - 4

    # Recommendation callout.
    recommendation = (
        _unique_items(memo.recommended_next_steps, limit=1, max_chars=200)
        or ["Complete targeted diligence before advancing."]
    )[0]
    callout_height = 62
    callout_y = max(y - callout_height, 62)
    pdf.setFillColor(LIGHT_BLUE)
    pdf.setStrokeColor(BLUE)
    pdf.roundRect(
        MARGIN_X,
        callout_y,
        CONTENT_WIDTH,
        callout_height,
        9,
        fill=1,
        stroke=1,
    )
    pdf.setFillColor(BLUE)
    pdf.setFont("Helvetica-Bold", 9.2)
    pdf.drawString(
        MARGIN_X + 14,
        callout_y + callout_height - 19,
        "RECOMMENDED NEXT STEP",
    )
    _draw_wrapped(
        pdf,
        recommendation,
        MARGIN_X + 14,
        callout_y + callout_height - 36,
        CONTENT_WIDTH - 28,
        font_name="Helvetica-Bold",
        font_size=8.8,
        leading=10.7,
        max_lines=2,
        color=TEXT,
    )

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()
