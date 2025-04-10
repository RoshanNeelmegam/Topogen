from PySide6.QtWidgets import QApplication
from gui_window import GuiWindow

app = QApplication([])
gui_window = GuiWindow()
gui_window.show()
app.exec()