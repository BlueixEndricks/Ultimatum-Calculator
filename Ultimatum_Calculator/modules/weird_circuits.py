import math
import matplotlib.pyplot as plt
import schemdraw
import schemdraw.elements as elm
import streamlit as st


def draw_bridge_schematic(r1, r2, r3, r4, rx, v_in):
    """Renders a clean Wheatstone Bridge schematic."""
    with schemdraw.Drawing(show=False) as d:
        source = elm.SourceV().up().label(f"Vs\n{v_in}V", loc="left")
        d += source
        d += elm.Line().right().length(2.0)

        # Top Bridge Rail (Node A)
        d += elm.Dot().label("Node A", loc="top")
        
        # Branch 1 (R1 -> Node C -> R3)
        d.push()
        d += elm.Resistor().down().left().label(f"R1\n{r1}Ω")
        d += elm.Dot().label("Node C", loc="left")
        d.push()
        d += elm.Resistor().right().label(f"Rx\n{rx}Ω")
        d += elm.Dot().label("Node D", loc="right")
        d.pop()
        d += elm.Resistor().down().right().label(f"R3\n{r3}Ω")
        d.pop()

        # Branch 2 (R2 -> Node D -> R4)
        d += elm.Resistor().down().right().label(f"R2\n{r2}Ω")
        d += elm.Resistor().down().left().label(f"R4\n{r4}Ω")

        # Bottom Ground Rail
        d += elm.Line().down().toy(source.start)
        d += elm.Line().left().tox(source.start)

        fig = d.draw()
    return fig


def solve_bridge_network(r1, r2, r3, r4, rx, v_in):
    """Solves arbitrary 5-resistor bridge mesh network using Delta-Wye Transformation."""
    # Delta-Wye transformation of top delta (R1, R2, Rx)
    r_sum = r1 + r2 + rx
    if r_sum == 0:
        return None

    r_a = (r1 * r2) / r_sum
    r_b = (r1 * rx) / r_sum
    r_c = (r2 * rx) / r_sum

    # Equivalent branches after transformation
    branch1 = r_b + r3
    branch2 = r_c + r4
    denom = branch1 + branch2
    r_parallel = (branch1 * branch2) / denom if denom > 0 else 0.0

    r_eq = r_a + r_parallel
    i_total = v_in / r_eq if r_eq > 0 else 0.0

    # Bridge Balance Check: (R1/R2) == (R3/R4)
    is_balanced = math.isclose(r1 * r4, r2 * r3, rel_tol=1e-3)
    
    denom_v1 = r1 + r3
    denom_v2 = r2 + r4
    v_c = (v_in * r3 / denom_v1) if denom_v1 > 0 else 0.0
    v_d = (v_in * r4 / denom_v2) if denom_v2 > 0 else 0.0
    v_bridge = 0.0 if is_balanced else abs(v_c - v_d)

    return {
        "r_eq": r_eq,
        "i_total": i_total,
        "is_balanced": is_balanced,
        "v_bridge": v_bridge,
    }


def render_weird_circuits_tab():
    st.header("🌀 Weird & Arbitrary Mesh Networks")
    st.caption("Solves Non-Series/Parallel Grids, Wheatstone Bridges, and Delta-Wye Conversions")

    col1, col2 = st.columns([1.1, 1])

    with col1:
        st.subheader("⚙️ Bridge Network Resistors")
        v_in = st.number_input("Input Voltage Vs (V)", value=12.0, key="wc_v")
        r1 = st.number_input("R1 (Top Left Ω)", value=100.0, key="wc_r1")
        r2 = st.number_input("R2 (Top Right Ω)", value=100.0, key="wc_r2")
        rx = st.number_input("Rx (Center Bridge Ω)", value=50.0, key="wc_rx")
        r3 = st.number_input("R3 (Bottom Left Ω)", value=100.0, key="wc_r3")
        r4 = st.number_input("R4 (Bottom Right Ω)", value=100.0, key="wc_r4")

    with col2:
        st.subheader("Bridge Network Schematic")
        fig = draw_bridge_schematic(r1, r2, r3, r4, rx, v_in)
        st.pyplot(fig.fig, use_container_width=True)

    st.divider()

    if st.button("⚡ Solve Mesh Grid Network", use_container_width=True):
        res = solve_bridge_network(r1, r2, r3, r4, rx, v_in)
        if res:
            m1, m2, m3 = st.columns(3)
            m1.metric("Equivalent Resistance (R_eq)", f"{res['r_eq']:.2f} Ω")
            m2.metric("Total Input Current", f"{res['i_total']:.4f} A")
            m3.metric("Bridge Differential (V_cd)", f"{res['v_bridge']:.3f} V")

            if res["is_balanced"]:
                st.success("⚖️ **Bridge Status:** Perfectly Balanced! Zero current flows across Rx.")
            else:
                st.warning("⚡ **Bridge Status:** Unbalanced Network. Current flows across central branch Rx.")

            log_entry = f">> Bridge Mesh Solved: R_eq={res['r_eq']:.2f}Ω, I_total={res['i_total']:.4f}A, Balanced={res['is_balanced']}"
            if "calc_history" in st.session_state:
                st.session_state.calc_history.append(log_entry)