import sys
import subprocess
import threading
import os
import time
import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext, END, DISABLED, NORMAL
from pathlib import Path

# ================== ФАЗА 0: ЗАГРУЗКА ЗАВИСИМОСТЕЙ ==================

def show_error_and_wait(title, message):
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(title, message)
    root.destroy()

def install_and_reload():
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"],
                       capture_output=True, check=True)
    except subprocess.CalledProcessError:
        show_error_and_wait("Ошибка", "pip не найден. Установите Python с Add to PATH.")
        sys.exit(1)

    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "--user", "--no-warn-script-location",
            "customtkinter",
            "zstandard"
        ])
        time.sleep(2)
        os.execl(sys.executable, sys.executable, *sys.argv)
    except Exception as e:
        show_error_and_wait("Ошибка установки", str(e))
        sys.exit(1)

try:
    import customtkinter as ctk
    import zstandard as zstd
except ImportError:
    install_and_reload()

# ================== ФАЗА 1: ОСНОВНОЕ ПРИЛОЖЕНИЕ ==================

class GZDecryptorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ZSTD Decryptor Pro")
        self.geometry("850x650")
        self.minsize(800, 600)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="ZSTD DECRYPTOR PRO",
            font=("Segoe UI", 28, "bold"),
            text_color="#2ecc71"
        )
        self.title_label.pack(pady=(20, 10))

        self.subtitle_label = ctk.CTkLabel(
            self.main_frame,
            text="Расшифровка ZSTD-файлов с перезаписью оригиналов",
            font=("Segoe UI", 14),
            text_color="#bdc3c7"
        )
        self.subtitle_label.pack(pady=(0, 30))

        self.folder_frame = ctk.CTkFrame(self.main_frame)
        self.folder_frame.pack(fill="x", padx=20, pady=(0, 25))

        self.folder_path = ctk.StringVar()

        self.folder_entry = ctk.CTkEntry(
            self.folder_frame,
            textvariable=self.folder_path,
            placeholder_text="Выберите папку...",
            height=45
        )
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)

        self.browse_button = ctk.CTkButton(
            self.folder_frame,
            text="Выбрать папку",
            command=self.browse_folder,
            width=150,
            height=45
        )
        self.browse_button.pack(side="right", padx=10, pady=10)

        self.decrypt_button = ctk.CTkButton(
            self.main_frame,
            text="РАСШИФРОВАТЬ",
            command=self.start_decryption,
            height=60,
            font=("Segoe UI", 18, "bold"),
            fg_color="#2ecc71"
        )
        self.decrypt_button.pack(pady=(0, 30), padx=40, fill="x")

        self.progress_label = ctk.CTkLabel(self.main_frame, text="Готово")
        self.progress_label.pack()

        self.progress_bar = ctk.CTkProgressBar(self.main_frame)
        self.progress_bar.pack(fill="x", padx=40, pady=(5, 20))
        self.progress_bar.set(0)

        self.log_textbox = scrolledtext.ScrolledText(
            self.main_frame,
            font=("Consolas", 11),
            bg="#1e1e1e",
            fg="#2ecc71"
        )
        self.log_textbox.pack(fill="both", expand=True, padx=20, pady=20)
        self.log_textbox.configure(state=DISABLED)

        self.log("Приложение готово")

    # ================== УТИЛИТЫ ==================

    def log(self, text):
        self.log_textbox.configure(state=NORMAL)
        self.log_textbox.insert(END, text + "\n")
        self.log_textbox.see(END)
        self.log_textbox.configure(state=DISABLED)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)
            self.log(f"Выбрана папка: {folder}")

    # ================== ZSTD ДЕШИФРОВКА ==================

    def decrypt_file_worker(self, file_path: Path):
        try:
            # Минимальный размер ZSTD
            if file_path.stat().st_size < 4:
                return True, "Пропущен (маленький файл)"

            # Проверка ZSTD magic number
            with open(file_path, "rb") as f:
                magic = f.read(4)
                if magic != b"\x28\xB5\x2F\xFD":
                    return True, "Не ZSTD"

            temp_path = file_path.with_suffix(file_path.suffix + ".tmp")

            dctx = zstd.ZstdDecompressor()

            # STREAM-дешифровка (КАК ВО ВТОРОМ КОДЕ)
            with open(file_path, "rb") as f_in:
                with open(temp_path, "wb") as f_out:
                    with dctx.stream_reader(f_in) as reader:
                        while True:
                            chunk = reader.read(16384)
                            if not chunk:
                                break
                            f_out.write(chunk)

            # Перезаписываем оригинал ТОЛЬКО если всё прошло успешно
            os.replace(temp_path, file_path)

            return True, "Расшифрован (ZSTD)"

        except Exception as e:
            # Чистим временный файл при ошибке
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except:
                pass

            return False, str(e)


    # ================== ОБРАБОТКА ПАПКИ ==================

    def process_directory(self, folder):
        files = []
        for root, _, filenames in os.walk(folder):
            for name in filenames:
                files.append(Path(root) / name)

        total = len(files)
        success = 0
        errors = 0

        for i, file in enumerate(files, 1):
            ok, msg = self.decrypt_file_worker(file)
            if ok:
                success += 1
            else:
                errors += 1

            self.log(f"[{i}/{total}] {file.name} → {msg}")
            self.progress_bar.set(i / total)
            self.progress_label.configure(text=f"{i}/{total}")

        self.log(f"ГОТОВО | Успешно: {success} | Ошибки: {errors}")

        self.decrypt_button.configure(state="normal")
        self.browse_button.configure(state="normal")

    # ================== ЗАПУСК ==================

    def start_decryption(self):
        folder = self.folder_path.get()
        if not folder or not os.path.isdir(folder):
            self.log("Ошибка: выберите папку")
            return

        self.decrypt_button.configure(state="disabled")
        self.browse_button.configure(state="disabled")

        threading.Thread(
            target=self.process_directory,
            args=(folder,),
            daemon=True
        ).start()

# ================== ТОЧКА ВХОДА ==================

if __name__ == "__main__":
    app = GZDecryptorApp()
    app.mainloop()
