import toml
import datetime
from openai import OpenAI
from PySide6.QtWidgets import (
    QApplication, QVBoxLayout, QLineEdit, QTextEdit, QPushButton, QWidget,
    QLabel, QMenuBar, QMenu, QDialog, QDialogButtonBox, QFormLayout, QSpinBox, QDoubleSpinBox
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QThread, Signal

# Load configuration
config_file = 'settings.toml'
config = toml.load(config_file)
openai_api_key = config.get('apikey', '')

# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)
aimodel = "gpt-4"

# Default parameters
max_tokens = config.get('max_tokens', 420)
top_p = config.get('top_p', 0.69)

# Function to query the AI model
def queryai(msg):
    msgs = [{"role": "user", "content": msg}]
    cc = client.chat.completions.create(
        messages=msgs, stream=True, max_tokens=max_tokens, top_p=top_p, model=aimodel
    )
    reply1 = ''
    for ck in cc:
        reply1 += (ck.choices[0].delta.content or "")
    
    # Save the response with a timestamp
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M%S")
    with open(f"reply_{timestamp}.txt", "w") as f:
        f.write(reply1)
    
    return reply1

# Function to get available models
def get_available_models():
    models = client.models.list()
    return [model.id for model in models]

class QueryThread(QThread):
    result = Signal(str)

    def __init__(self, msg):
        super().__init__()
        self.msg = msg

    def run(self):
        response = queryai(self.msg)
        self.result.emit(response)

class ModelInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Available Models")
        self.setGeometry(300, 300, 400, 300)

        layout = QVBoxLayout()

        models = get_available_models()
        model_info = "\n".join(models)

        self.model_label = QLabel(model_info)
        self.model_label.setWordWrap(True)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)

        layout.addWidget(self.model_label)
        layout.addWidget(button_box)

        self.setLayout(layout)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setGeometry(300, 300, 400, 250)

        layout = QFormLayout()

        self.api_key_edit = QLineEdit(self)
        self.api_key_edit.setText(openai_api_key)

        self.max_tokens_spinbox = QSpinBox(self)
        self.max_tokens_spinbox.setRange(1, 1000)
        self.max_tokens_spinbox.setValue(max_tokens)

        self.top_p_spinbox = QDoubleSpinBox(self)
        self.top_p_spinbox.setRange(0.0, 1.0)
        self.top_p_spinbox.setSingleStep(0.01)
        self.top_p_spinbox.setValue(top_p)

        layout.addRow("API Key:", self.api_key_edit)
        layout.addRow("Max Tokens:", self.max_tokens_spinbox)
        layout.addRow("Top P:", self.top_p_spinbox)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

        self.setLayout(layout)

    def save_settings(self):
        global openai_api_key, max_tokens, top_p, client
        openai_api_key = self.api_key_edit.text()
        max_tokens = self.max_tokens_spinbox.value()
        top_p = self.top_p_spinbox.value()
        
        # Save to settings file
        config['apikey'] = openai_api_key
        config['max_tokens'] = max_tokens
        config['top_p'] = top_p
        with open(config_file, 'w') as f:
            toml.dump(config, f)

        # Update OpenAI client
        client = OpenAI(api_key=openai_api_key)

        self.accept()

# PySide6 application
class AIQueryApp(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle("AI Query Interface")
        self.setGeometry(100, 100, 800, 600)  # Set window size to 800x600

        layout = QVBoxLayout()

        self.menu_bar = QMenuBar(self)
        settings_menu = self.menu_bar.addMenu("Settings")

        model_info_action = QAction("Model Info", self)
        model_info_action.triggered.connect(self.show_model_info)
        settings_menu.addAction(model_info_action)

        edit_settings_action = QAction("Edit Settings", self)
        edit_settings_action.triggered.connect(self.show_edit_settings)
        settings_menu.addAction(edit_settings_action)

        self.input_box = QLineEdit(self)
        self.input_box.setPlaceholderText("Enter your query here")
        self.input_box.returnPressed.connect(self.handle_query)  # Connect Enter key to handle_query

        self.output_box = QTextEdit(self)
        self.output_box.setReadOnly(True)

        self.query_button = QPushButton("Query AI", self)
        self.query_button.clicked.connect(self.handle_query)

        self.spinner = QLabel(self)
        self.spinner.setAlignment(Qt.AlignCenter)
        self.spinner.hide()

        layout.addWidget(self.menu_bar)
        layout.addWidget(self.input_box)
        layout.addWidget(self.output_box)
        layout.addWidget(self.query_button)
        layout.addWidget(self.spinner)

        self.setLayout(layout)

    def handle_query(self):
        msg = self.input_box.text()
        if msg:
            self.spinner.setText("Loading...")
            self.spinner.show()
            self.query_button.setEnabled(False)
            self.query_thread = QueryThread(msg)
            self.query_thread.result.connect(self.show_result)
            self.query_thread.start()

    def show_result(self, response):
        self.output_box.setText(response)
        self.spinner.hide()
        self.query_button.setEnabled(True)

    def show_model_info(self):
        model_info_dialog = ModelInfoDialog(self)
        model_info_dialog.exec()

    def show_edit_settings(self):
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec()

if __name__ == "__main__":
    app = QApplication([])

    window = AIQueryApp()
    window.show()

    app.exec()
