from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui.backup_page import BackupPage
from ui.drivers_page import DriversPage
from ui.history_page import HistoryPage
from ui.reimbursement_page import ReimbursementPage
from ui.service_types_page import ServiceTypesPage
from utils.paths import resource_path


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Controle de Reembolsos")
        self.setMinimumSize(1120, 720)
        self.logo_icon = QIcon(resource_path("assets/app.ico"))
        if not self.logo_icon.isNull():
            self.setWindowIcon(self.logo_icon)
        self._build_ui()
        self._apply_style()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(18, 20, 18, 18)

        brand = QHBoxLayout()
        brand.setSpacing(10)
        logo = QLabel()
        logo.setObjectName("brandLogo")
        if not self.logo_icon.isNull():
            logo.setPixmap(self.logo_icon.pixmap(38, 38))
        logo.setFixedSize(42, 42)
        logo.setAlignment(Qt.AlignCenter)
        brand.addWidget(logo)

        app_title = QLabel("CONTROLE\nDE REEMBOLSOS")
        app_title.setObjectName("appTitle")
        brand.addWidget(app_title, 1)
        side_layout.addLayout(brand)

        nav_label = QLabel("MENU")
        nav_label.setObjectName("navLabel")
        side_layout.addWidget(nav_label)

        self.nav = QListWidget()
        self.nav.setObjectName("navList")
        for text in ["Novo Reembolso", "Histórico", "Motoristas", "Tipos Serviço", "Backup"]:
            item = QListWidgetItem(text)
            item.setTextAlignment(Qt.AlignVCenter)
            self.nav.addItem(item)
        self.nav.currentRowChanged.connect(self._change_page)
        side_layout.addWidget(self.nav, 1)
        root.addWidget(sidebar)

        self.stack = QStackedWidget()
        self.reimbursement_page = ReimbursementPage()
        self.history_page = HistoryPage()
        self.drivers_page = DriversPage()
        self.service_types_page = ServiceTypesPage()
        self.backup_page = BackupPage()
        self.stack.addWidget(self.reimbursement_page)
        self.stack.addWidget(self.history_page)
        self.stack.addWidget(self.drivers_page)
        self.stack.addWidget(self.service_types_page)
        self.stack.addWidget(self.backup_page)
        root.addWidget(self.stack, 1)

        self.reimbursement_page.saved.connect(self.history_page.refresh)
        self.nav.setCurrentRow(0)

    def _change_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        if index == 0:
            self.reimbursement_page.reload_catalogs()
        elif index == 1:
            self.history_page.reload_service_filter()
            self.history_page.refresh()
        elif index == 2:
            self.drivers_page.refresh()
        elif index == 3:
            self.service_types_page.refresh()

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #f6f7f4;
                color: #24312f;
                font-family: Segoe UI;
                font-size: 13px;
            }
            #sidebar {
                background: #243733;
                border-right: 1px solid #d9ded8;
            }
            #brandLogo {
                background: #f4f1e8;
                border: 1px solid #d8d0bf;
                border-radius: 8px;
            }
            #appTitle {
                background: transparent;
                color: #ffffff;
                font-size: 17px;
                font-weight: 700;
                letter-spacing: 0px;
                padding-bottom: 2px;
            }
            #navLabel {
                background: transparent;
                color: #9db0a9;
                font-size: 11px;
                font-weight: 700;
                padding: 24px 0 7px 4px;
            }
            #navList {
                background: transparent;
                border: none;
                color: #dce5df;
                outline: none;
            }
            #navList::item {
                border-radius: 7px;
                padding: 12px 11px;
                margin: 2px 0;
            }
            #navList::item:selected {
                background: #dfece4;
                color: #173a32;
                font-weight: 700;
            }
            #navList::item:hover {
                background: #324a44;
                color: #ffffff;
            }
            #pageTitle {
                font-size: 23px;
                font-weight: 700;
                padding: 20px 22px 10px 22px;
                color: #1d2c29;
            }
            QStackedWidget > QWidget {
                padding: 14px 22px 22px 22px;
            }
            QLineEdit, QComboBox, QDateEdit {
                background: #ffffff;
                border: 1px solid #cfd7d0;
                border-radius: 6px;
                padding: 8px;
                min-height: 20px;
                selection-background-color: #2f7d68;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
                border: 1px solid #2f7d68;
            }
            QTableWidget {
                background: #ffffff;
                alternate-background-color: #f7faf7;
                border: 1px solid #d9ded8;
                border-radius: 6px;
                gridline-color: #e4e8e2;
                selection-background-color: #dfece4;
                selection-color: #173a32;
            }
            QHeaderView::section {
                background: #edf2ed;
                color: #263b35;
                padding: 8px;
                border: none;
                font-weight: 700;
            }
            QPushButton {
                background: #52635d;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 9px 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #42534d;
            }
            #primaryButton {
                background: #23846f;
                min-width: 190px;
                min-height: 38px;
                font-size: 14px;
            }
            #primaryButton:hover {
                background: #1c6c5b;
            }
            #dangerButton {
                background: #b24a3b;
            }
            #dangerButton:hover {
                background: #913b30;
            }
            #totalLabel, #detailTotal {
                color: #1b3f37;
                font-size: 22px;
                font-weight: 800;
                padding: 10px 0;
            }
            QFrame[frameShape="4"], QFrame[frameShape="5"] {
                color: #d9ded8;
            }
            QCheckBox {
                spacing: 7px;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            """
        )
