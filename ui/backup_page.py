from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from services.backup_service import BackupService
from utils.paths import database_path, downloads_dir


class BackupPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = BackupService()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        title = QLabel("BACKUP")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        info = QLabel(
            f"Banco atual:\n{database_path()}\n\n"
            "Use o backup antes de trocar de computador ou antes de alterações importantes."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        backup_btn = QPushButton("Fazer Backup")
        backup_btn.clicked.connect(self.backup)
        restore_btn = QPushButton("Restaurar Backup")
        restore_btn.setObjectName("dangerButton")
        restore_btn.clicked.connect(self.restore)
        layout.addWidget(backup_btn)
        layout.addWidget(restore_btn)
        layout.addStretch(1)

    def backup(self) -> None:
        default = downloads_dir() / f"backup_reembolsos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        path, _ = QFileDialog.getSaveFileName(self, "Salvar backup", str(default), "SQLite (*.db)")
        if not path:
            return
        try:
            self.service.backup_to(Path(path))
            QMessageBox.information(self, "Backup concluído", f"Backup salvo em:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Erro no backup", str(exc))

    def restore(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar backup", "", "SQLite (*.db);;Todos (*.*)")
        if not path:
            return
        confirm = QMessageBox.question(
            self,
            "Confirmar restauração",
            "A restauração substituirá os dados atuais. Deseja continuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return
        try:
            self.service.restore_from(Path(path))
            QMessageBox.information(self, "Backup restaurado", "Backup restaurado com sucesso. Reinicie o aplicativo.")
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao restaurar", str(exc))
