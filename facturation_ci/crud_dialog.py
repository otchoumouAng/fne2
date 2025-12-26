from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QDialogButtonBox, QLineEdit, QTextEdit, QLabel
from core.theme import STYLESHEET

class CrudDialog(QDialog):
    def __init__(self, mode, fields_config, title, data=None, parent=None, read_only=False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setStyleSheet(STYLESHEET)
        self.fields_config = fields_config
        self.widgets = {}
        self.read_only = read_only

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        for field in self.fields_config:
            field_name = field['name']
            label = field['label']
            field_type = field.get('type', 'QLineEdit')

            if field_type == 'QLineEdit':
                widget = QLineEdit()
            elif field_type == 'QTextEdit':
                widget = QTextEdit()
            else:
                widget = QLineEdit() # Default

            if data and field_name in data:
                widget.setText(str(data[field_name]))

            if self.read_only:
                widget.setEnabled(False)

            self.widgets[field_name] = widget
            form_layout.addRow(label, widget)

        main_layout.addLayout(form_layout)

        if self.read_only:
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        else:
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def get_data(self):
        data = {}
        for field_name, widget in self.widgets.items():
            if isinstance(widget, QLineEdit):
                data[field_name] = widget.text()
            elif isinstance(widget, QTextEdit):
                data[field_name] = widget.toPlainText()
        return data
