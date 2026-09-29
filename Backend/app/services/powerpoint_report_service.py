import os
import math
from io import BytesIO
import re
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

from app.services.boost_powerpoint_content_service import (
    build_boost_powerpoint_content,
)


OUTPUT_DIR = "generated_reports"

UIMM_BLUE = RGBColor(35, 71, 103)
UIMM_RED = RGBColor(210, 0, 50)
DARK_TEXT = RGBColor(20, 31, 46)
GREY_TEXT = RGBColor(90, 105, 125)
LIGHT_GREY = RGBColor(242, 245, 248)
BORDER_GREY = RGBColor(210, 220, 230)
WHITE = RGBColor(255, 255, 255)


def safe_filename(value):
    value = str(value or "company").strip()
    value = re.sub(r"[^a-zA-Z0-9_-]+", "_", value)
    return value[:60] or "company"


def add_textbox(
    slide,
    text,
    left,
    top,
    width,
    height,
    font_size=18,
    bold=False,
    color=DARK_TEXT,
    align=PP_ALIGN.LEFT,
):
    box = slide.shapes.add_textbox(left, top, width, height)
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.vertical_anchor = MSO_ANCHOR.TOP

    paragraph = frame.paragraphs[0]
    paragraph.alignment = align

    run = paragraph.add_run()
    run.text = str(text or "")
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = color

    return box


def add_title(slide, title, subtitle=None):
    add_textbox(
        slide,
        title,
        Inches(0.55),
        Inches(0.35),
        Inches(8.2),
        Inches(0.45),
        font_size=24,
        bold=True,
        color=DARK_TEXT,
    )

    if subtitle:
        add_textbox(
            slide,
            subtitle,
            Inches(0.58),
            Inches(0.82),
            Inches(7.8),
            Inches(0.28),
            font_size=10,
            color=GREY_TEXT,
        )

    line = slide.shapes.add_shape(
        1,
        Inches(0.55),
        Inches(1.16),
        Inches(8.2),
        Inches(0.02),
    )
    line.fill.solid()
    line.fill.fore_color.rgb = UIMM_RED
    line.line.color.rgb = UIMM_RED


def add_footer(slide, page_number=None):
    add_textbox(
        slide,
        "UIMM Support Industries – diag 360",
        Inches(0.55),
        Inches(7.08),
        Inches(4.8),
        Inches(0.22),
        font_size=8,
        color=GREY_TEXT,
    )

    if page_number is not None:
        add_textbox(
            slide,
            str(page_number),
            Inches(9.05),
            Inches(7.05),
            Inches(0.25),
            Inches(0.2),
            font_size=8,
            color=GREY_TEXT,
            align=PP_ALIGN.RIGHT,
        )


def add_logo_block(slide):
    logo_path = Path(__file__).resolve().parents[1] / "assets" / "uimm-logo.jpg"

    if not logo_path.exists():
        print(f"Logo not found: {logo_path}")
        return

    with Image.open(logo_path) as logo:
        image_width, image_height = logo.size

    # Fit inside the header while preserving the original proportions.
    scale = min(2.0 / image_width, 1.1 / image_height)

    width = image_width * scale
    height = image_height * scale

    slide.shapes.add_picture(
        str(logo_path),
        Inches(9.0 - width),
        Inches(0.25),
        width=Inches(width),
        height=Inches(height),
    )






def add_bullet_list(slide, items, left, top, width, height, font_size=13, maximum=7):
    box = slide.shapes.add_textbox(left, top, width, height)
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True

    clean_items = [str(item).strip() for item in items if str(item or "").strip()]
    clean_items = clean_items[:maximum]

    if not clean_items:
        clean_items = ["Information à compléter."]

    for index, item in enumerate(clean_items):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.text = item
        paragraph.level = 0
        paragraph.font.size = Pt(font_size)
        paragraph.font.color.rgb = DARK_TEXT
        paragraph.space_after = Pt(6)

    return box


def add_section_slide(prs, title, page_number):
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = UIMM_BLUE

    add_textbox(
        slide,
        title,
        Inches(0.75),
        Inches(2.8),
        Inches(7.8),
        Inches(0.8),
        font_size=34,
        bold=True,
        color=WHITE,
    )

    red_line = slide.shapes.add_shape(
        1,
        Inches(0.75),
        Inches(3.75),
        Inches(2.2),
        Inches(0.06),
    )
    red_line.fill.solid()
    red_line.fill.fore_color.rgb = UIMM_RED
    red_line.line.color.rgb = UIMM_RED

    add_footer(slide, page_number)
    return slide


