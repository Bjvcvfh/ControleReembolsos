from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.catalog_service import CatalogService
from ui.dialogs.name_dialog import NameDialog


class DriversPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.catalog = CatalogService()
        self.rows: list[dict] = []
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        title = QLabel("MOTORISTAS")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        actions = QHBoxLayout()
        add_btn = QPushButton("+ Cadastrar motorista")
        add_btn.clicked.connect(self.add_driver)
        self.show_inactive = QCheckBox("Mostrar inativos")
        self.show_inactive.stateChanged.connect(self.refresh)
        actions.addWidget(add_btn)
        actions.addWidget(self.show_inactive)
        actions.addStretch(1)
        layout.addLayout(actions)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Nome", "Status", "Ação"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

    def refresh(self) -> None:
        self.rows = self.catalog.list_drivers(include_inactive=self.show_inactive.isChecked())
        self.table.setRowCount(0)
        for data in self.rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(data["nome"]))
            status = QTableWidgetItem("Ativo" if data["ativo"] else "Inativo")
            status.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, status)
            edit_btn = QPushButton("Editar")
            edit_btn.clicked.connect(lambda _, item=data: self.edit_driver(item))
            self.table.setCellWidget(row, 2, edit_btn)
        self.table.resizeColumnsToContents()

    def add_driver(self) -> None:
        dialog = NameDialog("Cadastrar motorista", "Nome:", parent=self)
        if dialog.exec():
            try:
                self.catalog.create_driver(dialog.value())
                self.refresh()
            except Exception as exc:
                QMessageBox.critical(self, "Erro", str(exc))

    def edit_driver(self, data: dict) -> None:
        dialog = NameDialog("Editar motorista", "Nome:", data["nome"], self)
        if dialog.exec():
            active = QMessageBox.question(
                self,
                "Status",
                "Manter motorista ativo?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes if data["ativo"] else QMessageBox.No,
            ) == QMessageBox.Yes
            try:
                self.catalog.update_driver(int(data["id"]), dialog.value(), active)
                self.refresh()
            except Exception as exc:
                QMessageBox.critical(self, "Erro", str(exc))
