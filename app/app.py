import sys
from pathlib import Path

# Add parent directory so we can import model_code
# sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from model_code import model
from model_code.params import param_dict

# ── Label mappings (from Results_and_figures.py) ──

ROW_LABELS_MAP = {
    "A_LA": ("$A_{L_A}$", "(land use efficiency in agriculture)"),
    "A_EpsA": ("$A_{\\mathcal{E}_A}$", "(energy efficiency agriculture)"),
    "A_P": ("$A_P$", "(fertilizer efficiency in agriculture)"),
    "A_W": ("$A_W$", "(water efficiency in agriculture)"),
    "A_MA": ("$A_{M_A}$", "(other inputs efficiency in agriculture)"),
    "P_EP": ("$P_{E_P}$", "(fossil fuel efficiency in fertilizer prod.)"),
    "P_Pho": ("$P_{\\mathcal{P}}$", "(phosphor efficiency in fertilizer prod.)"),
    "P_MP": ("$P_{M_P}$", "(other inputs efficiency in fertilizer prod.)"),
    "Eps_AB": ("$\\mathcal{E}_{A_B}$", "(biofuel efficiency in energy service prod.)"),
    "Eps_EEps": ("$\\mathcal{E}_{E_{\\mathcal{E}}}$", "(fossil fuel efficiency in energy service prod.)"),
    "Eps_R": ("$\\mathcal{E}_R$", "(renewable efficiency in energy service prod.)"),
    "Y_EpsY": ("$Y_{\\mathcal{E}_Y}$", "(energy services efficiency in manufacturing)"),
    "Y_MY": ("$Y_{M_Y}$", "(other inputs efficiency in manufacturing)"),
    "Fi_EFi": ("$F_{E_F}$", "(fossil fuels efficiency in fisheries)"),
    "Fi_MFi": ("$F_{M_F}$", "(other inputs efficiency in fisheries)"),
    "T_LT": ("$T_{L_T}$", "(land use efficiency in timber prod.)"),
    "T_MT": ("$T_{M_T}$", "(other inputs efficiency in timber prod.)"),
}

COL_LABELS_MAP = {
    "Aerosol effect": "Aerosols",
    "CO2 effect": "CO2",
    "Biodiv. incl. climate effect": "Biodiversity loss",
    "Biogeochem. effect": "Biogeochemicals",
    "Freshwater effect": "Freshwater use",
    "Land-use effect": "Cultivated land",
}

FOOD_COL_LABELS_MAP = {
    "Food price effect": "Food price effect",
    "Food quantity effect": "Food quantity effect",
    "Food value effect": "Food value effect",
}

# ── Friendly names for param_dict keys ──

PARAM_DESCRIPTIONS = {
    "tau_E": "Carbon tax (τ_E)",
    "V_A": "Conversion costs agriculture (V_A)",
    "V_T": "Conversion costs timber (V_T)",
    "GammaP_Pho": "Phosphate share in fertilizer prod. (Γ_P,Pho)",
    "GammanLA_EpsA": "Energy share in non-land agric. (Γ_nLA,EpsA)",
    "GammaY_EpsY": "Energy share in manufacturing (Γ_Y,EpsY)",
    "GammaT_LT": "Land share in timber prod. (Γ_T,LT)",
    "GammaFi_EFi": "Fossil fuel share in fisheries (Γ_Fi,EFi)",
    "GammaEps_EEps": "Fossil fuel share in energy serv. (Γ_Eps,EEps)",
    "GammaEps_AB": "Biofuel share in energy serv. (Γ_Eps,AB)",
    "GammaP_EP": "Fossil fuel share in fertilizer prod. (Γ_P,EP)",
    "GammanLA_W": "Water share in non-land agric. (Γ_nLA,W)",
    "GammanLA_P": "Fertilizer share in non-land agric. (Γ_nLA,P)",
    "GammaA_LA": "Land share in agric. prod. (Γ_A,LA)",
    "GammanF_LU": "Unused land share in non-food (Γ_nF,LU)",
    "GammanF_Y": "Manufacturing share in non-food (Γ_nF,Y)",
    "GammaF_Fi": "Fish share in food (Γ_F,Fi)",
    "GammaU_F": "Food share in utility (Γ_U,F)",
    "Q_EFi": "Fossil fuel share for fisheries (Q_EFi)",
    "Q_EP": "Fossil fuel share for fertilizer (Q_EP)",
    "Q_EpsA": "Energy share for agriculture (Q_EpsA)",
    "Q_AB": "Agric. share for biofuels (Q_AB)",
    "Q_LT": "Land share for timber (Q_LT)",
    "Q_LA": "Land share for agriculture (Q_LA)",
    "Lambda_MFi": "Supply elast. intermediates fisheries (Λ_MFi)",
    "Lambda_MP": "Supply elast. intermediates fertilizers (Λ_MP)",
    "Lambda_MY": "Supply elast. intermediates final goods (Λ_MY)",
    "Lambda_MT": "Supply elast. intermediates timber (Λ_MT)",
    "Lambda_MA": "Supply elast. intermediates agriculture (Λ_MA)",
    "Lambda_M": "Supply elast. intermediates (Λ_M)",
    "Lambda_Pho": "Supply elast. phosphate (Λ_Pho)",
    "Lambda_W": "Supply elast. water (Λ_W)",
    "Lambda_E": "Supply elast. fossil fuel (Λ_E)",
    "Lambda_R": "Supply elast. renewables (Λ_R)",
    "sigma_Y": "Elast. subst. energy in manufacturing (σ_Y)",
    "sigma_T": "Elast. subst. timber prod. (σ_T)",
    "sigma_Fi": "Elast. subst. fisheries (σ_Fi)",
    "sigma_Eps": "Elast. subst. energy services (σ_Eps)",
    "sigma_nLA": "Elast. subst. non-land agric. (σ_nLA)",
    "sigma_P": "Elast. subst. fertilizer (σ_P)",
    "sigma_A": "Elast. subst. agric. prod. (σ_A)",
    "sigma_nF": "Elast. subst. non-food (σ_nF)",
    "sigma_F": "Elast. subst. food (σ_F)",
    "sigma_U": "Elast. subst. utility (σ_U)",
}


