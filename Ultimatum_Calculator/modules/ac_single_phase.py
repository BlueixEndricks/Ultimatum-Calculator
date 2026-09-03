import cmath
import math
import matplotlib.pyplot as plt
import schemdraw
import schemdraw.elements as elm
import streamlit as st


def initialize_ac1_state():
    if "ac1_components" not in st.session_state:
        st.session_state.ac1_components = [
            {
                "type": "Resistor",
                "name": "R1",
                "val": 50.0,
                "unit": "Ω",
                "conn": "Series",
            },
            {
                "type": "Capacitor",
                "name": "C1",
                "val": 20.0,
                "unit": "µF",
                "conn": "Series",
            },
        ]


def build_ac1_schematic(source_v):
    with schemdraw.Drawing(show=False) as d:
        source = (
            elm.SourceSin().up().label(f"Vs (AC)\n{source_v}V", loc="left")
        )
        d += source
        d += elm.Line().right().length(1.5)

        series_comps = [
            c
            for c in st.session_state.ac1_components
            if c["conn"] == "Series"
        ]
        parallel_comps = [
            c
            for c in st.session_state.ac1_components
            if c["conn"] == "Parallel"
        ]

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
        d += elm.Line().left().tox(source.start)
        fig = d.draw()
    return fig


def solve_ac1_circuit(v_source, freq):
    if not st.session_state.ac1_components:
        return None

    omega = 2 * math.pi * freq

    def get_z(comp):
        val = comp["val"]
        c_type = comp["type"]
        if c_type == "Resistor":
            return complex(val, 0.0)
        elif c_type == "Capacitor":
            x_c = 1.0 / (omega * (val * 1e-6)) if val > 0 else 0.0
            return complex(0.0, -x_c)
        elif c_type == "Inductor":
            x_l = omega * (val * 1e-3)
            return complex(0.0, x_l)

    series_comps = [
        c
        for c in st.session_state.ac1_components
        if c["conn"] == "Series"
    ]
    parallel_comps = [
        c
        for c in st.session_state.ac1_components
        if c["conn"] == "Parallel"
    ]

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
    z_deg = math.degrees(z_rad)
    i_total = v_source / z_mag if z_mag > 0 else 0.0

    s_total = v_source * i_total
    pf = math.cos(z_rad)
    p_real = s_total * pf
    q_reactive = s_total * math.sin(z_rad)

    return {
        "z_eq": z_eq,
        "z_mag": z_mag,
        "z_deg": z_deg,
        "i_total": i_total,
        "s_total": s_total,
        "p_real": p_real,
        "q_reactive": q_reactive,
        "pf": pf,
    }


def render_ac1_mode():
    initialize_ac1_state()

    st.header("⚡ Single-Phase AC Engine & Schematic Solver")

    cfg1, cfg2 = st.columns(2)
    with cfg1:
        v_source = st.number_input(
            "Source Voltage RMS (V)", value=120.0, step=5.0, key="ac1_v_src"
        )
    with cfg2:
        freq = st.number_input(
            "Frequency (Hz)", value=60.0, step=5.0, key="ac1_freq"
        )

    st.divider()

    col_inputs, col_preview = st.columns([1.1, 1])

    with col_inputs:
        st.subheader("➕ Component Management")
        ac1, ac2, ac3 = st.columns([1.2, 1, 1])
        with ac1:
            c_type = st.selectbox(
                "Type",
                ["Resistor", "Capacitor", "Inductor"],
                key="ac1_new_type",
            )
        with ac2:
            c_val = st.number_input(
                "Value", value=50.0, step=5.0, key="ac1_new_val"
            )
        with ac3:
            c_conn = st.selectbox(
                "Branch", ["Series", "Parallel"], key="ac1_new_conn"
            )

        unit_map = {"Resistor": "Ω", "Capacitor": "µF", "Inductor": "mH"}

        if st.button("Add to Single-Phase Network", use_container_width=True):
            idx = len(st.session_state.ac1_components) + 1
            prefix = c_type[0]
            st.session_state.ac1_components.append(
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
        for idx, comp in enumerate(list(st.session_state.ac1_components)):
            ec1, ec2, ec3 = st.columns([2, 1.5, 0.5])
            comp["val"] = ec1.number_input(
                f"{comp['name']} ({comp['type']})",
                value=float(comp["val"]),
                key=f"ac1_val_{idx}",
            )
            comp["conn"] = ec2.selectbox(
                "Branch",
                ["Series", "Parallel"],
                index=0 if comp["conn"] == "Series" else 1,
                key=f"ac1_conn_{idx}",
            )
            if ec3.button("❌", key=f"ac1_del_{idx}"):
                st.session_state.ac1_components.pop(idx)
                st.rerun()

    with col_preview:
        st.subheader("Single-Phase Schematic")
        fig = build_ac1_schematic(v_source)
        st.pyplot(fig.fig, use_container_width=True)

    st.divider()

    st.subheader("📊 Single-Phase AC Power & Impedance Analytics")

    if st.button("⚡ Solve Single-Phase Circuit", use_container_width=True):
        res = solve_ac1_circuit(v_source, freq)
        if res:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Equiv Impedance |Z_eq|", f"{res['z_mag']:.2f} Ω")
            m2.metric("Total RMS Current", f"{res['i_total']:.4f} A")
            m3.metric("Real Power (P)", f"{res['p_real']:.2f} W")
            m4.metric("Power Factor", f"{res['pf']:.3f}")

            st.write("---")

            st.write(
                f"**Impedance (Rectangular):** `{res['z_eq'].real:.2f} + {res['z_eq'].imag:.2f}j Ω`"
            )
            st.write(
                f"**Impedance (Polar):** `{res['z_mag']:.2f} Ω  ∠  {res['z_deg']:.2f}°`"
            )
            st.write(
                f"**Apparent Power (S):** `{res['s_total']:.2f} VA` | **Reactive Power (Q):** `{res['q_reactive']:.2f} VAR`"
            )

            log_entry = f">> Single-Phase AC Solved: Z={res['z_mag']:.2f}Ω, I={res['i_total']:.4f}A, P={res['p_real']:.2f}W"
            if "calc_history" in st.session_state:
                st.session_state.calc_history.append(log_entry)