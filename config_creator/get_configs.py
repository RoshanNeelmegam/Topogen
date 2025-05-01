from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
import yaml
from jinja2 import Template
import sys

def get_device_configs(yaml_file, jinja_template):
    # Load YAML and template
    with open(yaml_file) as f:
        yaml_data = yaml.safe_load(f)

    with open(jinja_template) as f:
        loaded_jinja_template = f.read()

    jinja_template_object = Template(loaded_jinja_template, trim_blocks=True)
    rendered_output = jinja_template_object.render(yaml_data)

    # Create and show the popup dialog
    app = QApplication.instance() or QApplication(sys.argv)
    dialog = QDialog()
    dialog.setWindowTitle("Rendered Configuration")

    layout = QVBoxLayout(dialog)
    text_edit = QTextEdit()
    text_edit.setText(rendered_output)
    layout.addWidget(text_edit)

    button_layout = QHBoxLayout()
    copy_button = QPushButton("Copy")
    cancel_button = QPushButton("Cancel")
    button_layout.addWidget(copy_button)
    button_layout.addWidget(cancel_button)
    layout.addLayout(button_layout)

    copy_button.clicked.connect(lambda: QApplication.clipboard().setText(text_edit.toPlainText()))
    cancel_button.clicked.connect(dialog.reject)

    dialog.setLayout(layout)
    dialog.resize(600, 500)
    dialog.exec()
