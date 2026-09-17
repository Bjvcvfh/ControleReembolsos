from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from services.catalog_service import CatalogService
from services.pdf_service import generate_reimbursement_pdf
from services.reimbursement_service import ReimbursementService
from ui.dialogs.name_dialog import NameDialog
from utils.currency import format_brl_from_cents, parse_brl_to_cents


ROW_GRID_SPACING = 8
NEW_SERVICE_BUTTON_WIDTH = 104
REMOVE_BUTTON_WIDTH = 72


class ServiceRow(QWidget):
    changed = Signal()
    remove_requested = Signal(object)
    new_service_requested = Signal(object)

    def __init__(self, services: list[dict], parent=None):
        super().__init__(parent)
        self.services = services
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(ROW_GRID_SPACING)
        layout.setColumnStretch(0, 4)
        layout.setColumnStretch(1, 2)
        layout.setColumnStretch(2, 2)
        layout.setColumnStretch(3, 2)
        layout.setColumnStretch(4, 2)

        self.service_combo = QComboBox()
        self.service_combo.setEditable(True)
        self.service_combo.setInsertPolicy(QComboBox.NoInsert)
        self.plate_edit = QLineEdit()
        self.plate_edit.setPlaceholderText("Opcional")
        self.plate_edit.setMaxLength(8)
        self.os_edit = QLineEdit()
        self.os_edit.setPlaceholderText("Opcional")
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setDate(QDate.currentDate())
        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText("R$ 0,00")
        self.value_edit.editingFinished.connect(self._format_value)
        self.value_edit.textChanged.connect(self.changed.emit)

        self.new_service_btn = QPushButton("+ Novo tipo")
        self.new_service_btn.setFixedWidth(NEW_SERVICE_BUTTON_WIDTH)
        self.new_service_btn.clicked.connect(lambda: self.new_service_requested.emit(self))
        self.remove_btn = QPushButton("Excluir")
        self.remove_btn.setObjectName("dangerButton")
        self.remove_btn.setFixedWidth(REMOVE_BUTTON_WIDTH)
        self.remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))

        layout.addWidget(self.service_combo, 0, 0)
        layout.addWidget(self.date_edit, 0, 1)
        layout.addWidget(self.plate_edit, 0, 2)
        layout.addWidget(self.os_edit, 0, 3)
        layout.addWidget(self.value_edit, 0, 4)
        layout.addWidget(self.new_service_btn, 0, 5)
        layout.addWidget(self.remove_btn, 0, 6)
        self.reload_services(services)

    def reload_services(self, services: list[dict], select_id: int | None = None) -> None:
        current_id = select_id or self.current_service_id()
        self.services = services
        self.service_combo.blockSignals(True)
        self.service_combo.clear()
        for service in services:
            self.service_combo.addItem(service["descricao"], service["id"])
        if current_id:
            index = self.service_combo.findData(current_id)
            if index >= 0:
                self.service_combo.setCurrentIndex(index)
        self.service_combo.blockSignals(False)

    def current_service_id(self) -> int:
        text = self.service_combo.currentText().strip().casefold()
        for service in self.services:
            if service["descricao"].strip().casefold() == text:
                return int(service["id"])
        return 0

    def value_cents(self) -> int:
        return parse_brl_to_cents(self.value_edit.text())

    def data(self) -> dict:
        return {
            "tipo_servico_id": self.current_service_id(),
            "data_servico": self.date_edit.date().toString("yyyy-MM-dd"),
            "placa": self.plate_edit.text().strip(),
            "os": self.os_edit.text().strip(),
            "valor_centavos": self.value_cents(),
        }

    def _format_value(self) -> None:
        cents = self.value_cents()
        self.value_edit.setText(format_brl_from_cents(cents) if cents else "")
        self.changed.emit()


