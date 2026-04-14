from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import QRegularExpression


class LexicalHighlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        super().__init__(parent)
        self.highlighting_rules = []

        # ==========================================
        # 1. FORMATOS DE COLOR
        # ==========================================
        keyword_format = self.create_format("#C678DD", bold=True)  # Color 4 (Morado)
        number_format = self.create_format("#D19A66")  # Color 1 (Naranja/Amarillo)

        # NUEVO: Azul claro para que los identificadores resalten y no sean blancos
        id_format = self.create_format("#61AFEF")  # Color 2 (Azul)

        comment_format = self.create_format("#5C6370", italic=True)  # Color 3 (Gris)
        operator_format = self.create_format("#56B6C2")  # Color 5 (Cyan)
        logic_rel_format = self.create_format("#E06C75")  # Color 6 (Rojo Coral)

        # NUEVO: Blanco absoluto para Símbolos y Asignación
        symbol_format = self.create_format("#FFFFFF")

        # NUEVO: Rojo brillante y subrayado para Errores
        error_format = self.create_format("#FF0000", bold=True, underline=True)

        # ==========================================
        # 2. REGLAS (EL ORDEN IMPORTA MUCHO)
        # ==========================================

        # REGLA DE ERRORES: Detecta "32.algo", "32." o símbolos no válidos como "@"
        self.highlighting_rules.append((QRegularExpression(r'\d+\.[a-zA-Z_]+|\d+\.(?!\d)|@'), error_format))

        # SÍMBOLOS Y ASIGNACIÓN (Blanco)
        self.highlighting_rules.append((QRegularExpression(r'[=,\(\)\{\}\[\];]'), symbol_format))

        # OPERADORES (Lógicos/Relacionales y Aritméticos)
        self.highlighting_rules.append((QRegularExpression(r'<=|>=|==|!=|<|>|&&|\|\||!'), logic_rel_format))
        self.highlighting_rules.append((QRegularExpression(r'[\+\-\*/%\^]'), operator_format))

        # IDENTIFICADORES (Azul) - Se aplica a cualquier palabra que no empiece con número
        self.highlighting_rules.append((QRegularExpression(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'), id_format))

        # PALABRAS RESERVADAS (Morado) - Se pone DESPUÉS de los identificadores para que los sobrescriba
        keywords = [
            r'\bif\b', r'\belse\b', r'\bend\b', r'\bdo\b', r'\bwhile\b', r'\buntil\b',
            r'\bswitch\b', r'\bcase\b', r'\bint\b', r'\bfloat\b', r'\breal\b',
            r'\bmain\b', r'\bcin\b', r'\bcout\b', r'\bthen\b'
        ]
        for pattern in keywords:
            self.highlighting_rules.append((QRegularExpression(pattern), keyword_format))

        # NÚMEROS (Enteros y Decimales válidos)
        self.highlighting_rules.append((QRegularExpression(r'\b\d+(\.\d+)?\b'), number_format))

        # COMENTARIOS SIMPLES (#)
        self.highlighting_rules.append((QRegularExpression(r'\#\#.*'), comment_format))
        self.multiline_comment_format = comment_format

        self.start_expression = QRegularExpression(r'(?<!#)\#(?!#)')
        self.end_expression = QRegularExpression(r'(?<!#)\#(?!#)')
    # ==========================================
    # 3. MODIFICACIÓN PARA ACEPTAR SUBRAYADO
    # ==========================================
    def create_format(self, color_hex, bold=False, italic=False, underline=False):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color_hex))
        if bold: fmt.setFontWeight(QFont.Weight.Bold)
        if italic: fmt.setFontItalic(True)

        # Magia para el subrayado de error
        if underline:
            fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SpellCheckUnderline)
            fmt.setUnderlineColor(QColor("#FF0000"))

        return fmt

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            expression = QRegularExpression(pattern)
            iterator = expression.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

        # Lógica para comentarios multilínea ##
        self.setCurrentBlockState(0)
        start_index = 0
        if self.previousBlockState() != 1:
            start_index = self.start_expression.match(text).capturedStart()

        while start_index >= 0:
            match = self.end_expression.match(text, start_index + 1)
            end_index = match.capturedStart()
            comment_length = 0
            if end_index == -1:
                self.setCurrentBlockState(1)
                comment_length = len(text) - start_index
            else:
                comment_length = end_index - start_index + 1
            self.setFormat(start_index, comment_length, self.multiline_comment_format)
            start_index = self.start_expression.match(text, start_index + comment_length).capturedStart()