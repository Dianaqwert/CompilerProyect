
#Operaciones : inserción y búsqueda.
class TablaSimbolos:
    def __init__(self):
        self.simbolos = {} # Estructura de diccionario

    def insertar(self, nombre, tipo, linea):
        if nombre in self.simbolos:
            return False # Error: Declaración duplicada
        self.simbolos[nombre] = {'tipo': tipo, 'linea': linea}
        return True

    def buscar(self, nombre):
        return self.simbolos.get(nombre, None)