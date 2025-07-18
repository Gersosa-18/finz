from enum import Enum

class CampoEnum(str, Enum):
    PRECIO = "precio"
    VOLUMEN = "volumen"

class TipoCondicionEnum(str, Enum):
    MAYOR_QUE = "mayor_que"
    MENOR_QUE = "menor_que"
    IGUAL_A = "igual_a"

class TipoAlertaEnum(str, Enum):
    SIMPLE = "simple"
    RANGO = "rango"
    PORCENTAJE = "porcentaje"
    COMPUESTA = "compuesta"