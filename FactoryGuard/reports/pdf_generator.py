from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from database.repository import list_findings, list_actions, list_documents

def build_report(factory):
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=40,
        bottomMargin=40,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="Small",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11,
    ))

    findings = list_findings(factory["id"])
    actions = list_actions(factory["id"])
    documents = list_documents(factory["id"])

    story = [
        Paragraph("FactoryGuard AI — Food Safety & Quality Report", styles["Title"]),
        Paragraph(
            escape(f"{factory['name']} • {factory['business_type']} • {factory['primary_product']} • {factory['country']}"),
            styles["Normal"],
        ),
        Spacer(1, 16),
        Paragraph("Audit Evidence & Knowledge Base", styles["Heading2"]),
        Paragraph(
            f"Factory knowledge documents indexed: {len(documents)}",
            styles["Normal"],
        ),
        Spacer(1, 10),
        Paragraph(f"Total findings: {len(findings)}", styles["Heading2"]),
    ]

    if findings:
        data = [["Severity", "Finding", "Status"]]
        for f in findings:
            data.append([
                Paragraph(escape(str(f["severity"])), styles["Small"]),
                Paragraph(escape(str(f["title"])), styles["Small"]),
                Paragraph(escape(str(f["status"])), styles["Small"]),
            ])
        table = Table(data, repeatRows=1, colWidths=[65, 330, 90])
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story += [table, Spacer(1, 14)]

        story.append(Paragraph("Finding Details", styles["Heading2"]))
        for f in findings:
            story += [
                Paragraph(
                    escape(f"{f['severity']} — {f['title']}"),
                    styles["Heading3"],
                ),
                Paragraph(
                    "<b>Evidence:</b> " + escape(str(f.get("evidence", ""))),
                    styles["Normal"],
                ),
                Paragraph(
                    "<b>Assessment:</b> " + escape(str(f.get("explanation", ""))),
                    styles["Normal"],
                ),
                Paragraph(
                    "<b>Recommendation:</b> " + escape(str(f.get("recommendation", ""))),
                    styles["Normal"],
                ),
                Spacer(1, 8),
            ]

    story.append(Paragraph("Corrective Actions", styles["Heading2"]))
    if actions:
        for a in actions:
            story += [
                Paragraph(
                    escape(f"{a['status']} — {a['action']}"),
                    styles["Normal"],
                ),
                Paragraph(
                    escape(
                        f"Responsible: {a['responsible'] or 'Not assigned'} | "
                        f"Due: {a['due_date'] or 'Not specified'}"
                    ),
                    styles["Small"],
                ),
                Spacer(1, 6),
            ]
    else:
        story.append(Paragraph("No corrective actions recorded.", styles["Normal"]))

    doc.build(story)
    return buf.getvalue()
