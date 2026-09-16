from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QMessageBox, QVBoxLayout


class NameDialog(QDialog):
    def __init__(self, title: str, label: str, initial_value: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name_edit = QLineEdit(initial_value)
        form.addRow(label, self.name_edit)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _accept(self) -> None:
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Atenção", "Informe um nome/descrição.")
            return
        self.accept()

    def value(self) -> str:
        return self.name_edit.text().strip()
