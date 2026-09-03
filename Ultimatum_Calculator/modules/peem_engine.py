import cmath
import math
import matplotlib.pyplot as plt
import numpy as np
import schemdraw
import schemdraw.elements as elm
import streamlit as st


def initialize_peem_state():
    """Initializes dynamic component list for PEEM Mode."""
    if "peem_components" not in st.session_state:
        st.session_state.peem_components = [
            {
                "type": "Resistor",
                "name": "R1",
                "val": 50.0,
                "unit": "Ω",
                "conn": "Series",
            },
            {
                "type": "Inductor",
                "name": "L1",
                "val": 10.0,
                "unit": "mH",
                "conn": "Series",
            },
            {
                "type": "Capacitor",
                "name": "C1",
                "val": 1.0,
                "unit": "µF",
                "conn": "Parallel",
            },
        ]


def build_peem_schematic(source_type, source_v):
    """Draws custom PEEM schematic supporting dynamic series and parallel branches."""
    with schemdraw.Drawing(show=False) as d:
        if source_type == "AC Sweep":
            source = (
                elm.SourceSin().up().label(f"Vs (AC)\n{source_v}V", loc="left")
            )
        else:
            source = (
                elm.SourceV().up().label(f"Vs (Step)\n{source_v}V", loc="left")
            )

        d += source
        d += elm.Line().right().length(1.5)

        series_comps = [
            c
            for c in st.session_state.peem_components
            if c["conn"] == "Series"
        ]
        parallel_comps = [
            c
            for c in st.session_state.peem_components
            if c["conn"] == "Parallel"
        ]

        # Draw Series branch components along top rail
        for comp in series_comps:
            c_label = f"{comp['name']}\n{comp['val']}{comp['unit']}"
            if comp["type"] == "Resistor":
                d += elm.Resistor().right().label(c_label)
            elif comp["type"] == "Capacitor":
                d += elm.Capacitor().right().label(c_label)
            elif comp["type"] == "Inductor":
                d += elm.Inductor().right().label(c_label)
            d += elm.Line().right().length(1.0)

        # Draw Parallel branches
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

        # Ground return wire
        d += elm.Line().down().toy(source.start)
        d += elm.Line().left().tox(source.start)

        fig = d.draw()
    return fig


