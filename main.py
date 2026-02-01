# ==============================================================
# DeepSeek Chat клиент для Groq API
# ==============================================================
import os
import json
import time
import threading
import requests
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from PIL import Image, ImageTk
import customtkinter as ctk

# ==============================================================
# ГЛОБАЛЬНЫЕ НАСТРОЙКИ
# ==============================================================
API_KEY = "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"
BASE_URL = "https://api.groq.com/openai/v1"
MODEL_NAME = "llama-3.3-70b-versatile"
APP_VERSION = "3.0.0 Groq Chat"
HISTORY_FILE = "chat_history.json"

# ==============================================================
# DeepSeek Core: работа с историей и API
# ==============================================================
class DeepSeekCore:
    def __init__(self, api_key):
        self.api_key = api_key
        self.history = []
        self.system_prompt = ("пиши на русском языке")
        
        self.load_history()

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except Exception:
                self.history = []

    def save_history(self):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[SAVE ERROR] {e}")

    def clear_history(self):
        self.history = []
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)

    def fetch_response(self, user_text, log_callback):
        """Отправка запроса в Groq API (OpenAI-совместимый)"""
        self.history.append({"role": "user", "content": user_text})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Формируем чат
        messages = [{"role": "system", "content": self.system_prompt}]
        for msg in self.history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        payload = {
            "model": MODEL_NAME,
            "messages": messages,
            "temperature": 0.7
        }

        try:
            log_callback(f">>> Sending request: {user_text[:40]}...")
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/chat/completions", headers=headers, json=payload, timeout=45)
            elapsed = time.time() - start_time

            if response.status_code == 401:
                return "Error: Invalid API Key."
            if response.status_code == 429:
                return "Error: Rate limit exceeded."

            response.raise_for_status()
            data = response.json()

            # Groq/LLM API OpenAI-style: получаем текст
            ai_message = data["choices"][0]["message"]["content"]

            self.history.append({"role": "assistant", "content": ai_message})
            self.save_history()
            log_callback(f"<<< Response received ({elapsed:.1f}s)")
            return ai_message

        except Exception as e:
            log_callback(f"[ERROR] {str(e)}")
            return f"Error connecting to API: {str(e)}"

