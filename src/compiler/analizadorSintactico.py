import ply.yacc as yacc
from compiler.analizadorLexico import tokens, lexer


# --- ESTRUCTURA DEL NODO DEL ÁRBOL ---
class TreeNode:
    def __init__(self, tipo_nodo, valor="", hijos=None):
        self.tipo_nodo = tipo_nodo
        self.valor = valor
        self.hijos = hijos if hijos is not None else []


# Jerarquía matemática estricta para resolver la precedencia de operadores
precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('right', 'NOT'),
    ('left', 'LT', 'LTE', 'GT', 'GTE', 'EQ', 'NE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'MULT', 'DIV', 'MOD'),
    ('right', 'POW'),
)


# =====================================================================
# REGLAS GRAMATICALES
# =====================================================================

# El parser ejecuta la regla: programa -> main { lista_declaracion }
def p_programa(p):
    '''programa : MAIN LBRACE lista_declaracion RBRACE
                | lista_declaracion'''
    nodo_main = TreeNode("main", "main")
    nodo_lista = p[3] if len(p) == 5 else p[1]
    if nodo_lista:
        nodo_lista.tipo_nodo = "lista_declaracion"
    p[0] = TreeNode("programa", hijos=[nodo_main, nodo_lista])


# El parser ejecuta la regla: lista_declaracion -> lista_declaracion declaración | declaración
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


# El parser ejecuta la regla: declaración -> declaración_variable | sentencia
def p_declaracion(p):
    '''declaracion : declaracion_variable
                   | sentencia'''
    p[0] = p[1]


# El parser ejecuta la regla: declaración_variable -> tipo lista_ids;
def p_declaracion_variable(p):
    '''declaracion_variable : tipo lista_ids SEMI'''
    nodo_tipo = TreeNode("tipo", p[1])
    nodo_ids = TreeNode("identificadores", hijos=p[2])
    p[0] = TreeNode("declaracion_variable", hijos=[nodo_tipo, nodo_ids])


# El parser ejecuta la regla: tipo -> int | float
def p_tipo(p):
    '''tipo : INT_DECL
            | FLOAT_DECL'''
    p[0] = p[1]


# El parser ejecuta la regla: lista_ids -> id , lista_ids | id
def p_lista_ids(p):
    '''lista_ids : ID COMMA lista_ids
                 | ID'''
    if len(p) == 4:
        p[0] = [TreeNode("id", p[1])] + p[3]
    else:
        p[0] = [TreeNode("id", p[1])]


# El parser ejecuta la regla: sentencia -> selección | iteración | repetición | sent_in | sent_out | asignación | inc_dec | expresión_suelta
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


# Recuperación en modo pánico para sentencias rotas: busca un punto y coma o llave de cierre
def p_sentencia_error(p):
    '''sentencia : error SEMI
                 | error RBRACE'''
    p[0] = TreeNode("sentencia_invalida", valor="Estructura No Válida")


# El parser ejecuta la regla: expresión_suelta -> expresión;
def p_expresion_suelta(p):
    '''expresion_suelta : expresion SEMI'''
    p[0] = TreeNode("expresion_suelta", hijos=[p[1]])


# El parser ejecuta la regla: asignación -> id = expresión;
def p_asignacion(p):
    '''asignacion : ID ASSIGN expresion SEMI'''
    nodo_id = TreeNode("id", p[1])
    nodo_sent = TreeNode("sent_expresion", hijos=[p[3]])
    p[0] = TreeNode("asignacion", hijos=[nodo_id, nodo_sent])


# El parser ejecuta la regla: selección -> if expresión then lista_declaracion [ else lista_declaracion ] end;
def p_seleccion(p):
    '''seleccion : IF expresion THEN lista_declaracion END SEMI
                 | IF expresion THEN lista_declaracion END
                 | IF expresion THEN lista_declaracion ELSE lista_declaracion END SEMI
                 | IF expresion THEN lista_declaracion ELSE lista_declaracion END'''
    hijos_then = p[4].hijos if (p[4] and hasattr(p[4], 'hijos')) else []
    nodo_then = TreeNode("bloque_then", hijos=hijos_then)

    if len(p) == 7 or len(p) == 6:
        p[0] = TreeNode("condicional_if", hijos=[p[2], nodo_then])
    else:
        hijos_else = p[6].hijos if (p[6] and hasattr(p[6], 'hijos')) else []
        nodo_else = TreeNode("bloque_else", hijos=hijos_else)
        p[0] = TreeNode("condicional_if_else", hijos=[p[2], nodo_then, nodo_else])


# El parser ejecuta la regla: iteración -> while expresión lista_declaracion end ;
def p_iteracion(p):
    '''iteracion : WHILE expresion lista_declaracion END SEMI
                 | WHILE expresion lista_declaracion END'''
    hijos_cuerpo = p[3].hijos if (p[3] and hasattr(p[3], 'hijos')) else []
    nodo_cuerpo = TreeNode("cuerpo_while", hijos=hijos_cuerpo)
    p[0] = TreeNode("iteracion_while", hijos=[p[2], nodo_cuerpo])


