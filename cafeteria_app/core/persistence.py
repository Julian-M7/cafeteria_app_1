"""
persistence.py
================
Capa de persistencia en JSON. Centraliza la lectura y escritura de los
tres archivos de datos de la aplicación (inventario, mesas, cierre),
garantizando:

    - Rutas siempre relativas a la raíz del proyecto (data/json/...),
      sin importar desde qué carpeta se ejecute main.py.
    - Escritura ATÓMICA: se escribe primero a un archivo temporal y
      luego se reemplaza el archivo final con os.replace(), para que
      un corte de energía o cierre inesperado nunca deje un JSON a
      medio escribir (corrupto).
    - Recuperación razonable si un archivo JSON llega a corromperse:
      se conserva una copia de respaldo (.bak) y se reinicia con un
      valor por defecto en vez de hacer crashear la aplicación.
"""

import json
import os
import sys
import tempfile

# En una app empaquetada con PyInstaller, el directorio de trabajo real no es
# la carpeta del código fuente. Por eso usamos la ruta de la app empacada si
# existe, o la raíz del proyecto en modo desarrollo.
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
    BUNDLED_DATA_DIR = os.path.join(sys._MEIPASS, "data", "json")
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BUNDLED_DATA_DIR = None

DATA_DIR = os.path.join(BASE_DIR, "data", "json")
# Si se empaquetó con --add-data "data;data", la carpeta "data" estará al lado
# de sys._MEIPASS o dentro de él; la ruta anterior cubre ambos escenarios.
if not os.path.exists(DATA_DIR):
    alt_dir = os.path.join(os.path.dirname(BASE_DIR), "data", "json")
    if os.path.exists(alt_dir):
        DATA_DIR = alt_dir

INVENTARIO_PATH = os.path.join(DATA_DIR, "inventario.json")
MESAS_PATH = os.path.join(DATA_DIR, "mesas.json")
CIERRE_PATH = os.path.join(DATA_DIR, "cierre.json")


def asegurar_directorio():
    os.makedirs(DATA_DIR, exist_ok=True)


def leer_json(path, valor_por_defecto):
    """
    Lee un archivo JSON. Si no existe, lo crea con `valor_por_defecto`.
    Si existe pero está corrupto (JSON inválido), se respalda como
    '<archivo>.bak' y se reinicia con el valor por defecto, para que
    la aplicación siga funcionando en vez de fallar por completo.
    """
    asegurar_directorio()

    if not os.path.exists(path) and BUNDLED_DATA_DIR:
        origen = os.path.join(BUNDLED_DATA_DIR, os.path.basename(path))
        if os.path.exists(origen):
            with open(origen, "r", encoding="utf-8") as archivo_origen:
                contenido = json.load(archivo_origen)
            escribir_json(path, contenido)
            return contenido

    if not os.path.exists(path):
        escribir_json(path, valor_por_defecto)
        return valor_por_defecto

    try:
        with open(path, "r", encoding="utf-8") as f:
            contenido = f.read().strip()
        if not contenido:
            return valor_por_defecto
        return json.loads(contenido)
    except (json.JSONDecodeError, OSError):
        backup_path = path + ".bak"
        try:
            os.replace(path, backup_path)
        except OSError:
            pass
        escribir_json(path, valor_por_defecto)
        return valor_por_defecto


def escribir_json(path, data):
    """
    Escritura atómica de un archivo JSON: se escribe a un archivo
    temporal en la misma carpeta y luego se reemplaza el destino final
    con os.replace (operación atómica a nivel de sistema operativo).
    """
    asegurar_directorio()
    directorio = os.path.dirname(path) or "."

    fd, tmp_path = tempfile.mkstemp(dir=directorio, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