# ==============================================================
# Терминал для логов
# ==============================================================
class TerminalModule:
    def __init__(self, parent):
        self.parent = parent
        self.window = None

    def show_terminal(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
        self.window = tk.Toplevel(self.parent)
        self.window.title("DeepSeek Terminal")
        self.window.geometry("600x400")
        self.text_box = tk.Text(self.window, font=("Consolas", 11), bg="#1E1E1E", fg="#00FF00")
        self.text_box.pack(fill="both", expand=True)
        self.text_box.insert("end", "Terminal initialized...\n")

    def write_log(self, text):
        print(text)
        if self.window and self.window.winfo_exists():
            self.text_box.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {text}\n")
            self.text_box.see("end")

# ==============================================================
# Основное окно приложения
# ==============================================================
class DeepSeekApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.core = DeepSeekCore(API_KEY)
        self.appearance_mode = "dark"

        self.setup_window()
        self.terminal = TerminalModule(self)
        self.terminal.write_log("Application started.")

        self.create_sidebar()
        self.create_main_area()
        self.create_status_bar()

        self.bind("<F6>", lambda e: self.terminal.show_terminal())
        self.protocol("WM_DELETE_WINDOW", self.on_exit)

    def setup_window(self):
        self.title(f"DeepSeek Groq v{APP_VERSION}")
        self.geometry("1200x800")
        ctk.set_appearance_mode(self.appearance_mode)
        ctk.set_default_color_theme("blue")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(8, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="DEEPSEEK PRO", font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 20))

        self.btn_new_chat = ctk.CTkButton(
            self.sidebar_frame, text="New Chat", command=self.new_session, fg_color="#2A9D8F", hover_color="#21867A"
        )
        self.btn_new_chat.grid(row=1, column=0, padx=20, pady=10)

        self.btn_theme = ctk.CTkButton(self.sidebar_frame, text="Toggle Theme", command=self.toggle_theme)
        self.btn_theme.grid(row=2, column=0, padx=20, pady=10)

        self.info_box = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent", border_width=1)
        self.info_box.grid(row=8, column=0, padx=20, pady=20, sticky="s")
        self.token_label = ctk.CTkLabel(self.info_box, text="Tokens: 0", font=("Consolas", 11))
        self.token_label.pack(padx=10, pady=5)

    def create_main_area(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=(20, 0))
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        self.chat_box = ctk.CTkTextbox(self.main_container, font=("Segoe UI", 15), wrap="word", border_width=1)
        self.chat_box.grid(row=0, column=0, sticky="nsew")
        self.chat_box.configure(state="disabled")

        self.input_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.input_frame.grid(row=1, column=0, sticky="ew", pady=20)
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.user_input = ctk.CTkEntry(self.input_frame, placeholder_text="Type your message here...", height=50, font=("Segoe UI", 14))
        self.user_input.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.user_input.bind("<Return>", lambda e: self.handle_send())

        self.send_button = ctk.CTkButton(self.input_frame, text="Send", width=120, height=50, command=self.handle_send, font=ctk.CTkFont(weight="bold"))
        self.send_button.grid(row=0, column=1)

    def create_status_bar(self):
        self.status_bar = ctk.CTkFrame(self, height=25, corner_radius=0)
        self.status_bar.grid(row=1, column=1, sticky="ew")
        self.status_label = ctk.CTkLabel(self.status_bar, text="Ready", font=("Segoe UI", 11))
        self.status_label.pack(side="left", padx=20)

    def toggle_theme(self):
        self.appearance_mode = "light" if self.appearance_mode == "dark" else "dark"
        ctk.set_appearance_mode(self.appearance_mode)
        self.terminal.write_log(f"Theme changed to {self.appearance_mode}")

    # ==============================================================
    # ОБРАБОТКА СОБЫТИЙ
    # ==============================================================
    def handle_send(self):
        query = self.user_input.get().strip()
        if not query:
            return

        self.user_input.delete(0, "end")
        self.user_input.configure(state="disabled")
        self.send_button.configure(state="disabled")
        self.append_to_chat("You", query, "#3B82F6")
        self.status_label.configure(text="AI is typing...")

        threading.Thread(target=self.async_api_call, args=(query,), daemon=True).start()

    def async_api_call(self, query):
        try:
            response = self.core.fetch_response(query, self.terminal.write_log)
            self.after(0, lambda: self.display_ai_response(response))
        except Exception as e:
            self.after(0, lambda: self.display_ai_response(f"Error: {str(e)}"))

    def display_ai_response(self, response):
        self.append_to_chat("DeepSeek", response, "#10B981")
        self.user_input.configure(state="normal")
        self.send_button.configure(state="normal")
        self.status_label.configure(text="Ready")
        self.user_input.focus()
        tokens = len(response.split()) * 1.3
        self.token_label.configure(text=f"Tokens approx: {int(tokens)}")

    def append_to_chat(self, sender, text, color):
        self.chat_box.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M")
        header = f"\n[{timestamp}] {sender}:\n"
        self.chat_box.insert("end", header, "header")
        self.chat_box.insert("end", f"{text}\n", "body")
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled")

    def new_session(self):
        if messagebox.askyesno("DeepSeek Groq", "Clear chat history?"):
            self.core.clear_history()
            self.chat_box.configure(state="normal")
            self.chat_box.delete("1.0", "end")
            self.chat_box.configure(state="disabled")
            self.terminal.write_log("New session started.")

    def on_exit(self):
        self.core.save_history()
        self.terminal.write_log("Application closing...")
        self.destroy()

# ==============================================================
# MAIN
# ==============================================================
def main():
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = DeepSeekApp()
    if not app.core.history:
        app.append_to_chat("System", "Welcome to DeepSeek Groq Chat.", "#6B7280")
    else:
        for msg in app.core.history:
            role = "You" if msg["role"] == "user" else "DeepSeek"
            color = "#3B82F6" if msg["role"] == "user" else "#10B981"
            app.append_to_chat(role, msg["content"], color)

    app.mainloop()

if __name__ == "__main__":
    main()

