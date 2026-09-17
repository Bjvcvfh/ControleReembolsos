from datetime import datetime

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from services.pdf_service import regenerate_pdf
from utils.currency import format_brl_from_cents


def format_plates(items: list[dict]) -> str:
    plates: list[str] = []
    seen: set[str] = set()
    for item in items:
        plate = str(item.get("placa") or "").strip().upper()
        if plate and plate not in seen:
            seen.add(plate)
            plates.append(plate)
    return " / ".join(plates) if plates else "-"


class ReimbursementDetailDialog(QDialog):
    def __init__(self, reimbursement: dict, parent=None):
        super().__init__(parent)
        self.reimbursement = reimbursement
        self.setWindowTitle(f"Reembolso {reimbursement['numero']}")
        self.setMinimumSize(720, 460)

        layout = QVBoxLayout(self)
        dt = datetime.fromisoformat(reimbursement["data_hora"])
        header = QLabel(
            f"<b>Reembolso nº:</b> {reimbursement['numero']}<br>"
            f"<b>Data:</b> {dt.strftime('%d/%m/%Y')} &nbsp; "
            f"<b>Hora:</b> {dt.strftime('%H:%M')}<br>"
            f"<b>Motorista:</b> {reimbursement['motorista_nome']}<br>"
            f"<b>Placa:</b> {format_plates(reimbursement['items'])}"
        )
        layout.addWidget(header)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Tipo de Serviço", "Data", "Placa", "O.S", "Valor"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        self._load_items()

        total = QLabel(f"TOTAL: {format_brl_from_cents(reimbursement['valor_total_centavos'])}")
        total.setObjectName("detailTotal")
        layout.addWidget(total)

        buttons_row = QHBoxLayout()
        self.regenerate_btn = QPushButton("Gerar PDF novamente")
        self.regenerate_btn.clicked.connect(self._regenerate_pdf)
        buttons_row.addWidget(self.regenerate_btn)
        buttons_row.addStretch(1)
        close_buttons = QDialogButtonBox(QDialogButtonBox.Close)
        close_buttons.rejected.connect(self.reject)
        buttons_row.addWidget(close_buttons)
        layout.addLayout(buttons_row)

    def _load_items(self) -> None:
        self.table.setRowCount(0)
        for item in self.reimbursement["items"]:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                item["tipo_servico_descricao"],
                datetime.strptime(item["data_servico"], "%Y-%m-%d").strftime("%d/%m/%Y") if item["data_servico"] else "-",
                item["placa"] or "-",
                item["os"] or "-",
                format_brl_from_cents(item["valor_centavos"]),
            ]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(value))
        self.table.resizeColumnsToContents()

    def _regenerate_pdf(self) -> None:
        try:
            path = regenerate_pdf(int(self.reimbursement["id"]))
            QMessageBox.information(self, "PDF gerado", f"PDF salvo em:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao gerar PDF", str(exc))
