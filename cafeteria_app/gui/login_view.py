"""
login_view.py
==============
Pantalla de inicio de sesión (módulo 2.1 del enunciado).
Credenciales fijas: usuario "hattu", contraseña "12345".
"""

import tkinter as tk
from tkinter import ttk

from .estilos import (COLOR_ACENTO, COLOR_ACENTO_HOVER, COLOR_BORDE, COLOR_ERROR,
                       COLOR_FONDO, COLOR_TEXTO, COLOR_TEXTO_SUAVE)


class LoginView(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLOR_FONDO)
        self.app = app

        tarjeta = tk.Frame(self, bg="white", highlightbackground=COLOR_BORDE,
                            highlightthickness=1)
        tarjeta.place(relx=0.5, rely=0.5, anchor="center", width=380, height=420)

        tk.Label(tarjeta, text="☕", font=("Segoe UI", 36), bg="white").pack(pady=(30, 0))
        tk.Label(tarjeta, text="Cafetería", font=("Segoe UI", 20, "bold"), bg="white",
                 fg=COLOR_ACENTO).pack(pady=(0, 4))
        tk.Label(tarjeta, text="Inicia sesión para continuar", font=("Segoe UI", 10),
                 bg="white", fg=COLOR_TEXTO_SUAVE).pack(pady=(0, 20))

        tk.Label(tarjeta, text="Usuario", font=("Segoe UI", 9), bg="white",
                 fg=COLOR_ACENTO).pack(anchor="w", padx=40)
        self.entry_usuario = ttk.Entry(tarjeta, font=("Segoe UI", 11))
        self.entry_usuario.pack(fill="x", padx=40, pady=(2, 12))
        self.entry_usuario.bind("<Return>", lambda e: self.entry_clave.focus_set())

        tk.Label(tarjeta, text="Contraseña", font=("Segoe UI", 9), bg="white",
                 fg=COLOR_ACENTO).pack(anchor="w", padx=40)
        self.entry_clave = ttk.Entry(tarjeta, font=("Segoe UI", 11), show="•")
        self.entry_clave.pack(fill="x", padx=40, pady=(2, 6))
        self.entry_clave.bind("<Return>", lambda e: self._intentar_login())

        self.label_error = tk.Label(tarjeta, text="", font=("Segoe UI", 9), bg="white",
                                     fg=COLOR_ERROR, wraplength=300)
        self.label_error.pack(pady=(4, 4))

        tk.Button(
            tarjeta, text="Iniciar sesión", font=("Segoe UI", 10, "bold"), bg=COLOR_ACENTO,
            fg="white", activebackground=COLOR_ACENTO_HOVER, activeforeground="white",
            bd=0, relief="flat", cursor="hand2", command=self._intentar_login,
        ).pack(fill="x", padx=40, pady=(10, 10), ipady=6)

        tk.Label(tarjeta, text="Usuario de prueba: hattu / 12345", font=("Segoe UI", 8),
                 bg="white", fg=COLOR_TEXTO_SUAVE).pack()

    def al_mostrar(self):
        self.entry_usuario.delete(0, tk.END)
        self.entry_clave.delete(0, tk.END)
        self.label_error.config(text="")
        self.entry_usuario.focus_set()

    def _intentar_login(self):
        usuario = self.entry_usuario.get().strip()
        clave = self.entry_clave.get()
        if self.app.controller.iniciar_sesion(usuario, clave):
            self.label_error.config(text="")
            self.app.mostrar("PrincipalView")
        else:
            self.label_error.config(text="Usuario o contraseña incorrectos.")
            self.entry_clave.delete(0, tk.END)
            self.entry_clave.focus_set()
