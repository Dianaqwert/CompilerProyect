import sys
import os
from PyQt6 import QtWidgets, uic, QtCore, QtGui
from PyQt6.QtGui import QFileSystemModel

# --- 1. CLASE PARA DIBUJAR LOS NÚMEROS ---
class NumeroLineas(QtWidgets.QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QtCore.QSize(self.editor.area_numeros_ancho(), 0)

    def paintEvent(self, event):
        self.editor.pintar_numeros_linea(event)

# --- 2. EDITOR DE CÓDIGO ---
class EditorConLineas(QtWidgets.QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.area_numeros = NumeroLineas(self)
        self.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        self.blockCountChanged.connect(self.actualizar_ancho_area_numeros)
        self.updateRequest.connect(self.actualizar_area_numeros)
        self.cursorPositionChanged.connect(self.resaltar_linea_actual)
        self.actualizar_ancho_area_numeros(0)

    def area_numeros_ancho(self):
        digitos = len(str(max(1, self.blockCount())))
        ancho = 20 + self.fontMetrics().horizontalAdvance('9') * digitos
        return ancho

    def actualizar_ancho_area_numeros(self, _):
        self.setViewportMargins(self.area_numeros_ancho(), 0, 0, 0)

    def actualizar_area_numeros(self, rect, dy):
        if dy: self.area_numeros.scroll(0, dy)
        else: self.area_numeros.update(0, rect.y(), self.area_numeros.width(), rect.height())
        if rect.contains(self.viewport().rect()): self.actualizar_ancho_area_numeros(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.area_numeros.setGeometry(QtCore.QRect(cr.left(), cr.top(), self.area_numeros_ancho(), cr.height()))

    def pintar_numeros_linea(self, event):
        painter = QtGui.QPainter(self.area_numeros)
        painter.fillRect(event.rect(), QtGui.QColor("#2b2b2b")) # Fondo oscuro IntelliJ
        bloque = self.firstVisibleBlock()
        num_bloque = bloque.blockNumber()
        top = int(self.blockBoundingGeometry(bloque).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(bloque).height())

        while bloque.isValid() and top <= event.rect().bottom():
            if bloque.isVisible() and bottom >= event.rect().top():
                numero = str(num_bloque + 1)
                painter.setPen(QtGui.QColor("#606366"))
                painter.drawText(0, top, self.area_numeros.width() - 5, self.fontMetrics().height(),
                                 QtCore.Qt.AlignmentFlag.AlignRight, numero)
            bloque = bloque.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(bloque).height())
            num_bloque += 1

    def resaltar_linea_actual(self):
        selections = []
        if not self.isReadOnly():
            selection = QtWidgets.QTextEdit.ExtraSelection()
            selection.format.setBackground(QtGui.QColor("#323232")) # Color de línea activa
            selection.format.setProperty(QtGui.QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            selections.append(selection)
        self.setExtraSelections(selections)

# --- 3. VENTANA PRINCIPAL ---
class MiIDE(QtWidgets.QMainWindow):
    def __init__(self):
        super(MiIDE, self).__init__()
        self.archivo_actual = None

        ruta_ui = os.path.join(os.path.dirname(__file__), 'untitled.ui')
        uic.loadUi(ruta_ui, self)

        # Reemplazo del editor con fuente Cascadia Code
        self.editor_nuevo = EditorConLineas()
        self.editor_nuevo.setObjectName("codigotextoplano")
        fuente = QtGui.QFont("Cascadia Code", 12)
        fuente.setWeight(600)
        self.editor_nuevo.setFont(fuente)

        self.modelo_archivos = QtGui.QFileSystemModel()

        # 2. Le decimos que empiece a leer desde tu carpeta de 8vo semestre
        ruta_proyecto = "D:\\Proyectos_8vo\\Compiladores_Si\\compilador_F1\\proyecto"
        self.modelo_archivos.setRootPath(ruta_proyecto)

        # 3. Se lo asignamos al widget que pusiste en Designer
        self.treeViewProyecto.setModel(self.modelo_archivos)
        self.treeViewProyecto.setRootIndex(self.modelo_archivos.index(ruta_proyecto))

        # 4. Estética: Ocultamos las columnas de Tamaño, Tipo y Fecha (para que se vea limpio)
        for i in range(1, 4):
            self.treeViewProyecto.hideColumn(i)

        # 5. Ocultamos el encabezado superior
        self.treeViewProyecto.header().hide()

        # SOLUCIÓN DE LOS ÍNDICES
        if hasattr(self, 'splitter'):
            self.splitter.replaceWidget(2, self.editor_nuevo)
            self.codigotextoplano.deleteLater()
            self.codigotextoplano = self.editor_nuevo
            # Darle más espacio al editor que a las pestañas
            self.splitter.setStretchFactor(1, 4)
            self.splitter.setStretchFactor(0, 1)

        # Configurar el movimiento vertical (Subir/Bajar errores)
        if hasattr(self, 'splitter_2'):
            # Según tu Inspector:
            # El índice 0 es 'ResultadosErrores' y el 1 es el 'splitter' (donde está el código)
            # Queremos que el código (índice 1) tenga más peso:
            self.splitter_2.setStretchFactor(1, 4)  # 80% para el editor
            self.splitter_2.setStretchFactor(0, 1)  # 20% para errores

        # --- CONEXIONES ---
        self.actionOpen.triggered.connect(self.abrir_archivo)
        self.actionGuardar.triggered.connect(self.guardar_archivo)
        self.actionGuardar_como.triggered.connect(self.guardar_como_archivo)
        self.actionbvn.triggered.connect(self.nuevo_archivo)
        self.actionSalir.triggered.connect(self.close)

        self.codigotextoplano.textChanged.connect(self.actualizar_estadisticas)
        self.codigotextoplano.cursorPositionChanged.connect(self.actualizar_estadisticas)

    def actualizar_estadisticas(self):
        contenido = self.codigotextoplano.toPlainText()
        palabras = len(contenido.split())
        cursor = self.codigotextoplano.textCursor()
        linea = cursor.blockNumber() + 1
        columna = cursor.columnNumber() + 1
        self.statusbar.showMessage(f"Línea: {linea} | Columna: {columna} | Palabras: {palabras}")

    # (Funciones de archivo: nuevo, abrir, guardar...)
    def nuevo_archivo(self):
        self.codigotextoplano.clear()
        self.archivo_actual = None
        self.setWindowTitle("Diana IDE - Nuevo Archivo")

    def abrir_archivo(self):
        nombre, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Abrir", "D:\\")
        if nombre:
            with open(nombre, 'r', encoding='utf-8') as f:
                self.codigotextoplano.setPlainText(f.read())
            self.archivo_actual = nombre
            self.setWindowTitle(f"Diana IDE - {os.path.basename(nombre)}")

    def guardar_archivo(self):
        if self.archivo_actual:
            with open(self.archivo_actual, 'w', encoding='utf-8') as f:
                f.write(self.codigotextoplano.toPlainText())
        else:
            self.guardar_como_archivo()

    def guardar_como_archivo(self):
        nombre, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Guardar como...", "D:\\", "Text files (*.txt)")
        if nombre:
            if not nombre.endswith('.txt'): nombre += '.txt'
            with open(nombre, 'w', encoding='utf-8') as f:
                f.write(self.codigotextoplano.toPlainText())
            self.archivo_actual = nombre
            self.setWindowTitle(f"Diana IDE - {os.path.basename(nombre)}")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MiIDE()
    window.show()
    sys.exit(app.exec())