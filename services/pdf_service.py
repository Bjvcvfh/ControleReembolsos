from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from services.reimbursement_service import ReimbursementService
from utils.currency import format_brl_from_cents
from utils.filenames import safe_filename_part, unique_path
from utils.paths import downloads_dir


def generate_reimbursement_pdf(reimbursement: dict, output_dir: Path | None = None) -> Path:
    output_dir = output_dir or downloads_dir()
    dt = datetime.fromisoformat(reimbursement["data_hora"])
    date_part = dt.strftime("%d-%m-%Y")
    driver_part = safe_filename_part(reimbursement["motorista_nome"])
    filename = f"Reembolso_{date_part}_{driver_part}_{reimbursement['numero']}.pdf"
    pdf_path = unique_path(output_dir / filename)

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"Reembolso {reimbursement['numero']}",
    )
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>REEMBOLSO</b>", styles["Title"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"<b>Reembolso no:</b> {reimbursement['numero']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Data:</b> {dt.strftime('%d/%m/%Y')}", styles["Normal"]))
    story.append(Paragraph(f"<b>Hora:</b> {dt.strftime('%H:%M')}", styles["Normal"]))
    story.append(Paragraph(f"<b>Motorista:</b> {reimbursement['motorista_nome']}", styles["Normal"]))
    story.append(Spacer(1, 14))

    rows = [["Tipo de Servico", "Data", "O.S", "Valor"]]
    for item in reimbursement["items"]:
        service_date = datetime.strptime(item["data_servico"], "%Y-%m-%d").strftime("%d/%m/%Y") if item["data_servico"] else "-"
        rows.append(
            [
                item["tipo_servico_descricao"],
                service_date,
                item["os"] or "-",
                format_brl_from_cents(item["valor_centavos"]),
            ]
        )
    rows.append(["", "", "TOTAL", format_brl_from_cents(reimbursement["valor_total_centavos"])])

    table = Table(rows, colWidths=[78 * mm, 28 * mm, 38 * mm, 33 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c8d0da")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f5f7fa")]),
                ("ALIGN", (3, 1), (3, -1), "RIGHT"),
                ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8eef7")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 28))

    signature = Table([[""], ["Autorização"]], colWidths=[70 * mm])
    signature.setStyle(
        TableStyle(
            [
                ("LINEABOVE", (0, 0), (0, 0), 0.8, colors.HexColor("#333333")),
                ("ALIGN", (0, 1), (0, 1), "CENTER"),
                ("TOPPADDING", (0, 0), (0, 0), 8),
                ("TOPPADDING", (0, 1), (0, 1), 4),
                ("BOTTOMPADDING", (0, 0), (0, 1), 0),
            ]
        )
    )
    story.append(signature)
    story.append(Spacer(1, 18))
    story.append(
        Paragraph(
            "Documento gerado automaticamente pelo Controle de Reembolsos.",
            styles["Italic"],
        )
    )
    doc.build(story)
    return pdf_path


def regenerate_pdf(reimbursement_id: int) -> Path:
    service = ReimbursementService()
    reimbursement = service.get_reimbursement(reimbursement_id)
    pdf_path = generate_reimbursement_pdf(reimbursement)
    service.set_pdf_path(reimbursement_id, str(pdf_path))
    return pdf_path
