import ply.yacc as yacc
from compiler.analizadorLexico import tokens, lexer


# --- NUEVA FUNCIÓN PARA CALCULAR COLUMNA EN EL SINTÁCTICO ---
def get_col(lexpos):
    global codigo_fuente_actual
    if lexpos is None or lexpos < 0 or not codigo_fuente_actual:
        return "-"
    line_start = codigo_fuente_actual.rfind('\n', 0, lexpos) + 1
    return (lexpos - line_start) + 1


# --- ESTRUCTURA DEL NODO DEL ÁRBOL ---
class TreeNode:
    def __init__(self, tipo_nodo, valor="", hijos=None, linea="-", columna="-"):
        self.tipo_nodo = tipo_nodo
        self.valor = valor
        self.hijos = hijos if hijos is not None else []
        self.linea = linea
        self.columna = columna

        # Atributos semánticos
        self.type = None
        self.dtype = None
        self.val = None


precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('right', 'NOT'),
    ('left', 'LT', 'LTE', 'GT', 'GTE', 'EQ', 'NE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'MULT', 'DIV', 'MOD'),
    ('right', 'POW'),
)


def p_programa(p):
    '''programa : MAIN LBRACE lista_declaracion RBRACE
                | lista_declaracion'''
    nodo_main = TreeNode("main", "main", linea=p.lineno(1), columna=get_col(p.lexpos(1)))
    nodo_lista = p[3] if len(p) == 5 else p[1]
    if nodo_lista:
        nodo_lista.tipo_nodo = "lista_declaracion"
    p[0] = TreeNode("programa", hijos=[nodo_main, nodo_lista])


def p_lista_declaracion(p):
    '''lista_declaracion : lista_declaracion declaracion
                         | declaracion'''
    if len(p) == 3:
        if p[1] and p[1].tipo_nodo == "lista_declaracion":
            if p[2]: p[1].hijos.append(p[2])
            p[0] = p[1]
        else:
            hijos = [p[2]] if p[2] else []
            p[0] = TreeNode("lista_declaracion", hijos=hijos)
    else:
        p[0] = TreeNode("lista_declaracion", hijos=[p[1]])


def p_declaracion(p):
    '''declaracion : declaracion_variable
                   | sentencia'''
    p[0] = p[1]


def p_declaracion_variable(p):
    '''declaracion_variable : tipo lista_ids SEMI'''
    nodo_tipo = TreeNode("tipo", p[1], linea=p.lineno(1), columna=get_col(p.lexpos(1)))
    nodo_ids = TreeNode("identificadores", hijos=p[2])
    p[0] = TreeNode("declaracion_variable", hijos=[nodo_tipo, nodo_ids], linea=p.lineno(1),
                    columna=get_col(p.lexpos(1)))


def p_tipo(p):
    '''tipo : INT_DECL
            | FLOAT_DECL'''
    p[0] = p[1]


def p_lista_ids(p):
    '''lista_ids : ID COMMA lista_ids
                 | ID'''
    nodo_id = TreeNode("id", p[1], linea=p.lineno(1), columna=get_col(p.lexpos(1)))
    if len(p) == 4:
        p[0] = [nodo_id] + p[3]
    else:
        p[0] = [nodo_id]


def p_sentencia(p):
    '''sentencia : asignacion
                 | seleccion
                 | iteracion
                 | repeticion
                 | sent_in
                 | sent_out
                 | inc_dec
                 | expresion_suelta'''
    p[0] = p[1]


def p_sentencia_error(p):
    '''sentencia : error SEMI
                 | error RBRACE'''
    p[0] = TreeNode("sentencia_invalida", valor="Estructura No Válida")
    if(hasattr(p,'parser')): # para reportar errores seguidos
        p.parser.errok()

def p_expresion_suelta(p):
    '''expresion_suelta : expresion SEMI'''
    p[0] = TreeNode("expresion_suelta", hijos=[p[1]])


