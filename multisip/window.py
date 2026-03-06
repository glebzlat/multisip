from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QMainWindow, QPushButton


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("MultiSIP")
        self.setGeometry(300, 300, 300, 220)
        self.setMinimumSize(QSize(400, 300))

        button = QPushButton("Press Me!")
        button.setCheckable(True)
        button.clicked.connect(self.handle_button_clicked)
        button.clicked.connect(self.handle_button_toggled)

        self.setCentralWidget(button)

    def handle_button_clicked(self):
        print("The button was clicked")

    def handle_button_toggled(self, checked):
        print(f"The button was checked: {checked}")
