# ui/change_password.py
import streamlit as st

from security.passwords import hash_password
from db.connection import get_db


def render_change_password():
    """
    Vista de cambio de contraseña (primer acceso).
    El usuario debe definir una contraseña antes de continuar.
    """

    user = st.session_state.get("user")
    if not user:
        st.error("Sesión no válida.")
        return

    st.markdown("### 🔐 Establecer contraseña")
    st.write(
        "Es tu primer acceso o tu cuenta no tiene contraseña definida. "
        "Debes establecer una contraseña para poder continuar."
    )

    with st.form("change_password_form"):
        pwd1 = st.text_input(
            "Nueva contraseña",
            type="password",
            help="Mínimo 6 caracteres",
        )
        pwd2 = st.text_input(
            "Repite la contraseña",
            type="password",
        )

        submitted = st.form_submit_button("Guardar contraseña")

    if not submitted:
        return

    # --------------------------
    # VALIDACIONES
    # --------------------------
    if not pwd1 or not pwd2:
        st.error("Debes rellenar ambos campos.")
        return

    if len(pwd1) < 6:
        st.error("La contraseña debe tener al menos 6 caracteres.")
        return

    if pwd1 != pwd2:
        st.error("Las contraseñas no coinciden.")
        return

    # --------------------------
    # ACTUALIZAR EN BD
    # --------------------------
    try:
        new_hash = hash_password(pwd1)

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE users
                    SET password_hash = %s
                    WHERE id = %s
                    """,
                    (new_hash, user["id"]),
                )

        st.success("✅ Contraseña actualizada correctamente.")
        st.info("La sesión se cerrará para que accedas con tu nueva contraseña.")
        
        # Forzar logout completo
        st.session_state.clear()
        st.rerun()

    except Exception as e:
        st.error("❌ Error al actualizar la contraseña.")
        st.exception(e)
