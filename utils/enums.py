# utils/enums.py

# ==============================
# ROLES
# ==============================

ROLE_ADMIN = "admin"
ROLE_JEFE = "jefe"
ROLE_DIRECTOR = "director"
ROLE_SECRETARIO = "secretario"
ROLE_CONVIVENCIA = "convivencia"
ROLE_ORIENTADOR = "orientador"
ROLE_PROFESOR = "profesor"

ROLES_ADMINISTRATIVOS = {
    ROLE_ADMIN,
    ROLE_JEFE,
    ROLE_DIRECTOR,
    ROLE_SECRETARIO,
}

ROLES_TODOS = {
    ROLE_ADMIN,
    ROLE_JEFE,
    ROLE_DIRECTOR,
    ROLE_SECRETARIO,
    ROLE_CONVIVENCIA,
    ROLE_ORIENTADOR,
    ROLE_PROFESOR,
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

# ==============================
# PERMISOS → ROLES AUTORIZADOS
# ==============================

PERMISSIONS_BY_ROLE = {
    PERM_ABRIR_INCIDENCIA: ROLES_TODOS,
    PERM_LISTAR_INCIDENCIAS: ROLES_TODOS,

    PERM_CERRAR_INCIDENCIA: {
        ROLE_ADMIN,
        ROLE_JEFE,
    },

    PERM_HISTORIAL_ALUMNO: {
        ROLE_ADMIN,
        ROLE_JEFE,
        ROLE_DIRECTOR,
        ROLE_SECRETARIO,
        ROLE_CONVIVENCIA,
    },

    PERM_HISTORIAL_PROFESOR: {
        ROLE_ADMIN,
        ROLE_JEFE,
        ROLE_DIRECTOR,
        ROLE_SECRETARIO,
    },

    PERM_RANKING_ALUMNOS: ROLES_ADMINISTRATIVOS | {ROLE_CONVIVENCIA},
    PERM_RANKING_GRUPOS: ROLES_ADMINISTRATIVOS | {ROLE_CONVIVENCIA},
    PERM_RANKING_PROFESORES: ROLES_ADMINISTRATIVOS,

    PERM_EXCURSION: ROLES_ADMINISTRATIVOS,

    PERM_GESTION_ALUMNOS: {
        ROLE_ADMIN,
    },

    PERM_GESTION_USUARIOS: {
        ROLE_ADMIN,
    },

    PERM_BACKUP: {
        ROLE_ADMIN,
    },
}
