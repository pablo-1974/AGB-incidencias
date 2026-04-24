import streamlit as st
from db.users import create_user

def render_create_first_admin():
    st.subheader("Crear administrador inicial")

    st.info(
        "No existe ningún usuario en el sistema. "
        "Cree el administrador inicial para comenzar."
    )

    name = st.text_input("Nombre completo")
    email = st.text_input("Email")
    password = st.text_input("Contraseña", type="password")

    if st.button("Crear administrador", use_container_width=True):
        if not name or not email or not password:
            st.error("Todos los campos son obligatorios.")
            return

        try:
            create_user(
                name=name,
                email=email,
                password=password,
                role="admin",
            )
        except Exception as e:
            st.error("No se pudo crear el administrador.")
            st.exception(e)
            return

        st.success("Administrador creado correctamente. Reiniciando…")
        st.rerun()