def p_asignacion(p):
    '''asignacion : ID ASSIGN expresion SEMI'''
    nodo_id = TreeNode("id", p[1], linea=p.lineno(1), columna=get_col(p.lexpos(1)))
    nodo_sent = TreeNode("sent_expresion", hijos=[p[3]])
    p[0] = TreeNode("asignacion", hijos=[nodo_id, nodo_sent], linea=p.lineno(2), columna=get_col(p.lexpos(2)))


def p_seleccion(p):
    '''seleccion : IF expresion THEN lista_declaracion END SEMI
                 | IF expresion THEN lista_declaracion END
                 | IF expresion THEN lista_declaracion ELSE lista_declaracion END SEMI
                 | IF expresion THEN lista_declaracion ELSE lista_declaracion END'''
    hijos_then = p[4].hijos if (p[4] and hasattr(p[4], 'hijos')) else []
    nodo_then = TreeNode("bloque_then", hijos=hijos_then)

    if len(p) == 7 or len(p) == 6:
        p[0] = TreeNode("condicional_if", hijos=[p[2], nodo_then], linea=p.lineno(1), columna=get_col(p.lexpos(1)))
    else:
        hijos_else = p[6].hijos if (p[6] and hasattr(p[6], 'hijos')) else []
        nodo_else = TreeNode("bloque_else", hijos=hijos_else)
        p[0] = TreeNode("condicional_if_else", hijos=[p[2], nodo_then, nodo_else], linea=p.lineno(1),
                        columna=get_col(p.lexpos(1)))


def p_iteracion(p):
    '''iteracion : WHILE expresion lista_declaracion END SEMI
                 | WHILE expresion lista_declaracion END'''
    hijos_cuerpo = p[3].hijos if (p[3] and hasattr(p[3], 'hijos')) else []
    nodo_cuerpo = TreeNode("cuerpo_while", hijos=hijos_cuerpo)
    p[0] = TreeNode("iteracion_while", hijos=[p[2], nodo_cuerpo], linea=p.lineno(1), columna=get_col(p.lexpos(1)))


def p_repeticion(p):
    '''repeticion : DO lista_declaracion WHILE expresion SEMI
                  | DO lista_declaracion WHILE expresion
                  | DO lista_declaracion UNTIL expresion SEMI
                  | DO lista_declaracion UNTIL expresion'''
    hijos_cuerpo = p[2].hijos if (p[2] and hasattr(p[2], 'hijos')) else []
    nodo_cuerpo = TreeNode("cuerpo_ciclo", hijos=hijos_cuerpo)

    if p[3] == 'while':
        p[0] = TreeNode("ciclo_do_while", hijos=[nodo_cuerpo, p[4]], linea=p.lineno(1), columna=get_col(p.lexpos(1)))
    else:
        p[0] = TreeNode("ciclo_do_until", hijos=[nodo_cuerpo, p[4]], linea=p.lineno(1), columna=get_col(p.lexpos(1)))


def p_sent_in(p):
    '''sent_in : CIN ID SEMI'''
    nodo_id = TreeNode("id", p[2], linea=p.lineno(2), columna=get_col(p.lexpos(2)))
    p[0] = TreeNode("lectura_cin", hijos=[nodo_id], linea=p.lineno(1), columna=get_col(p.lexpos(1)))


def p_sent_out(p):
    '''sent_out : COUT expresion SEMI'''
    p[0] = TreeNode("escritura_cout", hijos=[p[2]], linea=p.lineno(1), columna=get_col(p.lexpos(1)))


def p_inc_dec(p):
    '''inc_dec : ID INC SEMI
               | ID DEC SEMI'''
    nodo_id = TreeNode("id", p[1], linea=p.lineno(1), columna=get_col(p.lexpos(1)))
    p[0] = TreeNode("expresion_unaria", p[2], [nodo_id], linea=p.lineno(2), columna=get_col(p.lexpos(2)))


