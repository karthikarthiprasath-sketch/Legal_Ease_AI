from io import BytesIO
from pathlib import Path
import re
import html

from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from fpdf import FPDF


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]
LOGO_PATH = BASE_DIR / "assets" / "logo.png"


# ============================================================
# TEXT SANITIZATION
# ============================================================

def sanitize_text(text: str) -> str:
    """
    Removes/replaces common problematic Unicode characters
    so DOCX/PDF formatting is safer.
    """

    if not text:
        return ""

    replacements = {
        "—": "-",
        "–": "-",
        "−": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "•": "-",
        "…": "...",
        "₹": "Rs.",
        "\u00a0": " ",
        "\t": "    ",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove unsupported control characters
    text = "".join(
        char for char in text
        if char in "\n\r" or ord(char) >= 32
    )

    return text.strip()


# ============================================================
# TXT
# ============================================================

def text_to_txt(text: str) -> str:
    return sanitize_text(text)


# ============================================================
# DOCX HELPERS
# ============================================================

def add_docx_footer(section):
    footer = section.footer

    paragraph = footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

    run = paragraph.add_run(
        "LegalEase - AI-assisted legal document draft"
    )

    run.font.name = "Times New Roman"
    run.font.size = Pt(9)


def add_docx_logo(document):
    """
    Adds logo to the first page header.
    """

    if not LOGO_PATH.exists():
        return

    section = document.sections[0]

    header = section.header
    paragraph = header.paragraphs[0]

    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

    run = paragraph.add_run()

    run.add_picture(
        str(LOGO_PATH),
        width=Inches(1.0)
    )


def add_page_number(paragraph):

    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

    run = paragraph.add_run()

    run.font.name = "Times New Roman"
    run.font.size = Pt(9)

    run.add_text("Page ")

    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(
        qn("w:fldCharType"),
        "begin"
    )

    instr_text = OxmlElement("w:instrText")
    instr_text.set(
        qn("xml:space"),
        "preserve"
    )

    instr_text.text = "PAGE"

    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(
        qn("w:fldCharType"),
        "end"
    )

    run._r.append(fld_char1)
    run._r.append(instr_text)
    run._r.append(fld_char2)


def add_terms_table(document, terms):
    """
    Creates a simple Terms & Conditions table.

    Expected input example:
    Salary: Rs. 25000 per month;
    Duration: 1 year;
    Notice Period: 30 days
    """

    if not terms:
        return

    table = document.add_table(
        rows=1,
        cols=2
    )

    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"

    header = table.rows[0].cells

    header[0].text = "Term"
    header[1].text = "Details"

    for cell in header:
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True
                run.font.name = "Times New Roman"
                run.font.size = Pt(10)

    for item in terms.split(";"):

        item = item.strip()

        if not item:
            continue

        if ":" in item:
            key, value = item.split(":", 1)
        else:
            key = "Term"
            value = item

        row = table.add_row().cells

        row[0].text = key.strip()
        row[1].text = value.strip()

        for cell in row:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(10)

    document.add_paragraph()


# ============================================================
# DOCX
# ============================================================

def format_docx(text: str, doc_type: str = "") -> bytes:

    text = sanitize_text(text)

    document = Document()

    section = document.sections[0]

    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)

    # Normal style
    style = document.styles["Normal"]

    style.font.name = "Times New Roman"
    style.font.size = Pt(11)

    # Logo
    add_docx_logo(document)

    # Footer
    add_docx_footer(section)

    lines = text.splitlines()

    for index, line in enumerate(lines):

        line = line.strip()

        if not line:
            document.add_paragraph()
            continue

        paragraph = document.add_paragraph()

        paragraph.paragraph_format.space_after = Pt(6)
        paragraph.paragraph_format.line_spacing = 1.15

        run = paragraph.add_run(line)

        run.font.name = "Times New Roman"
        run.font.size = Pt(11)

        # Document title
        if index == 0:

            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

            run.bold = True
            run.font.size = Pt(16)

        # Headings
        elif (
            line.isupper()
            or line.startswith("ARTICLE ")
            or line.startswith("ARTICLE:")
            or line.startswith("SECTION ")
            or line.startswith("SECTION:")
            or line.startswith("CLAUSE ")
            or line.startswith("CLAUSE:")
            or line.startswith("TERMS ")
        ):

            run.bold = True
            run.font.size = Pt(12)

        # Signature
        elif (
            "SIGNATURE" in line.upper()
            or "SIGNATURES" in line.upper()
        ):

            run.bold = True
            run.font.size = Pt(12)

    # Page number
    footer = section.footer

    footer_paragraph = footer.paragraphs[0]

    footer_paragraph.clear()

    add_page_number(footer_paragraph)

    output = BytesIO()

    document.save(output)

    return output.getvalue()


