from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor, Qt
from core.gui_window import GuiWindow

def force_light_theme(app):
    palette = QPalette()
    # setting all components to white
    palette.setColor(QPalette.Window, QColor("#ffffff"))
    palette.setColor(QPalette.Base, QColor("#ffffff"))
    palette.setColor(QPalette.WindowText, Qt.black)
    palette.setColor(QPalette.Text, Qt.black)
    palette.setColor(QPalette.Button, QColor("#f0f0f0"))
    palette.setColor(QPalette.ButtonText, Qt.black)
    palette.setColor(QPalette.Highlight, QColor("#0078d7"))
    palette.setColor(QPalette.HighlightedText, Qt.white)
    app.setPalette(palette)
    app.setStyle("Fusion") 

app = QApplication([])
gui_window = GuiWindow()
gui_window.show()
force_light_theme(app)
app.setStyleSheet("""
    QMainWindow, QWidget, QDialog {
        background-color: white;
        color: black;
    }
""")
app.exec()