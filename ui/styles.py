# ui/styles.py

import streamlit as st


def apply_global_styles():
    """
    Estilos globales de la aplicación.
    Replica la estética de la app de ausencias (Tailwind → CSS directo).
    """

    st.markdown(
        """
        <style>

        /* =========================
           VARIABLES DE COLOR
           ========================= */
        :root {
            /* Identidad azul turquesa */
            --brand-primary: #14b8a6;
            --brand-primary-dark: #0f8f8a;
            --brand-bg-soft: #ecfeff;

            --gray-50: #f9fafb;
            --gray-100: #f3f4f6;
            --gray-200: #e5e7eb;
            --gray-400: #9ca3af;
            --gray-500: #6b7280;
            --gray-700: #374151;
            --gray-900: #111827;

            --card-bg: #ffffff;
        }

        /* =========================
           BASE
           ========================= */
        body {
            background-color: var(--gray-50);
            color: var(--gray-900);
        }

        .block-container {
            padding-top: 1rem !important;
        }

        /* =========================
           CARD
           ========================= */
        .card {
            background: var(--card-bg);
            border-radius: 0.75rem;
            padding: 1.5rem;
            box-shadow:
                0 10px 25px rgba(0, 0, 0, 0.08),
                0 4px 10px rgba(0, 0, 0, 0.04);
        }

        /* =========================
           LOGIN PAGE
           ========================= */
        .login-page {
            min-height: 100vh;
            background: var(--brand-bg-soft);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .login-card {
            width: 100%;
            max-width: 420px;
        }

        .login-title {
            color: #4c1d95;
            font-size: 1.5rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: 0.25rem;
        }

        .login-subtitle {
            text-align: center;
            font-size: 0.9rem;
            color: var(--gray-500);
            margin-bottom: 1.25rem;
        }

        /* =========================
           INPUTS
           ========================= */
        input[type="text"],
        input[type="email"],
        input[type="password"] {
            border-radius: 0.5rem !important;
            padding: 0.6rem 0.75rem !important;
            border: 1px solid var(--gray-200) !important;
            background-color: #f8fafc !important;
        }

        input:focus {
            outline: none !important;
            border-color: var(--brand-primary) !important;
            box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.25) !important;
        }

        /* =========================
           BOTONES
           ========================= */
        .stButton > button {
            width: 100%;
            border-radius: 0.5rem;
            padding: 0.6rem;
            background-color: var(--brand-primary);
            color: white;
            font-weight: 600;
            border: none;
        }

        .stButton > button:hover {
            background-color: var(--brand-primary-dark);
        }

        /* =========================
           HEADER
           ========================= */
        .app-header {
            background: #ffffff;
            border-bottom: 1px solid var(--gray-200);
            padding: 0.75rem 1rem;
            margin-bottom: 1rem;
        }

        /* =========================
           FOOTER
           ========================= */
        .app-footer {
            margin-top: 2rem;
            padding: 1.5rem 0;
            text-align: center;
            font-size: 0.75rem;
            color: var(--gray-400);
        }

        </style>
        """,
        unsafe_allow_html=True,
    )
