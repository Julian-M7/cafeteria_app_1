#!/usr/bin/env python3
"""
main.py
========
Punto de entrada de la aplicación de ventas para la cafetería.

Ejecutar desde la raíz del proyecto con:
    python3 main.py

Requisitos: Python 3.8+ con Tkinter (incluido en la instalación
estándar de Python en Windows y macOS; en Linux puede requerir
instalar el paquete "python3-tk" del sistema, ver GUIA_USUARIO.md).
"""

from gui.app import iniciar_aplicacion

if __name__ == "__main__":
    iniciar_aplicacion()