# El parser ejecuta la regla: repetición -> do lista_declaracion while expresión ; | do lista_declaracion until expresión ;
def p_repeticion(p):
    '''repeticion : DO lista_declaracion WHILE expresion SEMI
                  | DO lista_declaracion WHILE expresion
                  | DO lista_declaracion UNTIL expresion SEMI
                  | DO lista_declaracion UNTIL expresion'''
    hijos_cuerpo = p[2].hijos if (p[2] and hasattr(p[2], 'hijos')) else []
    nodo_cuerpo = TreeNode("cuerpo_ciclo", hijos=hijos_cuerpo)

    if p[3] == 'while':
        p[0] = TreeNode("ciclo_do_while", hijos=[nodo_cuerpo, p[4]])
    else:
        p[0] = TreeNode("ciclo_do_until", hijos=[nodo_cuerpo, p[4]])


# El parser ejecuta la regla: sent_in -> cin id;
def p_sent_in(p):
    '''sent_in : CIN ID SEMI'''
    p[0] = TreeNode("lectura_cin", hijos=[TreeNode("id", p[2])])


# El parser ejecuta la regla: sent_out -> cout expresión;
def p_sent_out(p):
    '''sent_out : COUT expresion SEMI'''
    p[0] = TreeNode("escritura_cout", hijos=[p[2]])


# El parser ejecuta la regla: inc_dec -> id ++ ; | id -- ;
def p_inc_dec(p):
    '''inc_dec : ID INC SEMI
               | ID DEC SEMI'''
    p[0] = TreeNode("expresion_unaria", p[2], [TreeNode("id", p[1])])


# El parser ejecuta la regla: expresión -> expresión_simple [rel_op expresión_simple]
def p_expresion(p):
    '''expresion : expresion_simple rel_op expresion_simple
                 | expresion_simple'''
    if len(p) == 4:
        p[0] = TreeNode("expresion_relacional", p[2], [p[1], p[3]])
    else:
        p[0] = p[1]


# El parser ejecuta la regla: rel_op -> < | <= | > | >= | == | !=
def p_rel_op(p):
    '''rel_op : LT
              | LTE
              | GT
              | GTE
              | EQ
              | NE'''
    p[0] = p[1]


# El parser ejecuta la regla: expresión_simple -> termino {suma_op termino }
def p_expresion_simple(p):
    '''expresion_simple : expresion_simple suma_op termino
                        | termino'''
    if len(p) == 4:
        p[0] = TreeNode("expresion_aditiva", p[2], [p[1], p[3]])
    else:
        p[0] = p[1]


# El parser ejecuta la regla: suma_op -> + | -
def p_suma_op(p):
    '''suma_op : PLUS
               | MINUS'''
    p[0] = p[1]


# El parser ejecuta la regla: termino -> factor {mult_op factor}
def p_termino(p):
    '''termino : termino mult_op factor
               | factor'''
    if len(p) == 4:
        p[0] = TreeNode("expresion_multiplicativa", p[2], [p[1], p[3]])
    else:
        p[0] = p[1]


# El parser ejecuta la regla: mult_op -> * | / | %
def p_mult_op(p):
    '''mult_op : MULT
               | DIV
               | MOD'''
    p[0] = p[1]


# El parser ejecuta la regla: factor -> componente [ ^ componente]
def p_factor(p):
    '''factor : componente POW componente
              | componente'''
    if len(p) == 4:
        p[0] = TreeNode("expresion_potencia", p[2], [p[1], p[3]])
    else:
        p[0] = p[1]


# El parser ejecuta la regla: componente -> (expresion) | numero | id | !componente | expresión log_op expresión
def p_componente_agrupacion(p):
    '''componente : LPAREN expresion RPAREN'''
    p[0] = p[2]


# Obliga a consumir tokens hasta el paréntesis de cierre )
def p_componente_error(p):
    '''componente : LPAREN error RPAREN'''
    p[0] = TreeNode("expresion_invalida", valor="Error en Condición")


def p_componente_not(p):
    '''componente : NOT componente'''
    p[0] = TreeNode("op_logico", p[1], [p[2]])


def p_componente_logico(p):
    '''componente : expresion log_op expresion'''
    p[0] = TreeNode("expresion_logica", p[2], [p[1], p[3]])


# El parser ejecuta la regla: log_op -> && | ||
def p_log_op(p):
    '''log_op : AND
              | OR'''
    p[0] = p[1]


def p_componente_num(p):
    '''componente : INT
                  | REAL'''
    p[0] = TreeNode("numero", str(p[1]))


def p_componente_id(p):
    '''componente : ID'''
    p[0] = TreeNode("id", p[1])


def p_empty(p):
    'empty :'
    pass


# --- MANEJO DE ERRORES SINTÁCTICOS ---
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


parser = yacc.yacc()


def ejecutar_parser(codigo):
    global errores_sintacticos, codigo_fuente_actual
    errores_sintacticos = []
    codigo_fuente_actual = codigo
    arbol = parser.parse(codigo, lexer=lexer)
    return arbol, errores_sintacticos