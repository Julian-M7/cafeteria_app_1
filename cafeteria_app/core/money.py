"""
money.py
=========
Utilidades para el manejo EXACTO de dinero en toda la aplicación.

Decisión de diseño (ver README.md, sección "Manejo de dinero"):
    Se usa `decimal.Decimal` para todo cálculo monetario. Nunca se usan
    `float` para precios, subtotales o totales, ya que los flotantes no
    pueden representar exactamente cantidades decimales (ej. 0.1 + 0.2
    != 0.3 en binario) y eso puede producir descuadres de caja.

Este módulo centraliza:
    - El parseo de texto ingresado por el usuario a `Decimal`
      (parse_monto), aceptando los formatos numéricos usados en
      Colombia (punto o coma como separador de miles, coma o punto
      como separador decimal, símbolo $ opcional).
    - El formateo de un `Decimal` a texto para mostrarlo en pantalla
      (formatear_monto), con separador de miles '.' y decimales ',' 
      (formato local: $10.000,50).
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re

DOS_DECIMALES = Decimal("0.01")

# Sólo se permiten dígitos, puntos y comas (una vez removidos espacios y '$')
_PATRON_CARACTERES_VALIDOS = re.compile(r"^[0-9.,]+$")


def _quantize(valor: Decimal) -> Decimal:
    """Redondea un Decimal a exactamente 2 decimales (ROUND_HALF_UP)."""
    return valor.quantize(DOS_DECIMALES, rounding=ROUND_HALF_UP)


def to_decimal(valor) -> Decimal:
    """
    Convierte de forma segura un valor (str, int, float, Decimal) ya
    normalizado internamente (por ejemplo, leído de un JSON) a Decimal.
    NO debe usarse para texto escrito libremente por el usuario: para
    eso está `parse_monto`, que además valida y explica errores.
    """
    if isinstance(valor, Decimal):
        return valor
    return Decimal(str(valor))


def parse_monto(texto):
    """
    Interpreta un texto ingresado por el usuario como un monto en pesos
    colombianos y lo convierte a Decimal con exactamente 2 decimales.

    Formatos aceptados (ver casos de prueba en tests/test_core.py):
        "10000"        -> 10000.00
        "10.000"       -> 10000.00   (punto usado como separador de miles)
        "10,000"       -> 10000.00   (coma usada como separador de miles,
                                       formato alterno)
        "10.000,50"    -> 10000.50   (punto miles + coma decimales)
        "10,000.50"    -> 10000.50   (coma miles + punto decimales)
        "$10.000,50"   -> 10000.50   (símbolo de moneda, se ignora)
        "10.5" / "10,5"-> 10.50      (decimal simple)

    Regla de desambiguación cuando sólo aparece UN tipo de separador:
        Si el separador aparece seguido de un grupo de EXACTAMENTE 3
        dígitos (y los demás grupos también tienen máximo 3 dígitos),
        se interpreta como separador de MILES (ej. "10.000" -> 10000),
        porque el dinero en COP no maneja 3 cifras decimales. En caso
        contrario (1 ó 2 dígitos después del separador) se interpreta
        como separador DECIMAL (ej. "10.50" -> 10.50).

    Retorna:
        (Decimal, None)      si el monto es válido
        (None, "mensaje")    si el monto es inválido, con un mensaje
                              de error claro y específico
    """
    if texto is None:
        return None, "Campo vacío."

    texto = str(texto).strip()
    if texto == "":
        return None, "Campo vacío."

    # Quitar símbolo de moneda y espacios internos (ej. "$ 10.000,50")
    texto = texto.replace("$", "").replace(" ", "")
    if texto == "":
        return None, "Campo vacío."

    negativo = texto.startswith("-")
    if negativo:
        return None, "El monto debe ser positivo."

    if not _PATRON_CARACTERES_VALIDOS.match(texto):
        return None, "Formato no aceptado. Use solo números, puntos y comas."

    tiene_punto = "." in texto
    tiene_coma = "," in texto

    try:
        if tiene_punto and tiene_coma:
            normalizado = _normalizar_con_ambos_separadores(texto)
        elif tiene_punto:
            normalizado = _normalizar_un_separador(texto, ".")
        elif tiene_coma:
            normalizado = _normalizar_un_separador(texto, ",")
        else:
            normalizado = texto

        if normalizado is None:
            return None, "Formato no aceptado."

        valor = Decimal(normalizado)
    except (InvalidOperation, IndexError, ValueError):
        return None, "Formato no aceptado."

    # Validar máximo 2 decimales EN EL VALOR YA NORMALIZADO como decimal
    exponente = valor.as_tuple().exponent
    if isinstance(exponente, int) and exponente < -2:
        return None, "El monto admite máximo 2 decimales."

    if valor <= 0:
        return None, "El monto debe ser mayor que cero."

    return _quantize(valor), None


def _es_grupo_de_miles(grupos):
    """
    True si una lista de grupos separados por un separador (ej.
    ["10", "000"] o ["1", "234", "567"]) tiene la forma de una
    agrupación de miles: el último grupo tiene exactamente 3 dígitos,
    todos los grupos anteriores tienen entre 1 y 3 dígitos, y ningún
    grupo está vacío.
    """
    if len(grupos) < 2 or any(g == "" for g in grupos):
        return False
    if len(grupos[-1]) != 3:
        return False
    return all(1 <= len(g) <= 3 for g in grupos[:-1])


def _normalizar_un_separador(texto, separador):
    """Normaliza un texto que sólo contiene UN tipo de separador
    (punto o coma) a un string tipo '1234.56' listo para Decimal()."""
    grupos = texto.split(separador)

    if _es_grupo_de_miles(grupos):
        # separador de miles: se eliminan todas las ocurrencias
        return "".join(grupos)

    # separador decimal: sólo puede haber una ocurrencia
    if len(grupos) != 2 or grupos[0] == "" and grupos[1] == "":
        return None
    entero = grupos[0] if grupos[0] != "" else "0"
    decimales = grupos[1]
    return f"{entero}.{decimales}"


def _normalizar_con_ambos_separadores(texto):
    """Normaliza un texto que contiene punto Y coma. El separador que
    aparece más a la derecha se interpreta como el separador decimal;
    el otro, como separador de miles (se elimina)."""
    pos_punto = texto.rfind(".")
    pos_coma = texto.rfind(",")

    if pos_coma > pos_punto:
        # coma = decimal, punto = miles
        parte_entera = texto[:pos_coma].replace(".", "")
        parte_decimal = texto[pos_coma + 1:]
    else:
        # punto = decimal, coma = miles
        parte_entera = texto[:pos_punto].replace(",", "")
        parte_decimal = texto[pos_punto + 1:]

    if parte_entera == "" or parte_decimal == "":
        return None
    return f"{parte_entera}.{parte_decimal}"


def formatear_monto(valor) -> str:
    """
    Formatea un Decimal (o algo convertible a Decimal) como texto en
    formato local colombiano: separador de miles '.', separador
    decimal ',', antecedido por '$'. Ej: Decimal('10000.5') -> '$10.000,50'
    """
    valor = _quantize(to_decimal(valor))
    negativo = valor < 0
    valor = abs(valor)

    entero = int(valor)
    centavos = int((valor - entero) * 100)

    entero_txt = f"{entero:,}".replace(",", ".")
    resultado = f"${entero_txt},{centavos:02d}"
    return f"-{resultado}" if negativo else resultado
