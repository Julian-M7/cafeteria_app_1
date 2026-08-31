"""
estilos.py
===========
Constantes visuales y widgets reutilizables, compartidos por todas las
pantallas de gui/, para mantener una apariencia consistente en toda la
aplicación (paleta "café").
"""

import tkinter as tk

COLOR_FONDO = "#f4ede4"
COLOR_BARRA = "#4a3327"
COLOR_ACENTO = "#6f4e37"
COLOR_ACENTO_HOVER = "#3a271d"
COLOR_TEXTO = "#2c2015"
COLOR_TEXTO_SUAVE = "#7a6a58"
COLOR_BORDE = "#d8cbb8"
COLOR_ERROR = "#b3261e"
COLOR_EXITO = "#2f7d32"
COLOR_EXITO_HOVER = "#265f28"
COLOR_BLANCO = "white"

FUENTE_BASE = ("Segoe UI", 10)
FUENTE_PEQUENA = ("Segoe UI", 9)
FUENTE_MUY_PEQUENA = ("Segoe UI", 8)
FUENTE_ETIQUETA = ("Segoe UI", 9)
FUENTE_TITULO = ("Segoe UI", 13, "bold")
FUENTE_TITULO_GRANDE = ("Segoe UI", 20, "bold")
FUENTE_NEGRITA = ("Segoe UI", 10, "bold")


def crear_barra_superior(parent, app, titulo, mostrar_volver=True):
    """Crea la barra superior estándar (marrón) con botón de regreso al
    panel principal y un título. La usan Inventario, Ventas y Cierre."""
    barra = tk.Frame(parent, bg=COLOR_BARRA, height=56)
    barra.pack(fill="x", side="top")
    barra.pack_propagate(False)

    if mostrar_volver:
        tk.Button(
            barra, text="← Panel principal", font=FUENTE_PEQUENA, bg=COLOR_BARRA,
            fg="white", bd=0, cursor="hand2", activebackground=COLOR_ACENTO_HOVER,
            activeforeground="white",
            command=lambda: app.mostrar("PrincipalView"),
        ).pack(side="left", padx=16)

    tk.Label(barra, text=titulo, font=FUENTE_TITULO, bg=COLOR_BARRA, fg="white").pack(
        side="left", padx=10)
    return barra


def boton_primario(parent, text, command, **kwargs):
    opciones = dict(font=FUENTE_NEGRITA, bg=COLOR_ACENTO, fg="white", bd=0, cursor="hand2",
                     activebackground=COLOR_ACENTO_HOVER, activeforeground="white",
                     padx=12, pady=6)
    opciones.update(kwargs)
    return tk.Button(parent, text=text, command=command, **opciones)


def boton_secundario(parent, text, command, **kwargs):
    opciones = dict(font=FUENTE_PEQUENA, bg="white", bd=1, relief="solid", cursor="hand2",
                     padx=12, pady=5)
    opciones.update(kwargs)
    return tk.Button(parent, text=text, command=command, **opciones)
