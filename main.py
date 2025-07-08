"""
Aplicação GUI para capturar números de uma imagem copiada (clipboard),
exibir a imagem, mostrar apenas os dígitos extraídos em um campo copiável
e permitir nova busca com confirmação.

Dependências:
    pip install pillow pytesseract
Também é necessário o Tesseract‑OCR instalado no sistema 
Se não tiver instalado, poderá instalar com o link: tesseract-ocr-w64-setup-5.5.0.20241111.exe 
ou empacotado junto usando PyInstaller (--add-data "Tesseract-OCR;Tesseract-OCR").
"""

import os
import sys
import re
import tkinter as tk
import pytesseract
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageGrab, ImageOps

# ----------------------------------------------------------------------
# 1. Resolve caminhos de recursos (funciona dentro e fora do .exe)
# ----------------------------------------------------------------------
def resource_path(rel_path: str) -> str:
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, rel_path)


# ----------------------------------------------------------------------
# 2. Caminho do Tesseract
# ----------------------------------------------------------------------
pytesseract.pytesseract.tesseract_cmd = resource_path(os.path.join("Tesseract-OCR", "tesseract.exe"))


# ----------------------------------------------------------------------
# 3. Janela principal
# ----------------------------------------------------------------------
class OCRApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Captura de Números (OCR)")
        self.geometry("700x550") 
        self.minsize(450, 450)  
        self.configure(padx=20, pady=20) 

        # --- Configuração de Tema e Estilos ---
        style = ttk.Style(self)
        style.theme_use('clam')

        # Estilo geral para Labels e Entry/Text
        style.configure('TLabel', font=('Segoe UI', 10))
        style.configure('TEntry', font=('Segoe UI', 10))
        style.configure('TText', font=('Consolas', 10)) 

        # Estilos para os Botões
        style.configure('TButton', font=('Segoe UI', 10, 'bold'), padding=10) 
        style.map('TButton',
                  foreground=[('pressed', 'white'), ('active', 'blue')], 
                  background=[('pressed', '!focus', 'gray'), ('active', 'lightblue')]) 

        style.configure('Red.TButton', background='firebrick', foreground='white') 
        style.map('Red.TButton',
                  background=[('pressed', 'darkred'), ('active', 'red')], 
                  foreground=[('pressed', 'white'), ('active', 'white')])


        # Mantém referência da imagem
        self._img_tk = None

        # Frame para a área da imagem
        self.img_container_frame = ttk.Frame(self, relief="flat", borderwidth=0)
        self.img_container_frame.grid(row=0, column=0, columnspan=3, sticky="nsew", pady=(0, 15)) 
        self.img_container_frame.grid_rowconfigure(0, weight=1)
        self.img_container_frame.grid_columnconfigure(0, weight=1)

        self.text_output_frame = ttk.Frame(self, relief="flat", borderwidth=0)
        self.text_output_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=(0, 15)) 
        self.text_output_frame.grid_rowconfigure(1, weight=1)
        self.text_output_frame.grid_columnconfigure(0, weight=1)

        self.button_controls_frame = ttk.Frame(self, relief="flat", borderwidth=0)
        self.button_controls_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(10, 0)) # Padding superior para os botões
        self.button_controls_frame.grid_columnconfigure((0, 1, 2), weight=1) # Colunas dos botões expandem igualmente


        # ----- Widgets e Posicionamento (dentro dos Frames) -----
        self.img_label = tk.Label(
            self.img_container_frame, 
            text="Cole uma imagem 🖼️",
            relief="solid", 
            borderwidth=1,
            justify="center",
            font=("Segoe UI", 16, "italic"),
            bg="#e0e0e0",
            fg="#606060"
        )
        self.img_label.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        ttk.Label(self.text_output_frame, text="Números extraídos:", font=("Segoe UI", 11, "bold"), padding=(0, 0, 0, 5)).grid(
            row=0, column=0, sticky="w"
        )
        self.text_box = tk.Text(self.text_output_frame, height=5, wrap="word",
                                relief="flat", borderwidth=1, highlightbackground="lightgray", highlightthickness=1,
                                padx=10, pady=10) 
        self.text_box.grid(row=1, column=0, sticky="nsew")

        self.btn_paste = ttk.Button(self.button_controls_frame, text="Colar Imagem", command=self.paste_image)
        self.btn_paste.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.btn_copy = ttk.Button(self.button_controls_frame, text="Copiar Números", command=self.copy_text)
        self.btn_copy.grid(row=0, column=1, sticky="ew", padx=8)

        self.btn_clear = ttk.Button(self.button_controls_frame, text="Limpar", command=self.confirm_clear, style='Red.TButton')
        self.btn_clear.grid(row=0, column=2, sticky="ew", padx=(8, 0))

        # --- Configuração de responsividade da janela principal ---
        self.grid_columnconfigure((0, 1, 2), weight=1)
        self.grid_rowconfigure(0, weight=3) 
        self.grid_rowconfigure(1, weight=1) 
        self.grid_rowconfigure(2, weight=0) 

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ------------------------------------------------------------------
    # Métodos (sem alterações na lógica)
    # ------------------------------------------------------------------
    def paste_image(self):
        """Captura imagem do clipboard, exibe e extrai dígitos."""
        img = ImageGrab.grabclipboard()
        if img is None:
            messagebox.showerror("Erro", "Não há imagem na área de transferência.")
            return

        gray = img.convert("L")
        gray = ImageOps.autocontrast(gray)
        w, h = gray.size
        gray = gray.resize((w * 2, h * 2), Image.LANCZOS)
        bw = gray.point(lambda x: 255 if x > 150 else 0, mode="1")

        # --- Mostra miniatura na GUI ---
        thumb = bw.convert("RGB").copy()
        label_width = self.img_label.winfo_width()
        label_height = self.img_label.winfo_height()

        if label_width == 1 or label_height == 1: 
            max_size = (600, 350)
        else:
            max_size = (label_width, label_height)

        thumb.thumbnail(max_size, Image.LANCZOS) 
        self._img_tk = ImageTk.PhotoImage(thumb)
        self.img_label.configure(image=self._img_tk, text="")

        # --- OCR restrito a dígitos ---
        config = "--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789"
        try:
            raw_text = pytesseract.image_to_string(bw, lang="eng", config=config)
        except pytesseract.TesseractNotFoundError:
            messagebox.showerror(
                "Tesseract não encontrado",
                "O executável Tesseract‑OCR não foi localizado.\n"
                "Verifique o caminho em pytesseract.pytesseract.tesseract_cmd.",
            )
            return

        numbers = re.findall(r"\d+", raw_text)
        self.text_box.delete("1.0", tk.END)
        if numbers:
            self.text_box.insert(tk.END, " ".join(numbers))
        else:
            messagebox.showinfo(
                "Nenhum número",
                "O OCR não encontrou dígitos na imagem.\n"
                "Tente um print mais nítido ou ajuste o limiar.",
            )

        print("Números que foram consultados: ", raw_text)

    def copy_text(self):
        text = self.text_box.get("1.0", tk.END).strip()
        if not text:
            messagebox.showinfo("Sem texto", "Não há texto para copiar.")
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Copiado", "Texto copiado para a área de transferência.")

    def confirm_clear(self):
        if messagebox.askyesno(
            "Nova consulta",
            "Deseja iniciar uma nova consulta?\nIsso apagará a imagem e o texto.",
        ):
            self.clear_all()

    def clear_all(self):
        self.img_label.configure(image="", text="Cole uma imagem 🖼️", bg="#e0e0e0", fg="#606060") # Restaura cor de fundo e texto
        self.text_box.delete("1.0", tk.END)
        self._img_tk = None

    def on_close(self):
        if messagebox.askokcancel("Sair", "Deseja sair do aplicativo?"):
            self.destroy()


# ----------------------------------------------------------------------
# 4. Execução
# ----------------------------------------------------------------------
if __name__ == "__main__":
    OCRApp().mainloop()