def add_simple_table(slide, title_left, title_right, left_items, right_items, top):
    add_textbox(
        slide,
        title_left,
        Inches(0.75),
        top,
        Inches(4.0),
        Inches(0.3),
        font_size=14,
        bold=True,
        color=UIMM_BLUE,
    )

    add_textbox(
        slide,
        title_right,
        Inches(5.0),
        top,
        Inches(4.0),
        Inches(0.3),
        font_size=14,
        bold=True,
        color=UIMM_BLUE,
    )

    left_box = slide.shapes.add_shape(
        1,
        Inches(0.7),
        top + Inches(0.42),
        Inches(4.1),
        Inches(2.0),
    )
    left_box.fill.solid()
    left_box.fill.fore_color.rgb = LIGHT_GREY
    left_box.line.color.rgb = BORDER_GREY

    right_box = slide.shapes.add_shape(
        1,
        Inches(4.95),
        top + Inches(0.42),
        Inches(4.1),
        Inches(2.0),
    )
    right_box.fill.solid()
    right_box.fill.fore_color.rgb = LIGHT_GREY
    right_box.line.color.rgb = BORDER_GREY

    add_bullet_list(
        slide,
        left_items,
        Inches(0.9),
        top + Inches(0.58),
        Inches(3.7),
        Inches(1.65),
        font_size=10,
        maximum=5,
    )

    add_bullet_list(
        slide,
        right_items,
        Inches(5.15),
        top + Inches(0.58),
        Inches(3.7),
        Inches(1.65),
        font_size=10,
        maximum=5,
    )


def add_cover_slide(prs, content):
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = UIMM_BLUE

    add_textbox(
        slide,
        "Dossier :",
        Inches(0.75),
        Inches(0.8),
        Inches(5.0),
        Inches(0.35),
        font_size=20,
        bold=True,
        color=WHITE,
    )

    add_textbox(
        slide,
        content["company_name"],
        Inches(0.75),
        Inches(1.25),
        Inches(6.5),
        Inches(0.6),
        font_size=30,
        bold=True,
        color=WHITE,
    )

    add_textbox(
        slide,
        "Au service des entreprises industrielles régionales\navec le dispositif BOOST INDUSTRIES",
        Inches(0.75),
        Inches(2.05),
        Inches(6.4),
        Inches(0.9),
        font_size=17,
        color=WHITE,
    )

    red_block = slide.shapes.add_shape(
        1,
        Inches(0),
        Inches(5.8),
        Inches(10),
        Inches(1.7),
    )
    red_block.fill.solid()
    red_block.fill.fore_color.rgb = UIMM_RED
    red_block.line.color.rgb = UIMM_RED

    add_textbox(
        slide,
        "UIMM Occitanie\nLA FABRIQUE DE L’AVENIR",
        Inches(0.75),
        Inches(6.05),
        Inches(5.4),
        Inches(0.8),
        font_size=24,
        bold=True,
        color=WHITE,
    )


def add_objectives_slide(prs, content, page_number):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(slide, "Rappel des objectifs")
    add_logo_block(slide)

    add_bullet_list(
        slide,
        content["objectives"],
        Inches(1.0),
        Inches(2.0),
        Inches(7.5),
        Inches(2.0),
        font_size=22,
        maximum=3,
    )

    add_textbox(
        slide,
        "Suite à l’analyse 360°, l’objectif est d’apporter une recommandation claire sur les leviers d’action prioritaires et les suites possibles.",
        Inches(1.0),
        Inches(4.7),
        Inches(7.6),
        Inches(0.8),
        font_size=15,
        color=GREY_TEXT,
    )

    add_footer(slide, page_number)


