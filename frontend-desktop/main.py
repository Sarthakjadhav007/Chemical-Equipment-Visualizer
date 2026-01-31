import sys
import requests
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QFileDialog, QTableWidget, QTableWidgetItem, 
                             QLabel, QListWidget, QTabWidget, QMessageBox, QLineEdit, QFormLayout, QDialog)
from PyQt5.QtCore import Qt
from requests.auth import HTTPBasicAuth

API_BASE = "http://127.0.0.1:8000/api"

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login to ChemVisualizer")
        self.layout = QFormLayout(self)
        self.username = QLineEdit(self)
        self.password = QLineEdit(self)
        self.password.setEchoMode(QLineEdit.Password)
        self.layout.addRow("Username:", self.username)
        self.layout.addRow("Password:", self.password)
        self.buttons = QHBoxLayout()
        self.login_btn = QPushButton("Login", self)
        self.login_btn.clicked.connect(self.accept)
        self.buttons.addWidget(self.login_btn)
        self.layout.addRow(self.buttons)

    def get_credentials(self):
        return self.username.text(), self.password.text()

class MplsCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        # Use dark style for matplotlib to match web design better
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi)
        self.fig.patch.set_facecolor('#1e1e1e')
        self.ax.set_facecolor('#1e1e1e')
        super(MplsCanvas, self).__init__(self.fig)

class EquipmentVisualizerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chemical Equipment Parameter Visualizer")
        self.resize(1100, 800)
        self.setStyleSheet("""
            QMainWindow { background-color: #121212; }
            QWidget { color: #e0e0e0; font-family: 'Segoe UI'; }
            QTabWidget::pane { border: 1px solid #333; background: #1e1e1e; }
            QTabBar::tab { background: #2d2d2d; padding: 10px 20px; border: 1px solid #333; }
            QTabBar::tab:selected { background: #4f46e5; color: white; }
            QPushButton { background-color: #4f46e5; border-radius: 5px; padding: 8px; color: white; font-weight: bold; }
            QPushButton:hover { background-color: #6366f1; }
            QPushButton:disabled { background-color: #333; color: #777; }
            QTableWidget { background-color: #1e1e1e; gridline-color: #333; border: none; }
            QHeaderView::section { background-color: #2d2d2d; padding: 5px; border: 1px solid #333; color: #94a3b8; }
            QLineEdit { background-color: #2d2d2d; border: 1px solid #444; padding: 5px; border-radius: 3px; }
            QListWidget { background-color: #1e1e1e; border: 1px solid #333; }
            QListWidget::item { padding: 10px; border-bottom: 1px solid #2d2d2d; }
            QListWidget::item:hover { background: #2d2d2d; }
        """)
        
        self.auth = None
        self.current_dataset_id = None
        self.full_data = [] # For local searching

        # Login First
        if not self.show_login():
            sys.exit()

        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)
        
        # Tabs
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        # Dashboard Tab
        self.dash_tab = QWidget()
        self.dash_layout = QVBoxLayout(self.dash_tab)
        
        # Top Controls
        top_ctrl = QHBoxLayout()
        self.upload_btn = QPushButton("Upload CSV File")
        self.upload_btn.clicked.connect(self.upload_csv)
        top_ctrl.addWidget(self.upload_btn)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search equipment by name or type...")
        self.search_input.textChanged.connect(self.filter_table)
        top_ctrl.addWidget(self.search_input)
        
        self.dash_layout.addLayout(top_ctrl)
        
        # Stats Labels
        self.stats_label = QLabel("Summary Statistics will appear here.")
        self.stats_label.setStyleSheet("font-size: 14px; color: #818cf8; font-weight: bold; margin: 10px 0;")
        self.dash_layout.addWidget(self.stats_label)
        
        # Table
        self.table = QTableWidget()
        self.dash_layout.addWidget(self.table)
        
        # Charts Section (Horizontal)
        self.charts_widget = QWidget()
        self.charts_layout = QHBoxLayout(self.charts_widget)
        self.canvas_dist = MplsCanvas(self, width=5, height=4, dpi=100)
        self.canvas_params = MplsCanvas(self, width=5, height=4, dpi=100)
        self.charts_layout.addWidget(self.canvas_dist)
        self.charts_layout.addWidget(self.canvas_params)
        self.dash_layout.addWidget(self.charts_widget)
        
        self.tabs.addTab(self.dash_tab, "Dashboard")
        
        # History Tab
        self.history_tab = QWidget()
        self.history_layout = QVBoxLayout(self.history_tab)
        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self.load_history_item)
        self.history_layout.addWidget(QLabel("Recent Uploads (Last 5)"))
        self.history_layout.addWidget(self.history_list)
        self.refresh_history_btn = QPushButton("Refresh History")
        self.refresh_history_btn.clicked.connect(self.fetch_history)
        self.history_layout.addWidget(self.refresh_history_btn)
        
        self.tabs.addTab(self.history_tab, "History")
        
        # Footer
        self.pdf_btn = QPushButton("Download PDF Report")
        self.pdf_btn.clicked.connect(self.download_pdf)
        self.pdf_btn.setEnabled(False)
        self.layout.addWidget(self.pdf_btn)
        
        self.fetch_history()

    def show_login(self):
        dialog = LoginDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            u, p = dialog.get_credentials()
            self.auth = HTTPBasicAuth(u, p)
            return True
        return False

    def upload_csv(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file', '', "CSV files (*.csv)")
        if fname:
            # Create a simple processing message box
            progress = QMessageBox(self)
            progress.setWindowTitle("Processing")
            progress.setText("Calculating the Result...")
            progress.setStandardButtons(QMessageBox.NoButton)
            progress.show()
            QApplication.processEvents() # Ensure the box shows up

            files = {'file': open(fname, 'rb')}
            try:
                response = requests.post(f"{API_BASE}/upload/", files=files, auth=self.auth)
                progress.close() # Close modern "Calculating" dialog
                if response.status_code == 201:
                    QMessageBox.information(self, "Success", "File uploaded successfully!")
                    self.fetch_summary()
                    self.fetch_history()
                elif response.status_code == 401:
                    QMessageBox.warning(self, "Error", "Authentication failed. Please check credentials.")
                else:
                    QMessageBox.warning(self, "Error", f"Upload failed: {response.text}")
            except Exception as e:
                progress.close()
                QMessageBox.critical(self, "Error", f"Connection error: {str(e)}")

    def fetch_summary(self, pk=None):
        url = f"{API_BASE}/summary/"
        if pk: url += f"{pk}/"
        
        try:
            response = requests.get(url, auth=self.auth)
            if response.status_code == 200:
                data = response.json()
                self.current_dataset_id = data['id']
                self.full_data = data['data']
                self.pdf_btn.setEnabled(True)
                self.update_ui(data)
            elif response.status_code == 401:
                QMessageBox.warning(self, "Error", "Session expired or invalid credentials.")
        except Exception as e:
            print(f"Error fetching summary: {e}")

    def update_ui(self, data):
        # Update Stats
        stats_text = (f"Dataset: {data['file_name']} | Total: {data['total_count']} | "
                    f"Flow: {data['averages']['flowrate']:.1f} | "
                    f"Press: {data['averages']['pressure']:.1f} | "
                    f"Temp: {data['averages']['temperature']:.1f}")
        self.stats_label.setText(stats_text)
        
        self.populate_table(self.full_data)
            
        # Update Charts
        # 1. Type Distribution (Pie)
        self.canvas_dist.ax.clear()
        types = list(data['type_distribution'].keys())
        counts = list(data['type_distribution'].values())
        self.canvas_dist.ax.pie(counts, labels=types, autopct='%1.1f%%', colors=plt.cm.Paired.colors)
        self.canvas_dist.ax.set_title("Equipment Type Distribution", color='white')
        self.canvas_dist.draw()
        
        # 2. Avg Parameters (Bar)
        self.canvas_params.ax.clear()
        params = ['Flowrate', 'Pressure', 'Temp']
        vals = [data['averages']['flowrate'], data['averages']['pressure'], data['averages']['temperature']]
        self.canvas_params.ax.bar(params, vals, color=['#6366f1', '#10b981', '#f59e0b'])
        self.canvas_params.ax.set_title("Average Parameters", color='white')
        self.canvas_params.draw()

    def populate_table(self, items):
        self.table.setRowCount(len(items))
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['Name', 'Type', 'Flowrate', 'Pressure', 'Temperature'])
        for i, item in enumerate(items):
            self.table.setItem(i, 0, QTableWidgetItem(str(item['name'])))
            self.table.setItem(i, 1, QTableWidgetItem(str(item['type'])))
            self.table.setItem(i, 2, QTableWidgetItem(str(item['flowrate'])))
            self.table.setItem(i, 3, QTableWidgetItem(str(item['pressure'])))
            self.table.setItem(i, 4, QTableWidgetItem(str(item['temperature'])))

    def filter_table(self):
        term = self.search_input.text().lower()
        filtered = [i for i in self.full_data if term in i['name'].lower() or term in i['type'].lower()]
        self.populate_table(filtered)

    def fetch_history(self):
        try:
            response = requests.get(f"{API_BASE}/history/", auth=self.auth)
            if response.status_code == 200:
                self.history_list.clear()
                self.history_data = response.json()
                for item in self.history_data:
                    self.history_list.addItem(f"{item['file_name']} - {item['uploaded_at']}")
        except Exception as e:
            print(f"Error fetching history: {e}")

    def load_history_item(self, item):
        idx = self.history_list.currentRow()
        dataset_id = self.history_data[idx]['id']
        self.fetch_summary(dataset_id)
        self.tabs.setCurrentIndex(0)

    def download_pdf(self):
        if not self.current_dataset_id: return
        url = f"{API_BASE}/pdf/{self.current_dataset_id}/"
        try:
            response = requests.get(url, auth=self.auth)
            if response.status_code == 200:
                path, _ = QFileDialog.getSaveFileName(self, "Save PDF Report", f"report_{self.current_dataset_id}.pdf", "PDF files (*.pdf)")
                if path:
                    with open(path, 'wb') as f:
                        f.write(response.content)
                    QMessageBox.information(self, "Success", "PDF Report saved!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to download PDF: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EquipmentVisualizerApp()
    window.show()
    sys.exit(app.exec_())
