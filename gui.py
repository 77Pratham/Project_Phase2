import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel
from PyQt5.QtCore import Qt
import threading

from main import process_command, speak
#from main import listen_command

class AssistantGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Assistant")
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        layout.addWidget(QLabel("Conversation:"))
        layout.addWidget(self.chat_area)

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Type your command here...")
        self.input_box.returnPressed.connect(self.send_text)
        layout.addWidget(self.input_box)

        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_text)
        layout.addWidget(self.send_btn)

        self.voice_btn = QPushButton("🎤 Voice")
        self.voice_btn.clicked.connect(self.send_voice)
        layout.addWidget(self.voice_btn)

        self.setLayout(layout)

    def update_chat(self, speaker, text):
        self.chat_area.append(f"<b>{speaker}:</b> {text}")

    def handle_command(self, command):
        if not command:
            return
        self.update_chat("You", command)
        result = process_command(command)
        self.update_chat("Assistant", result)
        speak(result)

    def send_text(self):
        command = self.input_box.text().strip()
        self.input_box.clear()
        threading.Thread(target=self.handle_command, args=(command,)).start()

    def send_voice(self):
        threading.Thread(target=self._listen_voice).start()

    """def _listen_voice(self):
        command = listen_command()
        self.handle_command(command)"""


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = AssistantGUI()
    gui.show()
    sys.exit(app.exec_())
