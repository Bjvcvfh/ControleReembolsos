from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.catalog_service import CatalogService
from services.export_service import ExportService
from services.reimbursement_service import ReimbursementService
from ui.dialogs.reimbursement_detail_dialog import ReimbursementDetailDialog
from utils.currency import format_brl_from_cents
from utils.paths import downloads_dir


class HistoryPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.reimbursement_service = ReimbursementService()
        self.catalog = CatalogService()
        self.current_rows: list[dict] = []
        self._build_ui()
        self.reload_service_filter()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        title = QLabel("HISTÓRICO")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        filters = QGridLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Pesquisar por número ou motorista")
        self.search_edit.textChanged.connect(self.refresh)
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("dd/MM/yyyy")
        self.start_date.setSpecialValueText("")
        self.start_date.setDate(self.start_date.minimumDate())
        self.start_date.dateChanged.connect(self.refresh)
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("dd/MM/yyyy")
        self.end_date.setSpecialValueText("")
        self.end_date.setDate(self.end_date.minimumDate())
        self.end_date.dateChanged.connect(self.refresh)
        self.service_filter = QComboBox()
        self.service_filter.currentIndexChanged.connect(self.refresh)
        clear_btn = QPushButton("Limpar filtros")
        clear_btn.clicked.connect(self.clear_filters)
        export_btn = QPushButton("Exportar CSV")
        export_btn.clicked.connect(self.export_csv)

        filters.addWidget(QLabel("Pesquisa:"), 0, 0)
        filters.addWidget(self.search_edit, 0, 1, 1, 3)
        filters.addWidget(QLabel("Data inicial:"), 1, 0)
        filters.addWidget(self.start_date, 1, 1)
        filters.addWidget(QLabel("Data final:"), 1, 2)
        filters.addWidget(self.end_date, 1, 3)
        filters.addWidget(QLabel("Tipo:"), 2, 0)
        filters.addWidget(self.service_filter, 2, 1)
        filters.addWidget(clear_btn, 2, 2)
        filters.addWidget(export_btn, 2, 3)
        layout.addLayout(filters)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Nº", "Data", "Motorista", "Itens", "Total"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.show_selected)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

        actions = QHBoxLayout()
        view_btn = QPushButton("Visualizar")
        view_btn.clicked.connect(self.show_selected)
        actions.addStretch(1)
        actions.addWidget(view_btn)
        layout.addLayout(actions)

    def reload_service_filter(self) -> None:
        selected = self.service_filter.currentText() if hasattr(self, "service_filter") else ""
        self.service_filter.blockSignals(True)
        self.service_filter.clear()
        self.service_filter.addItem("Todos", "")
        for service in self.catalog.list_service_types(include_inactive=True):
            self.service_filter.addItem(service["descricao"], service["descricao"])
        if selected:
            index = self.service_filter.findText(selected)
            if index >= 0:
                self.service_filter.setCurrentIndex(index)
        self.service_filter.blockSignals(False)

    def refresh(self) -> None:
        start = self._date_value(self.start_date)
        end = self._date_value(self.end_date)
        service_type = self.service_filter.currentData() or ""
        self.current_rows = self.reimbursement_service.list_history(
            self.search_edit.text(),
            start,
            end,
            service_type,
        )
        self.table.setRowCount(0)
        for row_data in self.current_rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            dt = datetime.fromisoformat(row_data["data_hora"])
            values = [
                row_data["numero"],
                dt.strftime("%d/%m/%Y %H:%M"),
                row_data["motorista_nome"],
                str(row_data["quantidade_itens"]),
                format_brl_from_cents(row_data["valor_total_centavos"]),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col in (0, 3, 4):
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)
        self.table.resizeColumnsToContents()

    def clear_filters(self) -> None:
        self.search_edit.clear()
        self.start_date.setDate(self.start_date.minimumDate())
        self.end_date.setDate(self.end_date.minimumDate())
        self.service_filter.setCurrentIndex(0)
        self.refresh()

    def show_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self.current_rows):
            QMessageBox.information(self, "Histórico", "Selecione um reembolso.")
            return
        reimbursement_id = int(self.current_rows[row]["id"])
        reimbursement = self.reimbursement_service.get_reimbursement(reimbursement_id)
        dialog = ReimbursementDetailDialog(reimbursement, self)
        dialog.exec()

    def export_csv(self) -> None:
        default = downloads_dir() / f"historico_reembolsos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar CSV",
            str(default),
            "CSV (*.csv)",
        )
        if not path:
            return
        try:
            ExportService().export_history_csv(Path(path))
            QMessageBox.information(self, "CSV exportado", f"Arquivo salvo em:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao exportar", str(exc))

    @staticmethod
    def _date_value(widget: QDateEdit) -> str:
        if widget.date() == widget.minimumDate():
            return ""
        return widget.date().toString("yyyy-MM-dd")