def add_summary_slide(prs, page_number):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(slide, "SOMMAIRE")
    add_logo_block(slide)

    items = [
        ("01", "Présentation & enjeux"),
        ("02", "Éléments internes & externes"),
        ("03", "Matrice SWOT"),
        ("04", "Vision Radar"),
        ("05", "Synthèse & préconisations"),
    ]

    top = 1.7
    for number, label in items:
        add_textbox(
            slide,
            number,
            Inches(1.0),
            Inches(top),
            Inches(0.6),
            Inches(0.3),
            font_size=16,
            bold=True,
            color=UIMM_RED,
        )
        add_textbox(
            slide,
            label,
            Inches(1.8),
            Inches(top),
            Inches(5.6),
            Inches(0.3),
            font_size=18,
            bold=True,
            color=DARK_TEXT,
        )
        top += 0.72

    add_footer(slide, page_number)


def add_company_presentation_slide(prs, content, page_number):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(slide, "Présentation & enjeux", content["company_name"])
    add_logo_block(slide)

    presentation = content["company_presentation"]

    add_textbox(slide, "HISTORIQUE :", Inches(0.8), Inches(1.55), Inches(2.2), Inches(0.3), 14, True, UIMM_BLUE)
    add_textbox(slide, presentation["history"], Inches(0.8), Inches(1.9), Inches(8.0), Inches(0.85), 13)

    add_textbox(slide, "ACTIVITÉ :", Inches(0.8), Inches(3.05), Inches(2.2), Inches(0.3), 14, True, UIMM_BLUE)
    add_textbox(slide, presentation["activity"], Inches(0.8), Inches(3.4), Inches(8.0), Inches(0.85), 13)

    add_textbox(slide, "LES DIRIGEANTS :", Inches(0.8), Inches(4.55), Inches(2.8), Inches(0.3), 14, True, UIMM_BLUE)
    add_textbox(slide, presentation["managers"], Inches(0.8), Inches(4.9), Inches(8.0), Inches(1.3), 12)

    add_footer(slide, page_number)


def add_company_issues_slide(prs, content, page_number):
    issues = content["company_issues"]
    sections = [
        ("Attente initiale du dirigeant vis à vis de BOOST :", issues["initial_expectation"]),
        ("Situation de l’entreprise :", issues["situation"]),
        ("Gouvernance :", issues["governance"]),
        ("Avenir :", issues["future"]),
    ]
    slide = None
    top = 6.7
    slide_count = 0
    line_height = 0.23

    for label, value in sections:
        # Explicit wrapping and line spacing make the occupied height predictable.
        # A conservative line length also leaves room for font substitution.
        lines = []
        for paragraph in str(value or "").splitlines():
            lines.extend(textwrap.wrap(paragraph, width=48) or [""])
        lines = lines or [""]
        continuation = False

        while lines:
            capacity = int((6.7 - top - 0.5) / line_height)
            if capacity < 3:
                slide = prs.slides.add_slide(prs.slide_layouts[6])
                add_title(slide, "ENJEUX" if slide_count == 0 else "ENJEUX (suite)", content["company_name"])
                add_logo_block(slide)
                add_footer(slide, page_number + slide_count)
                slide_count += 1
                top = 1.65
                capacity = int((6.7 - top - 0.5) / line_height)

            chunk, lines = lines[:capacity], lines[capacity:]
            heading = label + (" (suite)" if continuation else "")
            add_textbox(slide, heading, Inches(0.75), Inches(top), Inches(8.2), Inches(0.35), 12, True, UIMM_BLUE)
            height = len(chunk) * line_height + 0.08
            box = add_textbox(
                slide, "\n".join(chunk), Inches(0.75), Inches(top + 0.4),
                Inches(8.2), Inches(height), 12,
            )
            frame = box.text_frame
            frame.margin_top = frame.margin_bottom = 0
            frame.word_wrap = False
            for paragraph in frame.paragraphs:
                paragraph.line_spacing = Pt(line_height * 72)
                paragraph.space_before = paragraph.space_after = Pt(0)
                for run in paragraph.runs:
                    run.font.name = "Arial"
            top += 0.4 + height + 0.2
            continuation = True

    return slide_count


def add_interview_slide(prs, title, items, page_number):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(slide, title)
    add_logo_block(slide)

    add_bullet_list(
        slide,
        items,
        Inches(0.9),
        Inches(1.65),
        Inches(8.0),
        Inches(4.9),
        font_size=14,
        maximum=10,
    )

    add_footer(slide, page_number)