def render_peem_tab():
    initialize_peem_state()

    st.header("⚡ Professional Electrical Engineers Mode (PEEM)")
    st.caption(
        "High-Speed Interactive Topology Builder, Bode Sweep Engine, & Full Analytics"
    )

    # Top Control Bar
    cfg1, cfg2, cfg3 = st.columns(3)
    with cfg1:
        peem_mode = st.selectbox(
            "Analysis Domain",
            [
                "📈 Frequency Response (Bode Domain)",
                "⏱️ Time Domain (Step Response)",
            ],
            key="peem_domain",
        )
    with cfg2:
        source_v = st.number_input(
            "Source Voltage (V)", value=10.0, step=1.0, key="peem_v_src"
        )
    with cfg3:
        if "Bode" in peem_mode:
            f_start = st.number_input(
                "Start Frequency (Hz)", value=10.0, key="peem_fstart"
            )
            f_stop = st.number_input(
                "Stop Frequency (Hz)", value=100000.0, key="peem_fstop"
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
                key="peem_new_type",
            )
        with ac2:
            c_val = st.number_input(
                "Value", value=50.0, step=5.0, key="peem_new_val"
            )
        with ac3:
            c_conn = st.selectbox(
                "Branch", ["Series", "Parallel"], key="peem_new_conn"
            )

        unit_map = {"Resistor": "Ω", "Capacitor": "µF", "Inductor": "mH"}

        if st.button("Add to PEEM Network", use_container_width=True):
            idx = len(st.session_state.peem_components) + 1
            prefix = c_type[0]
            st.session_state.peem_components.append(
                {
                    "type": c_type,
                    "name": f"{prefix}{idx}",
                    "val": c_val,
                    "unit": unit_map[c_type],
                    "conn": c_conn,
                }
            )
            st.rerun()

        st.subheader("⚙️ Live Network Components")
        for idx, comp in enumerate(list(st.session_state.peem_components)):
            ec1, ec2, ec3 = st.columns([2, 1.5, 0.5])
            comp["val"] = ec1.number_input(
                f"{comp['name']} ({comp['type']})",
                value=float(comp["val"]),
                key=f"peem_val_{idx}",
            )
            comp["conn"] = ec2.selectbox(
                "Branch",
                ["Series", "Parallel"],
                index=0 if comp["conn"] == "Series" else 1,
                key=f"peem_conn_{idx}",
            )

            if ec3.button("❌", key=f"peem_del_{idx}"):
                st.session_state.peem_components.pop(idx)
                st.rerun()

    with col_preview:
        st.subheader("PEEM Schematic Topology")
        src_label = "AC Sweep" if "Bode" in peem_mode else "Step"
        fig = build_peem_schematic(src_label, source_v)
        st.pyplot(fig.fig, use_container_width=True)

    st.divider()

    # --- GRAPH & ANALYTICS SECTION ---
    st.subheader("📊 Dynamic Engineering Response & Analysis")

    # Aggregate R, L, C parameters for calculation engine
    r_total = sum(
        c["val"]
        for c in st.session_state.peem_components
        if c["type"] == "Resistor"
    )
    r_total = max(r_total, 1e-3)  # Prevent divide-by-zero

    l_mH = sum(
        c["val"]
        for c in st.session_state.peem_components
        if c["type"] == "Inductor"
    )
    l_H = l_mH * 1e-3

    c_uF = sum(
        c["val"]
        for c in st.session_state.peem_components
        if c["type"] == "Capacitor"
    )
    c_F = c_uF * 1e-6

    # --- FREQUENCY RESPONSE DOMAIN ---
    if "Bode" in peem_mode:
        f_res = (
            1.0 / (2 * math.pi * math.sqrt(l_H * c_F))
            if (l_H * c_F) > 0
            else 0.0
        )
        q_factor = (
            (1.0 / r_total) * math.sqrt(l_H / c_F)
            if (r_total > 0 and c_F > 0 and l_H > 0)
            else 0.0
        )

        freqs = np.logspace(np.log10(f_start), np.log10(f_stop), 500)
        omegas = 2 * np.pi * freqs

        z_r = r_total
        z_l = 1j * omegas * l_H
        z_c = 1.0 / (1j * omegas * c_F) if c_F > 0 else np.zeros_like(omegas)
        h_jw = z_c / (z_r + z_l + z_c) if (l_H > 0 and c_F > 0) else z_r / (z_r + z_l)

        magnitude_db = 20 * np.log10(np.abs(h_jw))
        phase_deg = np.angle(h_jw, deg=True)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 4.5), sharex=True)
        fig.patch.set_facecolor("#0e1117")
        for ax in (ax1, ax2):
            ax.set_facecolor("#0e1117")
            ax.tick_params(colors="white")
            ax.xaxis.label.set_color("white")
            ax.yaxis.label.set_color("white")
            ax.title.set_color("white")
            ax.grid(True, which="both", linestyle="--", alpha=0.3)

        ax1.semilogx(freqs, magnitude_db, color="#00ffcc", linewidth=2.5)
        ax1.set_ylabel("Magnitude (dB)")
        ax1.set_title("Bode Frequency Response H(jω)")
        if f_res > 0:
            ax1.axvline(
                f_res,
                color="#ff4b4b",
                linestyle=":",
                label=f"f₀ = {f_res:.1f} Hz",
            )
            ax1.legend(
                facecolor="#1e222a", edgecolor="white", labelcolor="white"
            )

        ax2.semilogx(freqs, phase_deg, color="#ff9900", linewidth=2.5)
        ax2.set_xlabel("Frequency (Hz)")
        ax2.set_ylabel("Phase (Deg)")

        st.pyplot(fig, use_container_width=True)

    # --- TIME RESPONSE DOMAIN ---
    else:
        alpha = r_total / (2.0 * l_H) if l_H > 0 else 0.0
        w0 = 1.0 / math.sqrt(l_H * c_F) if (l_H * c_F) > 0 else 0.0
        zeta = alpha / w0 if w0 > 0 else 0.0

        t_max = 5 * (1.0 / alpha) if alpha > 0 else 0.01
        t = np.linspace(0, t_max, 1000)

        if zeta < 1.0 and w0 > 0:
            wd = np.sqrt(w0**2 - alpha**2)
            vc = source_v * (
                1.0
                - np.exp(-alpha * t)
                * (np.cos(wd * t) + (alpha / wd) * np.sin(wd * t))
            )
        else:
            s1 = -alpha + np.sqrt(max(0, alpha**2 - w0**2))
            s2 = -alpha - np.sqrt(max(0, alpha**2 - w0**2))
            vc = source_v * (
                1.0
                + (s2 * np.exp(s1 * t) - s1 * np.exp(s2 * t))
                / (s1 - s2 if s1 != s2 else 1)
            )

        fig, ax = plt.subplots(figsize=(9, 4))
        fig.patch.set_facecolor("#0e1117")
        ax.set_facecolor("#0e1117")
        ax.tick_params(colors="white")
        ax.xaxis.label.set_color("white")
        ax.yaxis.label.set_color("white")
        ax.title.set_color("white")
        ax.grid(True, linestyle="--", alpha=0.3)

        ax.plot(
            t * 1000,
            vc,
            color="#00e5ff",
            linewidth=2.5,
            label="Capacitor Voltage v_C(t)",
        )
        ax.axhline(
            source_v, color="#ff4b4b", linestyle="--", label="Input Step Voltage"
        )
        ax.set_xlabel("Time (ms)")
        ax.set_ylabel("Voltage (V)")
        ax.set_title("Step Response Transient Curve v(t)")
        ax.legend(facecolor="#1e222a", edgecolor="white", labelcolor="white")

        st.pyplot(fig, use_container_width=True)

    st.divider()

    # --- GET DATA / EXTRANALYTICS ACTION ---
    if st.button(
        "⚡ Extract Complete Engineering Analytics Data",
        use_container_width=True,
    ):
        st.warning(
            "⚠️ **PROFESSIONAL DATA WARNING:** The extracted analytics below utilize non-linear differential matrix models, s-domain complex poles, and frequency attenuation matrices. Interpretation requires training in AC/DC Electrical Engineering & Signal Processing."
        )

        st.markdown("### 📋 Executive Engineering Report")

        # Network Totals
        r_sum = sum(
            c["val"]
            for c in st.session_state.peem_components
            if c["type"] == "Resistor"
        )
        l_sum = sum(
            c["val"]
            for c in st.session_state.peem_components
            if c["type"] == "Inductor"
        )
        c_sum = sum(
            c["val"]
            for c in st.session_state.peem_components
            if c["type"] == "Capacitor"
        )

        l_h_eval = l_sum * 1e-3
        c_f_eval = c_sum * 1e-6
        f_0 = (
            1.0 / (2 * math.pi * math.sqrt(l_h_eval * c_f_eval))
            if (l_h_eval * c_f_eval) > 0
            else 0.0
        )
        q_0 = (
            (1.0 / r_sum) * math.sqrt(l_h_eval / c_f_eval)
            if (r_sum > 0 and c_f_eval > 0 and l_h_eval > 0)
            else 0.0
        )
        bw_eval = f_0 / q_0 if q_0 > 0 else 0.0

        col_a1, col_a2, col_a3, col_a4 = st.columns(4)
        col_a1.metric("Resonant Freq (f₀)", f"{f_0:.2f} Hz")
        col_a2.metric("Quality Factor (Q)", f"{q_0:.3f}")
        col_a3.metric("Bandwidth (BW)", f"{bw_eval:.2f} Hz")
        col_a4.metric("Damping (α)", f"{(r_sum / (2 * l_h_eval)):.2f}" if l_h_eval > 0 else "N/A")

        st.markdown("#### 🔍 Structural Component Network Matrix")

        md_peem = (
            "| Component Name | Element Type | Network Branch | Value | Equivalent Reactance @ f₀ |\n"
            "| :--- | :--- | :--- | :--- | :--- |\n"
        )

        for c in st.session_state.peem_components:
            val = c["val"]
            c_t = c["type"]
            reactance_str = "0.00 Ω"

            if c_t == "Resistor":
                reactance_str = f"{val:.2f} Ω (Pure)"
            elif c_t == "Inductor":
                x_l = 2 * math.pi * f_0 * (val * 1e-3) if f_0 > 0 else 0.0
                reactance_str = f"+j{x_l:.2f} Ω"
            elif c_t == "Capacitor":
                x_c = 1.0 / (2 * math.pi * f_0 * (val * 1e-6)) if f_0 > 0 else 0.0
                reactance_str = f"-j{x_c:.2f} Ω"

            md_peem += f"| **{c['name']}** | {c_t} | {c['conn']} | `{val} {c['unit']}` | `{reactance_str}` |\n"

        st.markdown(md_peem)

        log_entry = f">> PEEM Data Solved: f0={f_0:.1f}Hz, Q={q_0:.3f}, Elements={len(st.session_state.peem_components)}"
        if "calc_history" in st.session_state:
            st.session_state.calc_history.append(log_entry)