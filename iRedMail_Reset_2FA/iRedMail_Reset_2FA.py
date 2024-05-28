import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error
import configparser
import os

config_file = 'db_config.ini'
def load_config():
    config = configparser.ConfigParser()
    if os.path.exists(config_file):
        config.read(config_file)
        if 'DATABASE' in config:
            host_entry.insert(0, config['DATABASE'].get('host', ''))
            database_entry.insert(0, config['DATABASE'].get('database', ''))
            user_entry.insert(0, config['DATABASE'].get('user', ''))
            password_entry.insert(0, config['DATABASE'].get('password', ''))
            remember_var.set(config['DATABASE'].getboolean('remember', False))

def save_config():
    config = configparser.ConfigParser()
    config['DATABASE'] = {
        'host': host_entry.get(),
        'database': database_entry.get(),
        'user': user_entry.get(),
        'password': password_entry.get(),
        'remember': str(remember_var.get())
    }
    with open(config_file, 'w') as configfile:
        config.write(configfile)

def fetch_authenticator():
    global twofactor_data, original_preferences
    if remember_var.get():
        save_config()

    host = host_entry.get()
    database = database_entry.get()
    user = user_entry.get()
    password = password_entry.get()
    username = username_entry.get()
    
    if not username:
        messagebox.showwarning("Cảnh báo", "Vui lòng nhập tên người dùng")
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
                    result_text.delete(1.0, tk.END)
                    result_text.insert(tk.END, twofactor_authenticator)

                    # Parse twofactor_authenticator to extract details
                    twofactor_data = parse_twofactor_authenticator(twofactor_authenticator)
                else:
                    messagebox.showinfo("Thông tin", "Không tìm thấy Twofactor Gauthenticator trong preferences")
            else:
                messagebox.showinfo("Thông tin", "Không tìm thấy người dùng")

    except Error as e:
        messagebox.showerror("Lỗi", f"Lỗi kết nối MySQL: {e}")
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
        for i in range(4):  # Assuming there are always 4 codes
            codes.append(recovery_codes_part.split(f'i:{i};s:10:"')[1].split('";')[0])
        data["recovery_codes"] = codes
    except IndexError:
        messagebox.showerror("Lỗi", "Lỗi khi phân tích dữ liệu Twofactor Gauthenticator")
    return data

def show_secret():
    if twofactor_data:
        messagebox.showinfo("Secret", twofactor_data["secret"])

def show_recovery_codes():
    if twofactor_data:
        codes = "\n".join(twofactor_data["recovery_codes"])
        messagebox.showinfo("Recovery Codes", codes)

def update_2fa_status(activate):
    global original_preferences
    username = username_entry.get()
    if not username or not twofactor_data:
        return
    
    try:
        host = host_entry.get()
        database = database_entry.get()
        user = user_entry.get()
        password = password_entry.get()
        
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
            messagebox.showinfo("Thông tin", f"2FA đã được {'kích hoạt' if activate else 'vô hiệu hóa'}")

    except Error as e:
        messagebox.showerror("Lỗi", f"Lỗi kết nối MySQL: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def activate_2fa():
    update_2fa_status(True)

def disable_2fa():
    update_2fa_status(False)

root = tk.Tk()
root.title("Reset Google Authenticator (2FA)")

mainframe = ttk.Frame(root, padding="10 10 10 10")
mainframe.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
mainframe.columnconfigure(0, weight=1)
mainframe.columnconfigure(1, weight=1)

ttk.Label(mainframe, text="Host:").grid(column=0, row=0, sticky=tk.W, pady=5)
host_entry = ttk.Entry(mainframe, width=30)
host_entry.grid(column=1, row=0, sticky=(tk.W, tk.E), pady=5)

ttk.Label(mainframe, text="Database:").grid(column=0, row=1, sticky=tk.W, pady=5)
database_entry = ttk.Entry(mainframe, width=30)
database_entry.grid(column=1, row=1, sticky=(tk.W, tk.E), pady=5)

ttk.Label(mainframe, text="User:").grid(column=0, row=2, sticky=tk.W, pady=5)
user_entry = ttk.Entry(mainframe, width=30)
user_entry.grid(column=1, row=2, sticky=(tk.W, tk.E), pady=5)

ttk.Label(mainframe, text="Password:").grid(column=0, row=3, sticky=tk.W, pady=5)
password_entry = ttk.Entry(mainframe, width=30, show="*")
password_entry.grid(column=1, row=3, sticky=(tk.W, tk.E), pady=5)

remember_var = tk.BooleanVar()
remember_check = ttk.Checkbutton(mainframe, text="Remember", variable=remember_var)
remember_check.grid(column=0, row=4, columnspan=2, pady=5)

username_label = ttk.Label(mainframe, text="Tên người dùng:")
username_label.grid(column=0, row=5, sticky=tk.W, pady=5)
username_entry = ttk.Entry(mainframe, width=30)
username_entry.grid(column=1, row=5, sticky=(tk.W, tk.E), pady=5)

fetch_button = ttk.Button(mainframe, text="Lấy Mã Google Authenticator 2FA", command=fetch_authenticator)
fetch_button.grid(column=0, row=6, columnspan=2, pady=5)

result_text = tk.Text(mainframe, width=80, height=10)
result_text.grid(column=0, row=7, columnspan=2, pady=5)

button_frame = ttk.Frame(mainframe, padding="10 0 0 0")
button_frame.grid(column=0, row=8, columnspan=2, pady=10)

secret_button = ttk.Button(button_frame, text="Xuất Secret Key", command=show_secret)
secret_button.grid(column=0, row=0, padx=5)

recovery_codes_button = ttk.Button(button_frame, text="Xuất Recovery Key", command=show_recovery_codes)
recovery_codes_button.grid(column=1, row=0, padx=5)

activate_button = ttk.Button(button_frame, text="Kích hoạt Google 2FA", command=activate_2fa)
activate_button.grid(column=2, row=0, padx=5)

disable_button = ttk.Button(button_frame, text="Vô hiệu hóa Google 2FA", command=disable_2fa)
disable_button.grid(column=3, row=0, padx=5)

load_config()

root.mainloop()
