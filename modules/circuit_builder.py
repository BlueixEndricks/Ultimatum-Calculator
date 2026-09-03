import cmath
import math
import matplotlib.pyplot as plt
import schemdraw
import schemdraw.elements as elm
import streamlit as st


def initialize_state():
    """Ensures session state variables are set up when the module loads."""
    if "circuit_components" not in st.session_state:
        st.session_state.circuit_components = [
            {
                "type": "Resistor",
                "name": "R1",
                "val": 100.0,
                "unit": "Ω",
                "conn": "Series",
            },
            {
                "type": "Resistor",
                "name": "R2",
                "val": 220.0,
                "unit": "Ω",
                "conn": "Parallel",
            },
        ]


def build_schematic(source_type, source_v):
    """Draws custom circuits supporting mixed Series and Parallel branches."""
    with schemdraw.Drawing(show=False) as d:
        if source_type == "DC":
            source = (
                elm.SourceV().up().label(f"Vs (DC)\n{source_v}V", loc="left")
            )
        else:
            source = (
                elm.SourceSin().up().label(f"Vs (AC)\n{source_v}V", loc="left")
            )

        d += source
        d += elm.Line().right().length(1.5)

        series_comps = [
            c
            for c in st.session_state.circuit_components
            if c["conn"] == "Series"
        ]
        parallel_comps = [
            c
            for c in st.session_state.circuit_components
            if c["conn"] == "Parallel"
        ]

        d += elm.Dot().label("Node 1", loc="top")

        for comp in series_comps:
            c_label = f"{comp['name']}\n{comp['val']}{comp['unit']}"
            if comp["type"] == "Resistor":
                d += elm.Resistor().right().label(c_label)
            elif comp["type"] == "Capacitor":
                d += elm.Capacitor().right().label(c_label)
            elif comp["type"] == "Inductor":
                d += elm.Inductor().right().label(c_label)
            d += elm.Line().right().length(1.0)

        if parallel_comps:
            d += elm.Line().right().length(1.0)
            d += elm.Dot().label("Node 2", loc="top")

            for i, comp in enumerate(parallel_comps):
                c_label = f"{comp['name']}\n{comp['val']}{comp['unit']}"
                d.push()
                if comp["type"] == "Resistor":
                    d += (
                        elm.Resistor()
                        .down()
                        .toy(source.start)
                        .label(c_label)
                    )
                elif comp["type"] == "Capacitor":
                    d += (
                        elm.Capacitor()
                        .down()
                        .toy(source.start)
                        .label(c_label)
                    )
                elif comp["type"] == "Inductor":
                    d += (
                        elm.Inductor()
                        .down()
                        .toy(source.start)
                        .label(c_label)
                    )
                d.pop()
                if i < len(parallel_comps) - 1:
                    d += elm.Line().right().length(2.5)

        d += elm.Line().down().toy(source.start)
        d += elm.Dot().label("Ref Ground (0V)", loc="bottom")
        d += elm.Line().left().tox(source.start)

        fig = d.draw()
    return fig


def run_full_circuit_analysis(source_type, source_v, freq):
    """Calculates Network Total, Nodal Analysis (KCL), and Branch/Mesh metrics."""
    if not st.session_state.circuit_components:
        return None

    omega = 2 * math.pi * freq if source_type == "AC" else 0.0

    def get_z(comp):
        val = comp["val"]
        c_type = comp["type"]
        if c_type == "Resistor":
            return complex(val, 0.0)
        elif c_type == "Capacitor":
            if source_type == "DC":
                return complex(1e9, 0.0)
            x_c = 1.0 / (omega * (val * 1e-6)) if val > 0 else 0.0
            return complex(0.0, -x_c)
        elif c_type == "Inductor":
            if source_type == "DC":
                return complex(0.0, 0.0)
            x_l = omega * (val * 1e-3)
            return complex(0.0, x_l)

    series_comps = [
        c
        for c in st.session_state.circuit_components
        if c["conn"] == "Series"
    ]
    parallel_comps = [
        c
        for c in st.session_state.circuit_components
        if c["conn"] == "Parallel"
    ]

    # Calculate Series & Parallel Branch Impedances
    z_series = sum((get_z(c) for c in series_comps), complex(0.0, 0.0))

    if parallel_comps:
        inv_z_sum = sum(
            1.0 / get_z(c) for c in parallel_comps if abs(get_z(c)) > 0
        )
        z_parallel = (
            1.0 / inv_z_sum if abs(inv_z_sum) > 0 else complex(0.0, 0.0)
        )
    else:
        z_parallel = complex(0.0, 0.0)

    z_eq = z_series + z_parallel
    z_mag, z_rad = cmath.polar(z_eq)
    i_total = source_v / z_mag if z_mag > 0 else 0.0

    # Correct Nodal Analysis Calculations
    v_node1 = complex(source_v, 0.0)
    
    # Voltage drop across series network
    v_drop_series = i_total * abs(z_series)
    v_node2_mag = max(0.0, source_v - v_drop_series) if parallel_comps else 0.0
    v_node2 = complex(v_node2_mag, 0.0)

    # Component Branch Breakdown
    branch_data = []
    for comp in st.session_state.circuit_components:
        z_c = get_z(comp)
        z_c_mag, _ = cmath.polar(z_c)

        if comp["conn"] == "Series":
            v_comp = i_total * z_c_mag
            i_comp = i_total
        else:
            v_comp = abs(v_node2)
            i_comp = v_comp / z_c_mag if z_c_mag > 0 else 0.0

        p_comp = (v_comp * i_comp) if comp["type"] == "Resistor" else 0.0

        branch_data.append(
            {
                "name": comp["name"],
                "type": comp["type"],
                "conn": comp["conn"],
                "val_str": f"{comp['val']}{comp['unit']}",
                "v_drop": v_comp,
                "i_branch": i_comp,
                "p_diss": p_comp,
            }
        )

    s_total = source_v * i_total
    pf = math.cos(z_rad)
    p_real = s_total * pf
    q_reactive = s_total * math.sin(z_rad)

    return {
        "z_eq": z_eq,
        "z_mag": z_mag,
        "z_deg": math.degrees(z_rad),
        "i_total": i_total,
        "v_node1": v_node1,
        "v_node2": v_node2,
        "p_real": p_real,
        "q_reactive": q_reactive,
        "pf": pf,
        "branches": branch_data,
    }


