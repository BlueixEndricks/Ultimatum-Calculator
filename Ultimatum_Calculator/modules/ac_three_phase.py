import math
import matplotlib.pyplot as plt
import schemdraw
import schemdraw.elements as elm
import streamlit as st


def draw_three_phase_schematic(v_line, config, r_val, x_val):
    """Renders authentic 3-Phase Wye and Delta schematics."""
    with schemdraw.Drawing(show=False) as d:
        if config == "Wye (Y)":
            # 3-Phase Wye (Y) Layout
            v_ph = v_line / math.sqrt(3)
            d += elm.Dot().label("N", loc="left")
            d.push()
            d += elm.Resistor().up().label(f"Za ({r_val}Ω)")
            d += elm.SourceSin().left().label(f"Va\n{v_ph:.0f}V")
            d.pop()
            d.push()
            d += elm.Resistor().right().label(f"Zb ({r_val}Ω)")
            d += elm.SourceSin().down().label(f"Vb\n{v_ph:.0f}V")
            d.pop()
            d += elm.Resistor().down().label(f"Zc ({r_val}Ω)")
            d += elm.SourceSin().left().label(f"Vc\n{v_ph:.0f}V")
        else:
            # 3-Phase Delta (Δ) Closed-Loop Layout
            d += elm.SourceSin().up().label(f"Vab ({v_line:.0f}V)", loc="left")
            d += elm.Line().right().length(2.0)
            d.push()
            d += elm.Resistor().down().label(f"Z_AB\n({r_val}Ω)")
            d.pop()
            d += elm.Line().right().length(2.5)
            d.push()
            d += elm.Resistor().down().label(f"Z_BC\n({r_val}Ω)")
            d.pop()
            d += elm.Line().right().length(2.5)
            d += elm.Resistor().down().label(f"Z_CA\n({r_val}Ω)")
            d += elm.Line().left().tox(0)

        fig = d.draw()
    return fig


def render_ac3_mode():
    st.header("🌀 3-Phase AC Engine (Wye & Delta)")
    st.caption("Complete 3-Phase Power, Delta Phase Currents, & Load Analysis")

    col_inputs, col_preview = st.columns([1.1, 1])

    with col_inputs:
        st.subheader("⚙️ System Configuration")

        config = st.selectbox(
            "Connection Type", ["Wye (Y)", "Delta (Δ)"], key="ac3_config"
        )
        v_line = st.number_input(
            "Line Voltage V_LL (V)", value=480.0, step=10.0, key="ac3_v_line"
        )

        st.markdown("**Per-Phase Load Impedance**")
        r_phase = st.number_input(
            "Phase Resistance R (Ω)", value=12.0, step=1.0, key="ac3_r"
        )
        x_phase = st.number_input(
            "Phase Reactance X (Ω)", value=9.0, step=1.0, key="ac3_x"
        )

    with col_preview:
        st.subheader("3-Phase Schematic Topology")
        fig = draw_three_phase_schematic(v_line, config, r_phase, x_phase)
        st.pyplot(fig.fig, use_container_width=True)

    st.divider()

    st.subheader("📊 3-Phase Power & Current Analysis")

    if st.button("⚡ Analyze 3-Phase Load", use_container_width=True):
        z_mag = math.sqrt(r_phase**2 + x_phase**2)
        pf = r_phase / z_mag if z_mag > 0 else 1.0

        if config == "Wye (Y)":
            v_phase = v_line / math.sqrt(3)
            i_phase = v_phase / z_mag if z_mag > 0 else 0.0
            i_line = i_phase
        else:
            v_phase = v_line
            i_phase = v_phase / z_mag if z_mag > 0 else 0.0
            i_line = i_phase * math.sqrt(3)

        p_total = math.sqrt(3) * v_line * i_line * pf
        s_total = math.sqrt(3) * v_line * i_line
        q_total = math.sqrt(max(0.0, s_total**2 - p_total**2))

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Line Current (I_line)", f"{i_line:.2f} A")
        m2.metric("Phase Current (I_phase)", f"{i_phase:.2f} A")
        m3.metric("Total Power (P)", f"{p_total / 1000:.2f} kW")
        m4.metric("Power Factor", f"{pf:.3f}")

        st.write("---")

        md_ac3 = (
            "| Metric | Formula / Relationship | Calculated Value |\n"
            "| :--- | :--- | :--- |\n"
            f"| **Phase Voltage (V_phase)** | `V_LL / √3` if Wye else `V_LL` | `{v_phase:.1f} V` |\n"
            f"| **Phase Impedance |Z|** | `√(R² + X²)` | `{z_mag:.2f} Ω` |\n"
            f"| **Apparent Power (S)** | `√3 × V_LL × I_line` | `{s_total / 1000:.2f} kVA` |\n"
            f"| **Reactive Power (Q)** | `√(S² - P²)` | `{q_total / 1000:.2f} kVAR` |\n"
        )
        st.markdown(md_ac3)

        log_entry = f">> 3-Phase [{config}]: V_LL={v_line}V, I_line={i_line:.2f}A, P={p_total/1000:.2f}kW"
        if "calc_history" in st.session_state:
            st.session_state.calc_history.append(log_entry)