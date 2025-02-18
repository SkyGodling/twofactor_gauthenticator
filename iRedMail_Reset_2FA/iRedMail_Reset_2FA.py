import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
import mysql.connector
from mysql.connector import Error

def resource_path(relative_path):
    """ Lấy đường dẫn file khi đã đóng gói .exe """
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

twofactor_data = None
original_preferences = None

def fetch_authenticator():
    global twofactor_data, original_preferences

    host = ''
    database = ''
    user = ''
    password = ''
    username = username_entry.text()

    if not username:
        QMessageBox.warning(window, "Cảnh báo", "Vui lòng nhập tên người dùng")
        return

    try:
        connection = mysql.connector.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )

        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            sql_select_query = """SELECT preferences FROM users WHERE username = %s"""
            cursor.execute(sql_select_query, (username,))
            record = cursor.fetchone()

            if record:
                preferences = record["preferences"]
                original_preferences = preferences
                start = preferences.find('"twofactor_gauthenticator";')
                if start != -1:
                    end = preferences.find('}}}', start) + 3
                    twofactor_authenticator = preferences[start:end]
                    result_text.clear()
                    result_text.append(twofactor_authenticator)

                    twofactor_data = parse_twofactor_authenticator(twofactor_authenticator)
                else:
                    QMessageBox.information(window, "Thông tin", "Không tìm thấy Twofactor Gauthenticator")
            else:
                QMessageBox.information(window, "Thông tin", "Không tìm thấy người dùng")

    except Error as e:
        QMessageBox.critical(window, "Lỗi", f"Lỗi kết nối MySQL: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def parse_twofactor_authenticator(authenticator):
    data = {}
    try:
        data["secret"] = authenticator.split('s:6:"secret";s:16:"')[1].split('";')[0]
        data["activate"] = authenticator.split('s:8:"activate";b:')[1].split(';')[0] == '1'
        recovery_codes_part = authenticator.split('s:14:"recovery_codes";a:')[1]
        codes = []
        for i in range(4):
            codes.append(recovery_codes_part.split(f'i:{i};s:10:"')[1].split('";')[0])
        data["recovery_codes"] = codes
    except IndexError:
        QMessageBox.critical(window, "Lỗi", "Lỗi phân tích dữ liệu Twofactor Gauthenticator")
    return data

def show_secret():
    if twofactor_data:
        QMessageBox.information(window, "Secret", twofactor_data["secret"])

def show_recovery_codes():
    if twofactor_data:
        codes = "\n".join(twofactor_data["recovery_codes"])
        QMessageBox.information(window, "Recovery Codes", codes)

def update_2fa_status(activate):
    global original_preferences, twofactor_data
    username = username_entry.text()
    if not username:
        QMessageBox.warning(window, "Cảnh báo", "Vui lòng nhập tên người dùng")
        return

    if not twofactor_data:
        QMessageBox.warning(window, "Cảnh báo", "Vui lòng lấy mã Google Authenticator trước khi thực hiện thao tác này")
        return

    try:
        host = ''
        database = ''
        user = ''
        password = ''

        connection = mysql.connector.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )

        if connection.is_connected():
            cursor = connection.cursor()

            new_activate = 'b:1' if activate else 'b:0'
            updated_preferences = original_preferences.replace(
                f's:8:"activate";b:{1 if twofactor_data["activate"] else 0}', 
                f's:8:"activate";{new_activate}'
            )

            sql_update_query = """UPDATE users SET preferences = %s WHERE username = %s"""
            cursor.execute(sql_update_query, (updated_preferences, username))
            connection.commit()

            twofactor_data["activate"] = activate
            QMessageBox.information(window, "Thông tin", f"2FA đã được {'kích hoạt' if activate else 'vô hiệu hóa'}")

    except Error as e:
        QMessageBox.critical(window, "Lỗi", f"Lỗi kết nối MySQL: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def activate_2fa():
    fetch_authenticator()
    update_2fa_status(True)

def disable_2fa():
    fetch_authenticator()
    update_2fa_status(False)

app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle("Google Authenticator Reset Tools")

# Set icon từ file đã nhúng
window.setWindowIcon(QIcon(resource_path("monero.ico")))

central_widget = QWidget()
window.setCentralWidget(central_widget)

layout = QVBoxLayout(central_widget)

banner_label = QLabel("Google Authenticator Reset Tools")
banner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
banner_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #34495E; margin-bottom: 20px;")
layout.addWidget(banner_label)

username_entry = QLineEdit()
username_entry.setPlaceholderText("Định dạng: user@domain.com")
username_entry.setStyleSheet("background-color: #ffffff; border: 1px solid #BDC3C7; border-radius: 5px; padding: 14px; font-size: 16px;")
layout.addWidget(QLabel("Tên người dùng hoặc tài khoản email."))
layout.addWidget(username_entry)

result_text = QTextEdit()
result_text.setStyleSheet("background-color: #ffffff; border: 1px solid #BDC3C7; border-radius: 5px; padding: 10px; font-size: 14px;")
layout.addWidget(result_text)

button_layout = QHBoxLayout()

activate_button = QPushButton("Kích hoạt Google 2FA")
activate_button.setFixedSize(180, 40)
activate_button.setStyleSheet("background-color: #27ae60; color: white; border-radius: 5px; font-size: 14px;")
activate_button.clicked.connect(activate_2fa)
button_layout.addWidget(activate_button)

disable_button = QPushButton("Vô hiệu hóa Google 2FA")
disable_button.setFixedSize(180, 40)
disable_button.setStyleSheet("background-color: #e74c3c; color: white; border-radius: 5px; font-size: 14px;")
disable_button.clicked.connect(disable_2fa)
button_layout.addWidget(disable_button)

layout.addLayout(button_layout)

license_label = QLabel("License by Nguyễn Hùng Anh @2020")
license_label.setAlignment(Qt.AlignmentFlag.AlignRight)
license_label.setStyleSheet("font-size: 14px; color: #FF6600; margin-top: 20px;")
layout.addWidget(license_label)

window.setStyleSheet("background-color: #f5f5f5;")

window.show()
sys.exit(app.exec())