def render_circuit_builder():
    initialize_state()

    st.header("⚡ Ultimate Circuit Schematic & Matrix Solver")

    cfg_col1, cfg_col2, cfg_col3 = st.columns(3)
    with cfg_col1:
        source_type = st.selectbox(
            "Source Type", ["DC", "AC"], key="cb_src_type"
        )
    with cfg_col2:
        source_v = st.number_input(
            "Source Voltage (V)", value=12.0, step=1.0, key="cb_v_src"
        )
    with cfg_col3:
        freq = st.number_input(
            "Frequency (Hz)",
            value=60.0,
            step=5.0,
            disabled=(source_type == "DC"),
            key="cb_freq",
        )

    st.divider()

    col_inputs, col_preview = st.columns([1.1, 1])

    with col_inputs:
        st.subheader("➕ Add Component")

        ac1, ac2, ac3 = st.columns([1.2, 1, 1])
        with ac1:
            c_type = st.selectbox(
                "Type",
                ["Resistor", "Capacitor", "Inductor"],
                key="new_c_type",
            )
        with ac2:
            c_val = st.number_input(
                "Value", value=100.0, step=10.0, key="new_c_val"
            )
        with ac3:
            c_conn = st.selectbox(
                "Branch", ["Series", "Parallel"], key="new_c_conn"
            )

        unit_map = {"Resistor": "Ω", "Capacitor": "µF", "Inductor": "mH"}

        if st.button("Add Component", use_container_width=True):
            idx = len(st.session_state.circuit_components) + 1
            prefix = c_type[0]
            st.session_state.circuit_components.append(
                {
                    "type": c_type,
                    "name": f"{prefix}{idx}",
                    "val": c_val,
                    "unit": unit_map[c_type],
                    "conn": c_conn,
                }
            )
            st.rerun()

        st.subheader("⚙️ Active Components")
        for idx, comp in enumerate(list(st.session_state.circuit_components)):
            ec1, ec2, ec3 = st.columns([2, 1.5, 0.5])
            comp["val"] = ec1.number_input(
                f"{comp['name']} ({comp['type']})",
                value=float(comp["val"]),
                key=f"val_{idx}",
            )
            comp["conn"] = ec2.selectbox(
                "Placement",
                ["Series", "Parallel"],
                index=0 if comp["conn"] == "Series" else 1,
                key=f"conn_{idx}",
            )

            if ec3.button("❌", key=f"del_{idx}"):
                st.session_state.circuit_components.pop(idx)
                st.rerun()

    with col_preview:
        st.subheader("Circuit Schematic")
        fig = build_schematic(source_type, source_v)
        st.pyplot(fig.fig, use_container_width=True)

    st.divider()

    st.subheader("🔬 Comprehensive Circuit Analysis Data")

    if st.button(
        "⚡ Run Full Nodal & Mesh Analysis", use_container_width=True
    ):
        data = run_full_circuit_analysis(source_type, source_v, freq)

        if data:
            # 1. Network Level Metrics
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Equiv Impedance |Z_eq|", f"{data['z_mag']:.2f} Ω")
            m2.metric("Total Current I_total", f"{data['i_total']:.4f} A")
            m3.metric("Real Power (P)", f"{data['p_real']:.2f} W")
            m4.metric("Power Factor", f"{data['pf']:.3f}")

            st.write("---")

            # 2. Nodal & Mesh Voltage Matrix
            n_col1, n_col2 = st.columns(2)

            with n_col1:
                st.markdown("### 📍 Nodal Analysis (KCL)")
                st.write(
                    "**Reference Node 0 (Ground):** `0.00 V` (0° Datum)"
                )
                st.write(
                    f"**Node 1 (Source Rail):** `{data['v_node1'].real:.2f} V`"
                )
                st.write(
                    f"**Node 2 (Parallel Junction):** `{data['v_node2'].real:.2f} V`"
                )

            with n_col2:
                st.markdown("### 🌀 Mesh Analysis (KVL)")
                st.write(
                    f"**Mesh Loop 1 Current:** `{data['i_total']:.4f} A`"
                )
                st.write(
                    f"**Total Loop Voltage Drop:** `{source_v:.2f} V` (Balance = 0V)"
                )

            st.write("---")

            # 3. Component Breakdown Table (Markdown - SAC Safe)
            st.markdown("### 📋 Component-by-Component Branch Matrix")

            md_table = (
                "| Component | Type | Placement | Value | Voltage Drop | Branch Current | Power Dissipation |\n"
                "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            )

            for b in data["branches"]:
                md_table += f"| **{b['name']}** | {b['type']} | {b['conn']} | `{b['val_str']}` | `{b['v_drop']:.2f} V` | `{b['i_branch']:.4f} A` | `{b['p_diss']:.2f} W` |\n"

            st.markdown(md_table)

            # Log calculation to Sidebar
            log_entry = f">> Full Nodal/Mesh Solved [{source_type}]: Node1={data['v_node1'].real:.1f}V, Node2={data['v_node2'].real:.1f}V, I_tot={data['i_total']:.4f}A"
            if "calc_history" in st.session_state:
                st.session_state.calc_history.append(log_entry)