def get_default_params():
    """Return a deep copy of param_dict with list values resolved to their default (index 2)."""
    p = {}
    for k, v in param_dict.items():
        if isinstance(v, list):
            p[k] = float(v[-1])
        else:
            p[k] = float(v)
    return p


def compute_table(model_params: dict) -> pd.DataFrame:
    """Run compute_pb_tech_individual and return the heatmap dataframe."""
    sm = model.SolveModel(model_params)
    prod_change = {}
    for k in sm.prod_change_dict:
        sm.prod_change_dict[k] = 1
        df_q, df_p = sm.gen_results()
        pb = sm.pb_effects(df_q)
        sm.prod_change_dict[k] = 0
        pb_sum = pb[pb.columns[4:]].sum()
        pb_sum["Food price effect"] = sm.pb_food_price_effect(df_p)
        pb_sum["Food quantity effect"] = sm.pb_food_quantity_effect(df_q)
        pb_sum["Food value effect"] = pb_sum["Food price effect"] + pb_sum["Food quantity effect"]
        prod_change[k] = pb_sum

    df = pd.DataFrame(prod_change).T
    all_cols = list(COL_LABELS_MAP) + list(FOOD_COL_LABELS_MAP)
    keep_cols = [c for c in all_cols if c in df.columns]
    df = df[keep_cols]
    df["Land-use effect"] = df["Land-use effect"] * -1
    return df


def render_heatmap(df: pd.DataFrame):
    """Draw a Plotly heatmap and return the figure."""
    # Use plain-text descriptions (index 1) instead of LaTeX (index 0)
    row_labels = [
        ROW_LABELS_MAP[v][1].strip("()") for v in df.index
    ]
    all_labels = {**COL_LABELS_MAP, **FOOD_COL_LABELS_MAP}
    col_labels = [all_labels[c] for c in df.columns]

    data = df.astype(float).values
    # Build annotation text matrix
    text = [[f"{v:.3f}" for v in row] for row in data]

    abs_max = float(np.abs(data).max())

    fig = go.Figure(go.Heatmap(
        z=data,
        x=col_labels,
        y=row_labels,
        colorscale="RdBu_r",
        zmid=0,
        zmin=-abs_max,
        zmax=abs_max,
        text=text,
        texttemplate="%{text}",
        textfont={"size": 11},
        showscale=False,
        xgap=1,
        ygap=1,
    ))

    fig.update_layout(
        height=max(350, len(df) * 38),
        margin=dict(l=260, r=20, t=80, b=20),
        xaxis=dict(side="top", tickfont=dict(size=11)),
        yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
    )
    return fig


# ── Streamlit UI ──

st.set_page_config(page_title="PB Tech – Parameter Explorer", layout="wide")
st.title("Planetary Boundaries – Technical Change Heatmap Explorer")
st.markdown(
    "Adjust model parameters in the sidebar, then click **Run model** to regenerate the heatmap."
)

# Initialise session-state defaults
if "user_params" not in st.session_state:
    st.session_state.user_params = get_default_params()

# ── Sidebar: parameter controls ──
with st.sidebar:
    st.header("Model parameters")

    if st.button("Reset to defaults"):
        st.session_state.user_params = get_default_params()

    # Group params by type
    scalar_keys = [k for k, v in param_dict.items() if not isinstance(v, list)]
    range_keys = [k for k, v in param_dict.items() if isinstance(v, list)]

    st.subheader("Scalar parameters")
    for key in scalar_keys:
        default_val = float(param_dict[key])
        label = PARAM_DESCRIPTIONS.get(key, key)
        st.session_state.user_params[key] = st.number_input(
            label,
            value=st.session_state.user_params[key],
            format="%.6f",
            step=0.01,
            key=f"input_{key}",
        )

    st.subheader("Range parameters")
    st.caption("Default is the last value in each [min, max, default] list.")
    for key in range_keys:
        default_val = float(param_dict[key][-1])
        label = PARAM_DESCRIPTIONS.get(key, key)
        st.session_state.user_params[key] = st.number_input(
            label,
            value=st.session_state.user_params[key],
            format="%.6f",
            step=0.01,
            key=f"input_{key}",
        )

# ── Main area ──
include_food = st.checkbox("Include food price & quantity effects", value=False)
run_clicked = st.button("Run model", type="primary")

if run_clicked:
    with st.spinner("Solving model…"):
        df_result = compute_table(st.session_state.user_params)
    st.session_state.last_result = df_result

if "last_result" in st.session_state:
    df_result = st.session_state.last_result
    if not include_food:
        display_df = df_result[[c for c in COL_LABELS_MAP if c in df_result.columns]]
    else:
        display_df = df_result
    fig = render_heatmap(display_df)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Expected value of PB")
    st.dataframe((df_result.sum(axis=0) / 2).to_frame("value").T)

    st.subheader("Raw data")
    st.dataframe(df_result.style.format("{:.5f}"))
else:
    st.info("Click **Run model** to generate the heatmap with the current parameters.")
