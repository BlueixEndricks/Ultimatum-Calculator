import math
import streamlit as st

# Import custom modules from the modules/ folder
from modules import ac_single_phase, ac_three_phase, circuit_builder
from modules.parser import evaluate_expression
from modules import ac_single_phase, ac_three_phase, circuit_builder, peem_engine
from modules import ac_single_phase, ac_three_phase, circuit_builder, peem_engine, weird_circuits

# Configure Web Page Layout
st.set_page_config(
    page_title="Ultimatum Calculator", page_icon="⚡", layout="wide"
)

# Global Variable & History State Management
if "user_vars" not in st.session_state:
    st.session_state.user_vars = {"ans": 0.0, "pi": float(math.pi)}

if "calc_history" not in st.session_state:
    st.session_state.calc_history = []  # Command window output history


def log_history(entry: str):
    """Helper function to append calculations to the command log."""
    st.session_state.calc_history.append(entry)


st.title("🌐 The Ultimatum Calculator")
st.caption(
    "Unified Multi-Mode Solver: Electronics, AC Power, & Symbolic Science"
)

# Master Tab Layout
tab_dc, tab_ac1, tab_ac3, tab_symbolic, tab_visual, tab_peem, tab_weird = st.tabs(
    [
        "🔌 DC Circuits",
        "⚡ AC Single-Phase",
        "🌀 AC Three-Phase",
        "🔬 Symbolic Algebra",
        "🎨 Visual Builder",
        "⚡ PEEM Mode",
        "🌀 Weird Mesh Networks",
    ]
)

# --- TAB 1: DC CIRCUITS ---
with tab_dc:
    st.header("DC Circuit Calculations")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Ohm's Law Solver")
        v_in = st.number_input("Voltage (V)", value=0.0, key="dc_v")
        i_in = st.number_input("Current (A)", value=0.0, key="dc_i")
        r_in = st.number_input("Resistance (Ω)", value=0.0, key="dc_r")

        if st.button("Solve DC Parameter"):
            if v_in == 0 and i_in > 0 and r_in > 0:
                res = f"V = {i_in * r_in:.4f} V"
                st.success(res)
                log_history(f">> DC Ohm's Law: {res}")
            elif i_in == 0 and v_in > 0 and r_in > 0:
                res = f"I = {v_in / r_in:.4f} A"
                st.success(res)
                log_history(f">> DC Ohm's Law: {res}")
            elif r_in == 0 and v_in > 0 and i_in > 0:
                res = f"R = {v_in / i_in:.4f} Ω"
                st.success(res)
                log_history(f">> DC Ohm's Law: {res}")
            else:
                st.warning(
                    "Leave exactly ONE value set to 0 to calculate it."
                )

    with col2:
        st.subheader("Resistor Combination Bank")
        r_list_str = st.text_input(
            "Enter resistors (e.g. 10, 20, 50):", "10, 20"
        )
        if r_list_str:
            try:
                vals = [
                    float(x.strip())
                    for x in r_list_str.split(",")
                    if x.strip()
                ]
                r_ser = sum(vals)
                r_par = (
                    1 / sum(1 / x for x in vals if x > 0)
                    if min(vals) > 0
                    else 0
                )
                st.metric("Series Resistance", f"{r_ser:.2f} Ω")
                st.metric("Parallel Resistance", f"{r_par:.2f} Ω")
            except ValueError:
                st.error("Invalid resistor list.")

# --- TAB 2: AC SINGLE-PHASE ---
with tab_ac1:
    ac_single_phase.render_ac1_mode()

# --- TAB 3: AC THREE-PHASE ---
with tab_ac3:
    ac_three_phase.render_ac3_mode()

# --- TAB 4: SYMBOLIC ALGEBRA & GENERAL MATH ---
with tab_symbolic:
    st.header("🔬 Scientific & Symbolic Engine")

    calc_mode = st.radio(
        "Select Operation Mode:",
        ["Basic / Variable Assignment", "Algebra (Solve for X)"],
        horizontal=True,
    )

    if calc_mode == "Basic / Variable Assignment":
        st.caption(
            "Use this mode to evaluate math or store variables (e.g., `x = 25`, `a = 10`, or `a + 5`)."
        )
    else:
        st.caption(
            "Use this mode to solve equations for `x` (e.g., `2*x + 10 = 50` or `x^2 - 9 = 0`)."
        )

    # st.form captures the ENTER key automatically when typing in inputs!
    with st.form(key="symbolic_math_form", clear_on_submit=False):
        user_input = st.text_input(
            "Input Expression (Press Enter to Calculate):", key="sym_input"
        )

        # Submit button for form (triggered by click OR pressing Enter)
        submit_btn = st.form_submit_button("Calculate ↵")

    if submit_btn and user_input:
        res = evaluate_expression(
            user_input, st.session_state.user_vars, calc_mode
        )
        st.code(f"Result: {res}")
        log_history(f">> [{calc_mode}] {user_input} => {res}")

    # Universal cross-version HTML script injection
    st.markdown(
        """
        <script>
            const inputs = window.parent.document.querySelectorAll('input[type="text"]');
            if (inputs.length > 0) {
                inputs[inputs.length - 1].focus();
            }
        </script>
        """,
        unsafe_allow_html=True,
    )

# --- TAB 5: VISUAL SCHEMATIC BUILDER ---
with tab_visual:
    circuit_builder.render_circuit_builder()

    # --- TAB 6: PEEM MODE ---
with tab_peem:
    peem_engine.render_peem_tab()

    # --- TAB 7: Weird Mesh Networks ---
with tab_weird:
    weird_circuits.render_weird_circuits_tab()

# --- SIDEBAR: OCTAVE-STYLE COMMAND WINDOW & VARIABLE MONITOR ---
with st.sidebar:
    st.subheader("🖥️ Command History Log")

    if st.session_state.calc_history:
        # Format the log text like an Octave / MATLAB command window console
        console_output = "\n".join(st.session_state.calc_history)
        st.code(console_output, language="text")

        if st.button("Clear History"):
            st.session_state.calc_history = []
            st.rerun()
    else:
        st.info("No calculations performed yet.")

    st.divider()

    st.subheader("📊 Variable Monitor")
    for k, v in st.session_state.user_vars.items():
        st.write(f"**{k.upper()}** : `{v}`")
import sys
from pathlib import Path

# Explicitly insert the absolute path of the app's root folder at the head of sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Import modules
from modules import ac_single_phase, ac_three_phase, circuit_builder, peem_engine, weird_circuits
