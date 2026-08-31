"""
Paquete core
=============
Contiene toda la lógica de negocio de la aplicación de ventas de la
cafetería, completamente independiente de la interfaz gráfica (Tkinter).

Módulos:
    money        -> parseo y formateo exacto de montos monetarios
    persistence  -> lectura/escritura atómica de los archivos JSON
    inventario   -> gestión de productos
    mesas        -> gestión de las 5 mesas y sus pedidos
    cierre       -> acumulación de ventas cobradas y totales de caja
    controller   -> fachada que coordina los módulos anteriores
"""
