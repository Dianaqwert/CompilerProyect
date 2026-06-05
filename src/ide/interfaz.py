import sys
import os
from PyQt6 import QtWidgets, uic, QtCore, QtGui
from PyQt6.QtWidgets import QHeaderView
#lexico
from compiler.analizadorLexico import lexer,find_column
from compiler.analizadorSintactico import ejecutar_parser
from compiler.highlighter import LexicalHighlighter

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def resource_path(relative_path):
    """ Obtiene la ruta absoluta basándose en la ubicación de interfaz.py """
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

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
        ###############################3
        #           VISTA
        ###############################
        self.archivo_actual = None
        self.contenido_original = ""  # Nueva variable para detectar cambios
        self.actionAnalisis_lexico: QtGui.QAction
        self.actionAnalisis_sintactico: QtGui.QAction
        self.tablaLexico: QtWidgets.QTableWidget
        self.tablaErroresLexicos: QtWidgets.QTableWidget
        #ruta_ui = os.path.join(os.path.dirname(__file__), 'untitled.ui')
        ruta_ui = resource_path('untitled.ui')
        uic.loadUi(ruta_ui, self)

        # ==========================================
        # 2. CARGA DE ÍCONOS
        # ==========================================
        icono_abrir = QtGui.QIcon(resource_path('recursos/icono_Open.png'))
        icono_guardar = QtGui.QIcon(resource_path('recursos/icono_savefile.png'))
        icono_guardar_como = QtGui.QIcon(resource_path('recursos/icono_saveAs.png'))
        icono_nuevo = QtGui.QIcon(resource_path('recursos/icono_newfile.png'))
        icono_salir = QtGui.QIcon(resource_path('recursos/icono_close.png'))
        icono_cerrar = QtGui.QIcon(resource_path('recursos/close_file.png'))

        # Asignarlos a las acciones de tu menú
        self.actionOpen.setIcon(icono_abrir)
        self.actionGuardar.setIcon(icono_guardar)
        self.actionGuardar_como.setIcon(icono_guardar_como)
        self.actionbvn.setIcon(icono_nuevo)
        self.actionSalir.setIcon(icono_salir)
        self.actionCerrar_archivo_self.setIcon(icono_cerrar)

        # Reemplazo del editor con fuente Cascadia Code
        self.editor_nuevo = EditorConLineas()
        self.editor_nuevo.setObjectName("codigotextoplano")
        fuente = QtGui.QFont("Cascadia Code", 12)
        fuente.setWeight(600)
        self.editor_nuevo.setFont(fuente)
        ##ANALIZADOR LEXICO
        self.actionAnalisis_lexico.triggered.connect(self.ejecutar_analisis_lexico)
        self.actionAnalisis_sintactico.triggered.connect(self.ejecutar_analisis_sintactico)
        self.highlighter = LexicalHighlighter(self.editor_nuevo.document())

        # SOLUCIÓN DE LOS ÍNDICES
        if hasattr(self, 'splitter'):
            indice_real = self.splitter.indexOf(self.codigotextoplano)

            # 2. Reemplazamos exactamente en esa posición
            self.splitter.replaceWidget(indice_real, self.editor_nuevo)
            self.codigotextoplano.deleteLater()
            self.codigotextoplano = self.editor_nuevo

            # 3. Ajustamos el estiramiento usando el MISMO índice
            self.splitter.setStretchFactor(indice_real, 4)
            self.splitter.setStretchFactor(0, 1)

        # Configurar el movimiento vertical (Subir/Bajar errores)
        if hasattr(self, 'splitter_2'):
            # Según tu Inspector:
            # El índice 0 es 'ResultadosErrores' y el 1 es el 'splitter' (donde está el código)
            self.splitter_2.setStretchFactor(1, 4)  # 80% para el editor
            self.splitter_2.setStretchFactor(0, 1)  # 20% para errores


        # --- CONEXIONES ---
        self.actionOpen.triggered.connect(self.abrir_archivo)
        self.actionGuardar.triggered.connect(self.guardar_archivo)
        self.actionGuardar_como.triggered.connect(self.guardar_como_archivo)
        self.actionbvn.triggered.connect(self.nuevo_archivo)
        self.actionSalir.triggered.connect(self.close)
        self.actionCerrar_archivo_self.triggered.connect(self.cerrar_archivo)

        self.codigotextoplano.textChanged.connect(self.actualizar_estadisticas)
        self.codigotextoplano.cursorPositionChanged.connect(self.actualizar_estadisticas)

    ##INTERFAZ :
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
        self.setWindowTitle("IDE")

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

    def cerrar_archivo(self):
        # 1. ¿Hay cambios sin guardar?
        contenido_actual = self.codigotextoplano.toPlainText()

        if contenido_actual != self.contenido_original:
            # Creamos la ventana de confirmación
            respuesta = QtWidgets.QMessageBox.question(
                self,
                "Cambios sin guardar",
                "¿Deseas guardar los cambios antes de cerrar?",
                QtWidgets.QMessageBox.StandardButton.Save |
                QtWidgets.QMessageBox.StandardButton.Discard |
                QtWidgets.QMessageBox.StandardButton.Cancel
            )

            if respuesta == QtWidgets.QMessageBox.StandardButton.Save:
                self.guardar_archivo()  # Llamamos a tu función de guardado
            elif respuesta == QtWidgets.QMessageBox.StandardButton.Cancel:
                return  # Detenemos el cierre si el usuario se arrepintió

        # 2. Si no hay cambios o el usuario eligió "Descartar", limpiamos todo
        self.codigotextoplano.clear()
        self.archivo_actual = None
        self.contenido_original = ""
        self.setWindowTitle("Diana IDE - Sin archivo")
        self.statusbar.showMessage("Archivo cerrado correctamente", 3000)

    #################################################### ANALIZADOR LEXICO ################################################
    def ejecutar_analisis_lexico(self):
        print("Botón presionado: Ejecutando análisis...")  # Mensaje para confirmar en consola
        codigo = self.codigotextoplano.toPlainText()

        lexer.input(codigo)
        lexer.lineno = 1

        tokens_lista = []
        errores_lista = []

        while True:
            tok = lexer.token()
            if not tok: break

            col = find_column(codigo, tok)

            # 1. Separamos los errores
            if tok.type in ['ERR_DECIMAL', 'ERROR_SIMBOLO']:
                errores_lista.append((tok.lineno, col, tok.value))
            else:
                # 2. Traductor a "Nombres"
                tipo_bonito = tok.type
                if tok.type in ['INT']:
                    tipo_bonito = "Número"
                elif tok.type in ['REAL']:
                    tipo_bonito="Flotante"
                elif tok.type in ['IF', 'ELSE', 'END', 'MAIN', 'DO', 'WHILE', 'INT_DECL', 'FLOAT_DECL', 'CIN', 'COUT',
                                  'SWITCH', 'CASE']:
                    tipo_bonito = "Reservada"
                elif tok.type == 'ID':
                    tipo_bonito = "Identificador"
                elif tok.type in ['PLUS', 'MINUS', 'MULT', 'DIV', 'MOD', 'POW', 'INC', 'DEC']:
                    tipo_bonito = "Op. Aritmético"
                elif tok.type in ['LBRACE', 'RBRACE', 'LPAREN', 'RPAREN', 'COMMA', 'SEMI']:
                    tipo_bonito = "Símbolo"
                elif tok.type in ['LT', 'LTE', 'GT', 'GTE', 'NE', 'EQ']:
                    tipo_bonito = "Op. Relacional"
                elif tok.type in ['AND', 'OR', 'NOT']:
                    tipo_bonito = "Op. Lógico"
                elif tok.type == 'ASSIGN':
                    tipo_bonito = "Asignación"

                tokens_lista.append((tok.lineno, col, tipo_bonito, tok.value))

        # Llamamos a la función que pinta las tablas
        self.mostrar_resultados_lexicos(tokens_lista, errores_lista)


    def mostrar_resultados_lexicos(self, tokens, errores):
        # ---  TABLA LÉXICA ---
        # Obligamos a Qt a crear 4 columnas, sin importar lo que diga el Designer
        self.tablaLexico.setColumnCount(4)
        self.tablaLexico.setHorizontalHeaderLabels(["Línea", "Columna", "Tipo de Token", "Lexema"])

        self.tablaLexico.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        header_lexico = self.tablaLexico.horizontalHeader()
        header_lexico.setSectionsMovable(True)
        header_lexico.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Línea: Ajuste exacto
        header_lexico.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Columna: Ajuste exacto
        header_lexico.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Tipo: Ajuste exacto
        header_lexico.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Lexema: Ocupa el resto de la pantalla

        self.tablaLexico.setRowCount(0)  # Limpiamos basura anterior
        self.tablaLexico.setRowCount(len(tokens))

        for i, (lin, col, tipo, lex) in enumerate(tokens):
            self.tablaLexico.setItem(i, 0, QtWidgets.QTableWidgetItem(str(lin)))
            self.tablaLexico.setItem(i, 1, QtWidgets.QTableWidgetItem(str(col)))
            self.tablaLexico.setItem(i, 2, QtWidgets.QTableWidgetItem(str(tipo)))
            self.tablaLexico.setItem(i, 3, QtWidgets.QTableWidgetItem(str(lex)))

        # --- TABLA DE ERRORES ---
        # Obligamos a Qt a crear 3 columnas
        self.tablaErroresLexicos.setColumnCount(3)
        self.tablaErroresLexicos.setHorizontalHeaderLabels(["Línea", "Columna", "Lexema"])

        self.tablaErroresLexicos.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        header_errores = self.tablaErroresLexicos.horizontalHeader()
        header_errores.setSectionsMovable(True)
        header_errores.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_errores.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header_errores.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        self.tablaErroresLexicos.setRowCount(0)
        self.tablaErroresLexicos.setRowCount(len(errores))

        for i, (lin, col, lex) in enumerate(errores):
            self.tablaErroresLexicos.setItem(i, 0, QtWidgets.QTableWidgetItem(str(lin)))
            self.tablaErroresLexicos.setItem(i, 1, QtWidgets.QTableWidgetItem(str(col)))
            self.tablaErroresLexicos.setItem(i, 2, QtWidgets.QTableWidgetItem(str(lex)))

    #ANALIZADOR SINTACTICO
    def ejecutar_analisis_sintactico(self):
        print("Botón presionado: Ejecutando análisis sintáctico...")
        codigo = self.codigotextoplano.toPlainText()

        # =========================================================
        # REGLA ESTRICTA: ESCANEO LÉXICO PREVIO
        # =========================================================
        lexer.input(codigo)
        lexer.lineno = 1
        hay_errores_lexicos = False
        while True:
            tok = lexer.token()
            if not tok: break
            if tok.type in ['ERR_DECIMAL', 'ERROR_SIMBOLO']:
                hay_errores_lexicos = True
                break

        if hay_errores_lexicos:
            QtWidgets.QMessageBox.critical(
                self,
                "Análisis Sintáctico Detenido",
                "Se encontraron errores léxicos.\nPor favor, corre el Analizador Léxico para verlos y corrígelos antes de analizar la sintaxis."
            )
            self.ResultadosErrores.setCurrentIndex(0)  # Salta automáticamente a errores léxicos
            return

        lexer.lineno = 1
        # =========================================================
        # EJECUCIÓN SINTÁCTICA
        # =========================================================
        arbol, errores_sint = ejecutar_parser(codigo)

        # ---------------------------------------------------------
        # 1. LLENAR LA TABLA DE ERRORES SINTÁCTICOS DEL DESIGNER
        # ---------------------------------------------------------
        self.tablaErroresSintacticos.setColumnCount(3)
        self.tablaErroresSintacticos.setHorizontalHeaderLabels(["Línea", "Columna", "Descripción del Error"])
        self.tablaErroresSintacticos.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        header_errores = self.tablaErroresSintacticos.horizontalHeader()
        header_errores.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_errores.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header_errores.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        # Hoja de estilos modo oscuro integrado (Sin bloques de colores sólidos invasivos)
        self.tablaErroresSintacticos.setStyleSheet("""
            QTableWidget { background-color: #1E1E1E; color: #E5E5E5; font-size: 13px; gridline-color: #323232; }
            QHeaderView::section { background-color: #2D2D2D; color: #FF6B6B; font-weight: bold; border: 1px solid #3F444D; }
        """)

        # Limpiamos filas viejas de forma segura sin borrar el componente
        self.tablaErroresSintacticos.setRowCount(0)
        self.tablaErroresSintacticos.setRowCount(len(errores_sint))

        # Desempaquetamos la tupla y casteamos a str() obligatoriamente
        for i, item_error in enumerate(errores_sint):
            if isinstance(item_error, tuple) and len(item_error) == 3:
                lin, col, msg = item_error
                self.tablaErroresSintacticos.setItem(i, 0, QtWidgets.QTableWidgetItem(str(lin)))
                self.tablaErroresSintacticos.setItem(i, 1, QtWidgets.QTableWidgetItem(str(col)))
                self.tablaErroresSintacticos.setItem(i, 2, QtWidgets.QTableWidgetItem(str(msg)))
            else:
                # Caso de respaldo por si el error viene en formato de cadena simple
                self.tablaErroresSintacticos.setItem(i, 0, QtWidgets.QTableWidgetItem("-"))
                self.tablaErroresSintacticos.setItem(i, 1, QtWidgets.QTableWidgetItem("-"))
                self.tablaErroresSintacticos.setItem(i, 2, QtWidgets.QTableWidgetItem(str(item_error)))

        # Si hay errores sintácticos, saltamos a la pestaña inferior y detenemos el proceso del árbol
        if errores_sint:
            self.ResultadosErrores.setCurrentIndex(1)  # Enfoca la pestaña de Errores Sintácticos
            QtWidgets.QMessageBox.warning(self, "Sintaxis",
                                          "Se detectaron errores. El árbol mostrará los bloques no válidos.")


        # ---------------------------------------------------------
        # 2. DIBUJAR ÁRBOL SINTÁCTICO EN SU PESTAÑA SUPERIOR ("Sintactico")
        # ---------------------------------------------------------
        if not self.Sintactico.layout():
            self.Sintactico.setLayout(QtWidgets.QVBoxLayout())

        while self.Sintactico.layout().count():
            child = self.Sintactico.layout().takeAt(0)
            if child.widget(): child.widget().deleteLater()

        if arbol:
            tree_widget = QtWidgets.QTreeWidget()
            tree_widget.setHeaderLabel("Estructura Gramatical (AST)")
            tree_widget.setStyleSheet("""
                QTreeWidget { background-color: #21252B; color: #E5E5E5; font-size: 14px; }
                QHeaderView::section { background-color: #0D47A1; color: white; font-weight: bold; }
            """)

            def dibujar_nodo(parent_item, ast_node):
                if ast_node is None: return

                # Protección por si algún nodo no es un objeto TreeNode
                if not hasattr(ast_node, 'tipo_nodo'):
                    QtWidgets.QTreeWidgetItem(parent_item, [f"[Token] -> {str(ast_node)}"])
                    return

                if ast_node.valor:
                    texto = f"{ast_node.tipo_nodo} -> {ast_node.valor}"
                else:
                    texto = f"{ast_node.tipo_nodo}"

                item = QtWidgets.QTreeWidgetItem(parent_item, [texto])

                #Si el nodo representa un error o estructura inválida, lo pintamos de naranja
                if "invalida" in ast_node.tipo_nodo or "error" in ast_node.tipo_nodo:
                    # Creamos un pincel con color naranja brillante para modo oscuro
                    color_naranja = QtGui.QColor("#FF8C00")
                    item.setForeground(0, QtGui.QBrush(color_naranja))

                    # Opcional: Le aplicamos negrita para que resalte aún más en la interfaz
                    fuente_nodo = item.font(0)
                    fuente_nodo.setBold(True)
                    item.setFont(0, fuente_nodo)

                for hijo in ast_node.hijos:
                    dibujar_nodo(item, hijo)

            dibujar_nodo(tree_widget, arbol)
            tree_widget.expandAll()  # Se despliega de forma automática

            self.Sintactico.layout().addWidget(tree_widget)

            # Cambiamos el foco visual a la pestaña del Árbol Sintáctico
            idx_sintactico = self.LCHSS.indexOf(self.Sintactico)
            self.LCHSS.setCurrentIndex(idx_sintactico)
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MiIDE()
    window.show()
    sys.exit(app.exec())