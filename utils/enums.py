# utils/enums.py

# ==============================
# ROLES
# ==============================

ROLE_ADMIN = "admin"
ROLE_JEFE = "jefe"
ROLE_PROFESOR = "profesor"
ROLE_CONVIVENCIA = "convivencia"
ROLE_DIRECTOR = "director"

ROLES_ADMINISTRATIVOS = {
    ROLE_ADMIN,
    ROLE_JEFE,
}

ROLES_TODOS = {
    ROLE_ADMIN,
    ROLE_JEFE,
    ROLE_PROFESOR,
    ROLE_CONVIVENCIA,
    ROLE_DIRECTOR,
}


# ==============================
# INCIDENCIAS
# ==============================

ESTADO_ABIERTO = "abierto"
ESTADO_CERRADO = "cerrado"

ESTADOS_INCIDENCIA = [
    ESTADO_ABIERTO,
    ESTADO_CERRADO,
]


GRAVEDAD_LEVE = "leve"
GRAVEDAD_GRAVE = "grave"
GRAVEDAD_MUY_GRAVE = "muy grave"

GRAVEDADES = [
    GRAVEDAD_LEVE,
    GRAVEDAD_GRAVE,
    GRAVEDAD_MUY_GRAVE,
]
