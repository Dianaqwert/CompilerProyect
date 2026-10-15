# FUNCION : recibe al ast y su raiz y lo recorre
#el recorrido depende del tipo de atributo

#H ATRIBUTOS HEREDADOS:
# recorrido: arriba hacia abajo o de izquierda a derecha
# para propagar el atributo .dtype desde el tipo hacia los identificadores y luego insertarlos en la tabla de simbolos

#ATRIBUTOS SINTETIZADOS:
# son expresiones con un recorrido postorden (hijos a padre) para .type
# para .val -> es desde las hojas hasta la raiz
# compiler/analizadorSemantico.py

class TablaSimbolos:
    def __init__(self):
        self.simbolos = {}
        self.contador_memoria = 1  # Simulador de dirección de memoria (1, 2, 3...)

    def insertar(self, nombre, tipo_dato, linea):
        if nombre in self.simbolos:
            return False
        # Guardamos el tipo, la memoria asignada, y la primera línea donde nace
        self.simbolos[nombre] = {
            'tipo': tipo_dato,
            'memoria': self.contador_memoria,
            'lineas': [int(linea)] if linea != "-" else []
        }
        self.contador_memoria += 1
        return True

    def buscar(self, nombre):
        return self.simbolos.get(nombre, None)

    def registrar_uso(self, nombre, linea):
        """Añade la línea al historial permitiendo duplicados si se usa varias veces en la misma línea."""
        if nombre in self.simbolos and linea != "-":
            self.simbolos[nombre]['lineas'].append(int(linea))
            self.simbolos[nombre]['lineas'].sort()  # Mantiene los números ordenados

class AnalizadorSemantico:
    def __init__(self):
        self.tabla_simbolos = TablaSimbolos()
        self.errores = []

    def registrar_error(self, nodo, mensaje):
        """Extrae la línea y columna del nodo y almacena el error como tupla."""
        linea = getattr(nodo, 'linea', '-')
        columna = getattr(nodo, 'columna', '-')
        self.errores.append((linea, columna, mensaje))

    def analizar(self, ast_raiz):
        self.errores.clear()
        self.tabla_simbolos = TablaSimbolos()
        self.recorrer(ast_raiz)
        return self.tabla_simbolos, self.errores

    def recorrer(self, nodo):
        if nodo is None:
            return

        # 1. EVALUACIÓN DESCENDENTE (ATRIBUTOS HEREDADOS)
        if nodo.tipo_nodo == "declaracion_variable":
            nodo_tipo = nodo.hijos[0]
            tipo_dato = nodo_tipo.valor
            nodo.dtype = tipo_dato

            nodo_ids = nodo.hijos[1]
            for hijo_id in nodo_ids.hijos:
                hijo_id.dtype = tipo_dato
                # PASAMOS LA LÍNEA AQUÍ
                exito = self.tabla_simbolos.insertar(hijo_id.valor, tipo_dato, hijo_id.linea)
                if not exito:
                    self.registrar_error(hijo_id, f"Declaración duplicada: '{hijo_id.valor}' ya fue declarada.")
                    self.tabla_simbolos.registrar_uso(hijo_id.valor, hijo_id.linea)
            return

        # 2. RECORRIDO POSTORDEN (Visitar hijos primero)
        for hijo in nodo.hijos:
            self.recorrer(hijo)

        # 3. SÍNTESIS DE ATRIBUTOS Y COMPROBACIÓN DE TIPOS
        if nodo.tipo_nodo == "numero":
            if "." in str(nodo.valor):
                nodo.type = "float"
                nodo.val = float(nodo.valor)
            else:
                nodo.type = "int"
                nodo.val = int(nodo.valor)

        elif nodo.tipo_nodo == "id":
            simbolo = self.tabla_simbolos.buscar(nodo.valor)
            if simbolo:
                nodo.type = simbolo['tipo']
                # REGISTRAMOS EL USO DE LA VARIABLE EN ESTA LÍNEA
                self.tabla_simbolos.registrar_uso(nodo.valor, nodo.linea)
            else:
                nodo.type = "error"
                self.registrar_error(nodo, f"Uso de variable no declarada '{nodo.valor}'.")

        elif nodo.tipo_nodo in ["expresion_aditiva", "expresion_multiplicativa", "expresion_potencia"]:
            tipo_izq = nodo.hijos[0].type
            tipo_der = nodo.hijos[1].type

            if tipo_izq == "error" or tipo_der == "error":
                nodo.type = "error"
            elif tipo_izq == "float" or tipo_der == "float":
                nodo.type = "float"
            else:
                nodo.type = "int"

            if nodo.hijos[0].val is not None and nodo.hijos[1].val is not None:
                try:
                    v1, v2 = nodo.hijos[0].val, nodo.hijos[1].val
                    op = nodo.valor
                    if op == '+':
                        nodo.val = v1 + v2
                    elif op == '-':
                        nodo.val = v1 - v2
                    elif op == '*':
                        nodo.val = v1 * v2
                    elif op == '/' and v2 != 0:
                        nodo.val = v1 / v2
                except:
                    pass

        elif nodo.tipo_nodo in ["expresion_relacional", "expresion_logica"]:
            tipo_izq = nodo.hijos[0].type
            tipo_der = nodo.hijos[1].type
            if tipo_izq == "error" or tipo_der == "error":
                nodo.type = "error"
            else:
                nodo.type = "bool"

        elif nodo.tipo_nodo == "asignacion":
            nodo_id = nodo.hijos[0]
            nodo_expr = nodo.hijos[1].hijos[0]

            simbolo = self.tabla_simbolos.buscar(nodo_id.valor)
            if not simbolo:
                self.registrar_error(nodo_id, f"Asignación a variable no declarada '{nodo_id.valor}'.")
                nodo.type = "error"
            else:
                tipo_var = simbolo['tipo']
                tipo_expr = nodo_expr.type

                if tipo_expr != "error":
                    if tipo_var == "int" and tipo_expr == "float":
                        self.registrar_error(nodo,
                                             f"Incompatibilidad: No se puede asignar 'float' a la variable entera '{nodo_id.valor}'.")
                nodo.type = tipo_var

        elif nodo.tipo_nodo == "lectura_cin":
            nodo_id = nodo.hijos[0]
            if not self.tabla_simbolos.buscar(nodo_id.valor):
                self.registrar_error(nodo_id, f"Lectura (cin) en variable no declarada '{nodo_id.valor}'.")

        elif nodo.tipo_nodo == "escritura_cout":
            if nodo.hijos[0].type == "error":
                self.registrar_error(nodo, "Intentando imprimir (cout) una expresión con errores.")

        elif nodo.tipo_nodo == "expresion_unaria":
            nodo_id = nodo.hijos[0]
            simbolo = self.tabla_simbolos.buscar(nodo_id.valor)
            if not simbolo:
                self.registrar_error(nodo_id, f"Operación (++ o --) sobre variable no declarada '{nodo_id.valor}'.")
            elif simbolo['tipo'] not in ["int", "float"]:
                self.registrar_error(nodo, f"La operación '{nodo.valor}' requiere variable numérica.")