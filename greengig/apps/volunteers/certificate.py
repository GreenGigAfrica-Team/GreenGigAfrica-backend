"""
PDF certificate generation for volunteers using ReportLab.
"""
import io
from django.utils import timezone


def generate_certificate(volunteer_name: str, task_title: str, org_name: str, completed_date) -> bytes:
    """
    Generate a PDF certificate of participation for a volunteer.
    Returns raw PDF bytes.
    """
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        styles = getSampleStyleSheet()
        green = colors.HexColor("#1a6b3c")
        light_green = colors.HexColor("#e8f5e9")

        title_style = ParagraphStyle(
            "Title",
            parent=styles["Title"],
            fontSize=32,
            textColor=green,
            alignment=TA_CENTER,
            spaceAfter=6,
        )
        subtitle_style = ParagraphStyle(
            "Subtitle",
            parent=styles["Normal"],
            fontSize=14,
            textColor=colors.grey,
            alignment=TA_CENTER,
            spaceAfter=20,
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=13,
            alignment=TA_CENTER,
            spaceAfter=10,
        )
        name_style = ParagraphStyle(
            "Name",
            parent=styles["Normal"],
            fontSize=26,
            textColor=green,
            alignment=TA_CENTER,
            spaceAfter=10,
            fontName="Helvetica-Bold",
        )

        date_str = completed_date.strftime("%B %d, %Y") if completed_date else timezone.now().strftime("%B %d, %Y")

        story = [
            Spacer(1, 0.5 * cm),
            Paragraph("🌿 GreenGig Africa", title_style),
            Paragraph("Certificate of Participation", subtitle_style),
            HRFlowable(width="80%", thickness=2, color=green, spaceAfter=20),
            Paragraph("This is to certify that", body_style),
            Paragraph(volunteer_name, name_style),
            Paragraph(
                f"has successfully completed the volunteer task <b>{task_title}</b>",
                body_style,
            ),
            Paragraph(f"organised by <b>{org_name}</b>", body_style),
            Paragraph(f"on <b>{date_str}</b>", body_style),
            Spacer(1, 1 * cm),
            HRFlowable(width="60%", thickness=1, color=colors.lightgrey, spaceAfter=10),
            Paragraph(
                "Thank you for contributing to a greener Lagos and a healthier planet.",
                ParagraphStyle(
                    "Footer",
                    parent=styles["Normal"],
                    fontSize=11,
                    textColor=colors.grey,
                    alignment=TA_CENTER,
                ),
            ),
            Spacer(1, 0.5 * cm),
            Paragraph(
                "GreenGig Africa — Clean Green, Earn Clean.",
                ParagraphStyle(
                    "Brand",
                    parent=styles["Normal"],
                    fontSize=10,
                    textColor=green,
                    alignment=TA_CENTER,
                ),
            ),
        ]

        doc.build(story)
        return buffer.getvalue()

    except ImportError:
        # ReportLab not installed — return a plain-text fallback
        text = (
            f"CERTIFICATE OF PARTICIPATION\n\n"
            f"This certifies that {volunteer_name} completed\n"
            f"'{task_title}' organised by {org_name}.\n\n"
            f"GreenGig Africa"
        )
        return text.encode("utf-8")
