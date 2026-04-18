import ply.lex as lex

# Palabras reservadas (Color 4)
reserved = {
    'if': 'IF', 'else': 'ELSE', 'end': 'END', 'do': 'DO', 'while': 'WHILE',
    'switch': 'SWITCH', 'case': 'CASE', 'int': 'INT_DECL', 'float': 'FLOAT_DECL',
    'main': 'MAIN', 'cin': 'CIN', 'cout': 'COUT'
}

tokens = [
    'ID', 'INT', 'REAL', 'PLUS', 'MINUS', 'MULT', 'DIV', 'MOD', 'POW',
    'INC', 'DEC', 'LT', 'LTE', 'GT', 'GTE', 'NE', 'EQ', 'AND', 'OR', 'NOT',
    'LBRACE', 'RBRACE', 'LPAREN', 'RPAREN', 'COMMA', 'SEMI', 'STRING',
    'CHAR', 'ASSIGN', 'ERR_DECIMAL'
] + list(reserved.values())

# Operadores (Color 5 y 6)
t_INC, t_DEC, t_EQ, t_NE = r'\+\+', r'--', r'==', r'!='
t_LTE, t_GTE = r'<=', r'>='
t_AND, t_OR = r'&&', r'\|\|'
t_PLUS, t_MINUS, t_MULT, t_DIV = r'\+', r'-', r'\*', r'/'
t_MOD, t_POW, t_NOT = r'%', r'\^', r'!'
t_ASSIGN, t_LT, t_GT = r'=', r'<', r'>'
t_LBRACE, t_RBRACE = r'\{', r'\}'
t_LPAREN, t_RPAREN = r'\(', r'\)'
t_COMMA, t_SEMI = r',', r';'

t_ignore = ' \t'

# 1. COMENTARIO DE UNA LÍNEA (##)
# Debe ir primero para que PLY le dé prioridad si encuentra dos gatos juntos.
def t_COMMENT_SIMPLE(t):
    r'\#\#.*'
    pass

# 2. COMENTARIO MULTILÍNEA (# ... #)
def t_COMMENT_MULTI(t):
    r'\#(.|\n)*?\#'
    t.lexer.lineno += t.value.count('\n')
    pass

def t_ERR_DECIMAL(t):
    r'\d+\.(?!\d)'# Captura el error "32.algo" o "32."
    return t

##SALTOS EN LINEA Y OPERADORES == Y ++
def t_INC(t):
    r'\+\s*\+'
    t.lexer.lineno += t.value.count('\n') # Si hubo un salto de línea en medio, lo contamos
    t.value = "++"                        # Forzamos a que el texto limpio sea "++"
    return t

def t_DEC(t):
    r'-\s*-'
    t.lexer.lineno += t.value.count('\n')
    t.value = "--"
    return t

def t_EQ(t):
    r'=\s*='
    t.lexer.lineno += t.value.count('\n')
    t.value = "=="
    return t

def t_NE(t):
    r'!\s*='
    t.lexer.lineno += t.value.count('\n')
    t.value = "!="
    return t

# 1. PRIMERO LA REGLA MÁS ESPECÍFICA (Números Reales/Decimales)
def t_REAL(t):
    r'\d+\.\d+'
    return t

# 2. LUEGO LA REGLA GENERAL (Números Enteros)
def t_INT(t):
    r'\d+'
    return t

def t_ID(t):
    r'[a-zA-Z][a-zA-Z0-9]*'
    t.type = reserved.get(t.value, 'ID')
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Función para calcular la columna
def find_column(input, token):
    line_start = input.rfind('\n', 0, token.lexpos) + 1
    return (token.lexpos - line_start) +1

# Regla de error general para símbolos fuera del alfabeto (ej: @)
def t_error(t):
    t.type = 'ERROR_SIMBOLO'
    t.value = t.value[0]
    t.lexer.skip(1)
    return t


lexer = lex.lex()

