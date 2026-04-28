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

FRANJAS_HORARIAS = (
    "1ª",
    "2ª",
    "3ª",
    "Recreo",
    "4ª",
    "5ª",
    "6ª",
)

FRANJA_ORDEN = {
    "1ª": 1,
    "2ª": 2,
    "3ª": 3,
    "Recreo": 4,
    "4ª": 5,
    "5ª": 6,
    "6ª": 7,
}

# ==============================
# PERMISOS FUNCIONALES
# ==============================

PERM_ABRIR_INCIDENCIA = "abrir_incidencia"
PERM_LISTAR_INCIDENCIAS = "listar_incidencias"
PERM_CERRAR_INCIDENCIA = "cerrar_incidencia"

PERM_HISTORIAL_ALUMNO = "historial_alumno"
PERM_HISTORIAL_PROFESOR = "historial_profesor"

PERM_RANKING_ALUMNOS = "ranking_alumnos"
PERM_RANKING_GRUPOS = "ranking_grupos"
PERM_RANKING_PROFESORES = "ranking_profesores"

PERM_EXCURSION = "excursion"

PERM_GESTION_ALUMNOS = "gestion_alumnos"
PERM_GESTION_USUARIOS = "gestion_usuarios"
PERM_BACKUP = "backup"