# Keep old frontend function name
def text_to_docx(text: str) -> bytes:
    return format_docx(text)


# ============================================================
# PDF CLASS
# ============================================================

class LegalEasePDF(FPDF):

    def header(self):

        if LOGO_PATH.exists():

            try:
                self.image(
                    str(LOGO_PATH),
                    x=95,
                    y=8,
                    w=20
                )

                self.ln(22)

            except Exception:
                self.ln(10)

        else:
            self.ln(10)

        self.set_draw_color(
            180,
            180,
            180
        )

        self.line(
            20,
            30,
            190,
            30
        )

        self.ln(8)

    def footer(self):

        self.set_y(-15)

        self.set_font(
            "Times",
            size=8
        )

        self.set_text_color(
            100,
            100,
            100
        )

        self.cell(
            0,
            5,
            "LegalEase - AI-assisted legal document draft",
            align="C"
        )


# ============================================================
# PDF
# ============================================================

def format_pdf(text: str, doc_type: str = "") -> bytes:

    text = sanitize_text(text)

    pdf = LegalEasePDF()

    pdf.set_auto_page_break(
        auto=True,
        margin=20
    )

    pdf.set_margins(
        left=20,
        top=35,
        right=20
    )

    pdf.add_page()

    pdf.set_font(
        "Times",
        size=11
    )

    lines = text.splitlines()

    for index, line in enumerate(lines):

        line = line.strip()

        if not line:
            pdf.ln(5)
            continue

        # Extra PDF safety
        safe_line = (
            line
            .encode(
                "latin-1",
                "replace"
            )
            .decode("latin-1")
        )

        # Document title
        if index == 0:

            pdf.set_font(
                "Times",
                style="B",
                size=16
            )

            pdf.multi_cell(
                0,
                8,
                safe_line,
                align="C"
            )

            pdf.ln(5)

            pdf.set_font(
                "Times",
                size=11
            )

            continue

        # Headings
        if (
            safe_line.isupper()
            or safe_line.startswith("ARTICLE ")
            or safe_line.startswith("ARTICLE:")
            or safe_line.startswith("SECTION ")
            or safe_line.startswith("SECTION:")
            or safe_line.startswith("CLAUSE ")
            or safe_line.startswith("CLAUSE:")
            or "SIGNATURE" in safe_line.upper()
        ):

            pdf.set_font(
                "Times",
                style="B",
                size=12
            )

            pdf.multi_cell(
                0,
                7,
                safe_line
            )

            pdf.ln(2)

            pdf.set_font(
                "Times",
                size=11
            )

        # Bullet-style terms
        elif (
            safe_line.startswith("- ")
            or safe_line.startswith("* ")
        ):

            bullet_text = safe_line.lstrip("-* ").strip()

            pdf.multi_cell(
                0,
                6,
                "- " + bullet_text
            )

        else:

            pdf.multi_cell(
                0,
                6,
                safe_line
            )

    return bytes(pdf.output())


# Keep old frontend function name
def text_to_pdf(text: str) -> bytes:
    return format_pdf(text)


# ============================================================
# HTML PREVIEW
# ============================================================

def format_html_preview(text: str) -> str:

    text = sanitize_text(text)

    lines = text.splitlines()

    output = []

    for index, line in enumerate(lines):

        line = line.strip()

        if not line:
            continue

        safe = html.escape(line)

        # Title
        if index == 0:

            output.append(
                f"<h2 style='text-align:center;'>"
                f"{safe}"
                f"</h2>"
            )

        # Heading
        elif (
            line.isupper()
            or line.startswith("ARTICLE ")
            or line.startswith("SECTION ")
            or line.startswith("CLAUSE ")
            or "SIGNATURE" in line.upper()
        ):

            output.append(
                f"<h4>{safe}</h4>"
            )

        # Bullet
        elif (
            line.startswith("- ")
            or line.startswith("* ")
        ):

            output.append(
                f"<li>{safe.lstrip('-* ')}</li>"
            )

        else:

            output.append(
                f"<p>{safe}</p>"
            )

    return "\n".join(output)