def p_expresion(p):
    '''expresion : expresion_simple rel_op expresion_simple
                 | expresion_simple'''
    if len(p) == 4:
        p[0] = TreeNode("expresion_relacional", p[2], [p[1], p[3]], linea=p[1].linea, columna=p[1].columna)
    else:
        p[0] = p[1]


def p_rel_op(p):
    '''rel_op : LT
              | LTE
              | GT
              | GTE
              | EQ
              | NE'''
    p[0] = p[1]


def p_expresion_simple(p):
    '''expresion_simple : expresion_simple suma_op termino
                        | termino'''
    if len(p) == 4:
        p[0] = TreeNode("expresion_aditiva", p[2], [p[1], p[3]], linea=p[1].linea, columna=p[1].columna)
    else:
        p[0] = p[1]


def p_suma_op(p):
    '''suma_op : PLUS
               | MINUS'''
    p[0] = p[1]


def p_termino(p):
    '''termino : termino mult_op factor
               | factor'''
    if len(p) == 4:
        p[0] = TreeNode("expresion_multiplicativa", p[2], [p[1], p[3]], linea=p[1].linea, columna=p[1].columna)
    else:
        p[0] = p[1]


def p_mult_op(p):
    '''mult_op : MULT
               | DIV
               | MOD'''
    p[0] = p[1]


def p_factor(p):
    '''factor : componente POW componente
              | componente'''
    if len(p) == 4:
        p[0] = TreeNode("expresion_potencia", p[2], [p[1], p[3]], linea=p[1].linea, columna=p[1].columna)
    else:
        p[0] = p[1]


def p_componente_agrupacion(p):
    '''componente : LPAREN expresion RPAREN'''
    p[0] = p[2]


def p_componente_error(p):
    '''componente : LPAREN error RPAREN'''
    p[0] = TreeNode("expresion_invalida", valor="Error en Condición")


def p_componente_not(p):
    '''componente : NOT componente'''
    p[0] = TreeNode("op_logico", p[1], [p[2]], linea=p.lineno(1), columna=get_col(p.lexpos(1)))


def p_componente_logico(p):
    '''componente : expresion log_op expresion'''
    p[0] = TreeNode("expresion_logica", p[2], [p[1], p[3]], linea=p[1].linea, columna=p[1].columna)


def p_log_op(p):
    '''log_op : AND
              | OR'''
    p[0] = p[1]


def p_componente_num(p):
    '''componente : INT
                  | REAL'''
    p[0] = TreeNode("numero", str(p[1]), linea=p.lineno(1), columna=get_col(p.lexpos(1)))


def p_componente_id(p):
    '''componente : ID'''
    p[0] = TreeNode("id", p[1], linea=p.lineno(1), columna=get_col(p.lexpos(1)))


errores_sintacticos = []
codigo_fuente_actual = ""


def p_error(p):
    global errores_sintacticos
    if p:
        inicio_linea = codigo_fuente_actual.rfind('\n', 0, p.lexpos) + 1
        columna = (p.lexpos - inicio_linea) + 1
        errores_sintacticos.append((p.lineno, columna, f"Error de sintaxis en el lexema '{p.value}'"))
    else:
        errores_sintacticos.append(("-", "-", "Error: Estructura sintáctica incompleta al final del código."))


class NullLogger(object):
    def critical(self, msg, *args, **kwargs): pass

    def error(self, msg, *args, **kwargs): pass

    def warning(self, msg, *args, **kwargs): pass

    def info(self, msg, *args, **kwargs): pass

    def debug(self, msg, *args, **kwargs): pass


log_silencioso = NullLogger()

parser = yacc.yacc(
    debug=False,
    write_tables=False,
    debuglog=log_silencioso,
    errorlog=log_silencioso
)


def ejecutar_parser(codigo):
    global errores_sintacticos, codigo_fuente_actual
    errores_sintacticos = []
    codigo_fuente_actual = codigo
    lexer.lineno = 1
    arbol = parser.parse(codigo, lexer=lexer)
    return arbol, errores_sintacticos