class ReimbursementPage(QWidget):
    saved = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.catalog = CatalogService()
        self.reimbursement_service = ReimbursementService()
        self.driver_cache: list[dict] = []
        self.service_cache: list[dict] = []
        self.rows: list[ServiceRow] = []
        self._build_ui()
        self.reload_catalogs()
        self.add_row()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        title = QLabel("NOVO REEMBOLSO")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        driver_row = QHBoxLayout()
        driver_row.addWidget(QLabel("Motorista:"))
        self.driver_combo = QComboBox()
        self.driver_combo.setEditable(True)
        self.driver_combo.setInsertPolicy(QComboBox.NoInsert)
        self.driver_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        driver_row.addWidget(self.driver_combo, 1)
        self.new_driver_btn = QPushButton("+ Novo motorista")
        self.new_driver_btn.clicked.connect(self.add_driver_inline)
        driver_row.addWidget(self.new_driver_btn)
        layout.addLayout(driver_row)

        header = QGridLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setHorizontalSpacing(ROW_GRID_SPACING)
        header.setColumnStretch(0, 4)
        header.setColumnStretch(1, 2)
        header.setColumnStretch(2, 2)
        header.setColumnStretch(3, 2)
        header.setColumnStretch(4, 2)
        header.setColumnStretch(5, 0)
        header.setColumnStretch(6, 0)
        header.addWidget(self._header_label("Tipo de Serviço"), 0, 0)
        header.addWidget(self._header_label("Data"), 0, 1)
        header.addWidget(self._header_label("Placa"), 0, 2)
        header.addWidget(self._header_label("O.S"), 0, 3)
        header.addWidget(self._header_label("Valor"), 0, 4)
        new_service_spacer = QWidget()
        new_service_spacer.setFixedWidth(NEW_SERVICE_BUTTON_WIDTH)
        remove_spacer = QWidget()
        remove_spacer.setFixedWidth(REMOVE_BUTTON_WIDTH)
        header.addWidget(new_service_spacer, 0, 5)
        header.addWidget(remove_spacer, 0, 6)
        layout.addLayout(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.rows_container = QWidget()
        self.rows_layout = QVBoxLayout(self.rows_container)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(8)
        self.rows_layout.addStretch(1)
        self.scroll.setWidget(self.rows_container)
        layout.addWidget(self.scroll, 1)

        actions = QHBoxLayout()
        add_btn = QPushButton("+ Adicionar serviço")
        add_btn.clicked.connect(self.add_row)
        actions.addWidget(add_btn)
        actions.addStretch(1)
        layout.addLayout(actions)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        layout.addWidget(divider)

        bottom = QHBoxLayout()
        self.total_label = QLabel("TOTAL DO REEMBOLSO: R$ 0,00")
        self.total_label.setObjectName("totalLabel")
        bottom.addWidget(self.total_label)
        bottom.addStretch(1)
        save_btn = QPushButton("SALVAR REEMBOLSO")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.save_reimbursement)
        bottom.addWidget(save_btn)
        layout.addLayout(bottom)

    def _header_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        return label

    def reload_catalogs(self) -> None:
        self.driver_cache = self.catalog.list_drivers()
        self.service_cache = self.catalog.list_service_types()
        current_driver = self.current_driver_id()
        self.driver_combo.clear()
        for driver in self.driver_cache:
            self.driver_combo.addItem(driver["nome"], driver["id"])
        if current_driver:
            index = self.driver_combo.findData(current_driver)
            if index >= 0:
                self.driver_combo.setCurrentIndex(index)
        for row in self.rows:
            row.reload_services(self.service_cache)

    def current_driver_id(self) -> int:
        text = self.driver_combo.currentText().strip().casefold()
        for driver in self.driver_cache:
            if driver["nome"].strip().casefold() == text:
                return int(driver["id"])
        return 0

    def add_row(self) -> None:
        row = ServiceRow(self.service_cache)
        row.changed.connect(self.update_total)
        row.remove_requested.connect(self.remove_row)
        row.new_service_requested.connect(self.add_service_inline)
        self.rows_layout.insertWidget(self.rows_layout.count() - 1, row)
        self.rows.append(row)
        self.update_total()

    def remove_row(self, row: ServiceRow) -> None:
        if len(self.rows) == 1:
            row.value_edit.clear()
            row.plate_edit.clear()
            row.os_edit.clear()
            self.update_total()
            return
        self.rows.remove(row)
        row.deleteLater()
        self.update_total()

    def add_driver_inline(self) -> None:
        dialog = NameDialog("Novo motorista", "Nome:", parent=self)
        if dialog.exec():
            try:
                driver_id = self.catalog.create_driver(dialog.value())
                self.reload_catalogs()
                index = self.driver_combo.findData(driver_id)
                if index >= 0:
                    self.driver_combo.setCurrentIndex(index)
            except Exception as exc:
                QMessageBox.critical(self, "Erro", str(exc))

    def add_service_inline(self, source_row: ServiceRow) -> None:
        dialog = NameDialog("Novo tipo de serviço", "Descrição:", parent=self)
        if dialog.exec():
            try:
                service_id = self.catalog.create_service_type(dialog.value())
                self.service_cache = self.catalog.list_service_types()
                for row in self.rows:
                    row.reload_services(self.service_cache, service_id if row is source_row else None)
            except Exception as exc:
                QMessageBox.critical(self, "Erro", str(exc))

    def update_total(self) -> None:
        total = sum(row.value_cents() for row in self.rows)
        self.total_label.setText(f"TOTAL DO REEMBOLSO: {format_brl_from_cents(total)}")

    def _validate(self) -> list[dict]:
        if not self.current_driver_id():
            raise ValueError("Selecione um motorista.")
        items = [row.data() for row in self.rows]
        valid_items = [
            item
            for item in items
            if item["tipo_servico_id"] or item["valor_centavos"] or item["placa"] or item["os"]
        ]
        if not valid_items:
            raise ValueError("Adicione pelo menos um serviço.")
        for item in valid_items:
            if not item["tipo_servico_id"]:
                raise ValueError("Todos os serviços precisam de tipo.")
            if item["valor_centavos"] <= 0:
                raise ValueError("Todos os serviços precisam de valor maior que zero.")
        return valid_items

    def save_reimbursement(self) -> None:
        try:
            items = self._validate()
            reimbursement = self.reimbursement_service.create_reimbursement(
                self.current_driver_id(),
                items,
            )
        except Exception as exc:
            QMessageBox.warning(self, "Atenção", str(exc))
            return

        try:
            pdf_path = generate_reimbursement_pdf(reimbursement)
            self.reimbursement_service.set_pdf_path(reimbursement["id"], str(pdf_path))
            QMessageBox.information(
                self,
                "Reembolso salvo",
                f"Reembolso {reimbursement['numero']} salvo com sucesso.\nPDF salvo em:\n{pdf_path}",
            )
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Reembolso salvo sem PDF",
                f"O reembolso {reimbursement['numero']} foi salvo, mas houve erro ao gerar o PDF:\n{exc}\n\n"
                "Use o Histórico para gerar novamente.",
            )
        self.clear_form()
        self.saved.emit()

    def clear_form(self) -> None:
        for row in list(self.rows):
            row.deleteLater()
        self.rows = []
        self.add_row()
        self.update_total()