def add_axis_swot_slide(prs, axis_swot, page_number):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(slide, axis_swot["axis_name"], f"Score : {axis_swot['score_percentage']}%")
    add_logo_block(slide)

    add_simple_table(
        slide,
        "Forces",
        "Faiblesses",
        axis_swot.get("strengths", []),
        axis_swot.get("weaknesses", []),
        Inches(1.45),
    )

    add_simple_table(
        slide,
        "Opportunités",
        "Menaces",
        axis_swot.get("opportunities", []),
        axis_swot.get("threats", []),
        Inches(4.15),
    )

    if axis_swot.get("comment"):
        add_textbox(
            slide,
            f"Commentaire : {axis_swot['comment']}",
            Inches(0.75),
            Inches(6.55),
            Inches(8.3),
            Inches(0.35),
            font_size=9,
            color=GREY_TEXT,
        )

    add_footer(slide, page_number)


def add_global_swot_slide(prs, title, letter, items, page_number):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(slide, "Analyse S.W.O.T", title)
    add_logo_block(slide)

    add_textbox(
        slide,
        letter,
        Inches(0.8),
        Inches(1.55),
        Inches(0.8),
        Inches(0.8),
        font_size=42,
        bold=True,
        color=UIMM_RED,
        align=PP_ALIGN.CENTER,
    )

    add_bullet_list(
        slide,
        items,
        Inches(1.7),
        Inches(1.45),
        Inches(7.2),
        Inches(5.2),
        font_size=11,
        maximum=12,
    )

    add_footer(slide, page_number)


def make_radar_image(scores, archive_averages):
    """Draw the same 0–100 comparison as the application's radar."""
    size = (1200, 790)
    chart = Image.new("RGBA", size, "white")
    draw = ImageDraw.Draw(chart, "RGBA")
    font = ImageFont.load_default()
    center_x, center_y, radius = 600, 365, 265
    count = len(scores)

    def point(index, percentage, distance=None):
        angle = -math.pi / 2 + 2 * math.pi * index / count
        extent = radius * max(0, min(float(percentage), 100)) / 100 if distance is None else distance
        return (center_x + extent * math.cos(angle), center_y + extent * math.sin(angle))

    for level in (25, 50, 75, 100):
        corners = [point(index, level) for index in range(count)]
        if count >= 3:
            draw.line(corners + [corners[0]], fill=(203, 213, 225, 255), width=2)
        draw.text((center_x + 7, center_y - radius * level / 100 - 10), str(level), font=font, fill=(100, 116, 139, 255))
    for index, score in enumerate(scores):
        endpoint = point(index, 100)
        draw.line(((center_x, center_y), endpoint), fill=(203, 213, 225, 255), width=2)

    current = [point(index, score["score_percentage"]) for index, score in enumerate(scores)]
    archived = [
        point(index, archive_averages[score["axis_id"]])
        if score["axis_id"] in archive_averages else None
        for index, score in enumerate(scores)
    ]
    if all(value is not None for value in archived) and count >= 3:
        overlay = Image.new("RGBA", size, (0, 0, 0, 0))
        ImageDraw.Draw(overlay).polygon(archived, fill=(37, 99, 235, 14))
        chart = Image.alpha_composite(chart, overlay)
        draw = ImageDraw.Draw(chart, "RGBA")
    if count >= 3:
        pairs = [(index, (index + 1) % count) for index in range(count)]
    else:
        pairs = [(index, index + 1) for index in range(count - 1)]
    for first, second in pairs:
        if archived[first] is not None and archived[second] is not None:
            draw.line((archived[first], archived[second]), fill=(37, 99, 235, 255), width=4)
    for position in archived:
        if position is not None:
            x, y = position
            draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(29, 78, 216, 255))
    if count >= 3:
        overlay = Image.new("RGBA", size, (0, 0, 0, 0))
        ImageDraw.Draw(overlay).polygon(current, fill=(34, 197, 94, 64))
        chart = Image.alpha_composite(chart, overlay)
        draw = ImageDraw.Draw(chart, "RGBA")
    draw.line(current + [current[0]] if count >= 3 else current, fill=(22, 163, 74, 255), width=5, joint="curve")
    for x, y in current:
        draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=(22, 101, 52, 255))
    output = BytesIO()
    chart.convert("RGB").save(output, format="PNG")
    output.seek(0)
    return output


def add_radar_slide(prs, content, page_number):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(slide, "VISION RADAR", content["company_name"])
    add_logo_block(slide)
    scores = content["radar_scores"]
    if scores:
        chart = make_radar_image(scores, content.get("archive_average_scores", {}))
        slide.shapes.add_picture(chart, Inches(0.7), Inches(1.3), width=Inches(8.6), height=Inches(5.55))
        for index, score in enumerate(scores):
            angle = -math.pi / 2 + 2 * math.pi * index / len(scores)
            x = 0.7 + (600 + 340 * math.cos(angle)) / 1200 * 8.6
            y = 1.3 + (365 + 340 * math.sin(angle)) / 790 * 5.55
            add_textbox(slide, score["axis_name"], Inches(x - 0.85), Inches(y - 0.13), Inches(1.7), Inches(0.3), 11, True, DARK_TEXT, PP_ALIGN.CENTER)
        add_textbox(slide, "● Entreprise actuelle", Inches(2.1), Inches(6.65), Inches(2.4), Inches(0.3), 11, False, RGBColor(22, 163, 74))
        if content.get("archive_average_scores"):
            add_textbox(slide, "● Moyenne archive", Inches(5.2), Inches(6.65), Inches(2.4), Inches(0.3), 11, False, RGBColor(37, 99, 235))
    else:
        add_textbox(slide, "Aucun score disponible.", Inches(1), Inches(2), Inches(8), Inches(0.5), 14)
    add_footer(slide, page_number)


def add_report_text_slides(prs, title, text, page_number):
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    if not lines:
        return 0
    # Keep each slide legible while retaining the saved report text.
    chunks = [lines[index:index + 10] for index in range(0, len(lines), 10)]
    for offset, chunk in enumerate(chunks):
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        add_title(slide, title + (" (suite)" if offset else ""))
        add_logo_block(slide)
        add_bullet_list(slide, chunk, Inches(0.9), Inches(1.55), Inches(8.1), Inches(5.25), font_size=12, maximum=10)
        add_footer(slide, page_number + offset)
    return len(chunks)


def add_synthesis_slide(prs, content, page_number):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(slide, "SYNTHESE & PRECONISATIONS", "Leviers d’action potentiels")
    add_logo_block(slide)

    synthesis = content["synthesis"]

    add_bullet_list(
        slide,
        synthesis["priority_action_levers"],
        Inches(0.9),
        Inches(1.6),
        Inches(8.0),
        Inches(3.4),
        font_size=14,
        maximum=7,
    )

    add_textbox(
        slide,
        "Conclusion",
        Inches(0.9),
        Inches(5.25),
        Inches(2.0),
        Inches(0.3),
        font_size=15,
        bold=True,
        color=UIMM_BLUE,
    )

    add_textbox(
        slide,
        synthesis["conclusion"] or "Conclusion à compléter.",
        Inches(0.9),
        Inches(5.62),
        Inches(8.0),
        Inches(0.8),
        font_size=11,
        color=DARK_TEXT,
    )

    add_footer(slide, page_number)


def add_complementary_mission_slide(prs, content, page_number):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(slide, "PROPOSITION MISSION COMPLEMENTAIRE")
    add_logo_block(slide)

    synthesis = content["synthesis"]

    add_textbox(
        slide,
        "A:",
        Inches(0.9),
        Inches(1.6),
        Inches(0.4),
        Inches(0.3),
        font_size=16,
        bold=True,
        color=UIMM_RED,
    )

    add_textbox(
        slide,
        synthesis["complementary_mission"],
        Inches(1.35),
        Inches(1.6),
        Inches(7.4),
        Inches(1.8),
        font_size=13,
        color=DARK_TEXT,
    )

    add_textbox(
        slide,
        "B:",
        Inches(0.9),
        Inches(3.8),
        Inches(0.4),
        Inches(0.3),
        font_size=16,
        bold=True,
        color=UIMM_RED,
    )

    add_textbox(
        slide,
        "Mission complémentaire à préciser selon les priorités retenues avec l’entreprise.",
        Inches(1.35),
        Inches(3.8),
        Inches(7.4),
        Inches(0.8),
        font_size=13,
        color=DARK_TEXT,
    )

    add_footer(slide, page_number)


def add_thank_you_slide(prs, content, page_number):
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = UIMM_BLUE

    add_textbox(
        slide,
        "Personnes ressources :",
        Inches(0.8),
        Inches(1.6),
        Inches(5.5),
        Inches(0.35),
        font_size=18,
        bold=True,
        color=WHITE,
    )

    add_textbox(
        slide,
        content["resource_people"],
        Inches(0.8),
        Inches(2.05),
        Inches(6.8),
        Inches(0.8),
        font_size=14,
        color=WHITE,
    )

    add_textbox(
        slide,
        "Merci !!!",
        Inches(0.8),
        Inches(4.5),
        Inches(6.0),
        Inches(0.8),
        font_size=40,
        bold=True,
        color=WHITE,
    )

    red_block = slide.shapes.add_shape(
        1,
        Inches(0),
        Inches(6.25),
        Inches(10),
        Inches(1.25),
    )
    red_block.fill.solid()
    red_block.fill_fore_color = UIMM_RED
    red_block.fill.fore_color.rgb = UIMM_RED
    red_block.line.color.rgb = UIMM_RED

    add_footer(slide, page_number)


def generate_report_powerpoint(company, report, db):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    content = build_boost_powerpoint_content(
        db=db,
        company=company,
        report=report,
    )

    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    page_number = 1

    add_cover_slide(prs, content)
    page_number += 1

    add_objectives_slide(prs, content, page_number)
    page_number += 1

    add_summary_slide(prs, page_number)
    page_number += 1

    add_section_slide(prs, "Présentation & enjeux", page_number)
    page_number += 1

    add_company_presentation_slide(prs, content, page_number)
    page_number += 1

    page_number += add_company_issues_slide(prs, content, page_number)

    interview_sections = [
        ("ÉLÉMENTS EXTERNES DU DIAGNOSTIC", content["interviews"]["external"]),
        ("ÉLÉMENTS INTERNES DU DIAGNOSTIC", content["interviews"]["internal_words"]),
        ('RÉPONSES : "Si j’avais une baguette magique..."', content["interviews"]["magic_wand"]),
        ("SIGNAUX CAPTÉS DANS LE DIAGNOSTIC", content["interviews"]["captured_signals"]),
    ]
    if any(items for _, items in interview_sections):
        add_section_slide(prs, "Éléments internes & externes", page_number)
        page_number += 1
        for title, items in interview_sections:
            if items:
                add_interview_slide(prs, title, items, page_number)
                page_number += 1

    add_section_slide(prs, "Restitution", page_number)
    page_number += 1

    for axis_swot in content["swot_by_axis"]:
        add_axis_swot_slide(prs, axis_swot, page_number)
        page_number += 1

    add_global_swot_slide(
        prs,
        "Forces",
        "S",
        content["global_swot"]["strengths"],
        page_number,
    )
    page_number += 1

    add_global_swot_slide(
        prs,
        "Faiblesses",
        "W",
        content["global_swot"]["weaknesses"],
        page_number,
    )
    page_number += 1

    add_global_swot_slide(
        prs,
        "Opportunités",
        "O",
        content["global_swot"]["opportunities"],
        page_number,
    )
    page_number += 1

    add_global_swot_slide(
        prs,
        "Menaces",
        "T",
        content["global_swot"]["threats"],
        page_number,
    )
    page_number += 1

    add_section_slide(prs, "Vision Radar", page_number)
    page_number += 1

    add_radar_slide(prs, content, page_number)
    page_number += 1


    add_section_slide(prs, "Synthèse & préconisations", page_number)
    page_number += 1

    page_number += add_report_text_slides(prs, "SYNTHÈSE DU DIAGNOSTIC", content["synthesis"]["diagnostic_summary"], page_number)
    page_number += add_report_text_slides(prs, "PRÉCONISATIONS DÉTAILLÉES", content["synthesis"]["recommendations_text"], page_number)

    add_synthesis_slide(prs, content, page_number)
    page_number += 1

    add_complementary_mission_slide(prs, content, page_number)
    page_number += 1

    add_thank_you_slide(prs, content, page_number)

    filename = (
        f"BOOST_restitution_{safe_filename(company.name)}_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.pptx"
    )

    file_path = os.path.join(OUTPUT_DIR, filename)
    prs.save(file_path)

    return file_path