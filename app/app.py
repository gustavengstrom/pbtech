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

PARAM_DETAILS = {
    "tau_E": {
        "group": "Policy and adjustment costs",
        "description": "Carbon tax applied to fossil energy use. Raising this parameter makes emissions-intensive production relatively more expensive throughout the model.",
    },
    "V_A": {
        "group": "Policy and adjustment costs",
        "description": "Conversion cost for agriculture. Higher values make it more costly to reallocate or expand agricultural production.",
    },
    "V_T": {
        "group": "Policy and adjustment costs",
        "description": "Conversion cost for timber production. Higher values make adjustments in timber land use and production more expensive.",
    },
    "GammaP_Pho": {
        "group": "Production shares",
        "description": "Cost share of phosphate in fertilizer production. Higher values make fertilizer output more dependent on phosphate inputs.",
    },
    "GammanLA_EpsA": {
        "group": "Production shares",
        "description": "Cost share of energy in non-land agricultural inputs. Higher values make agriculture more exposed to changes in energy availability and prices.",
    },
    "GammaY_EpsY": {
        "group": "Production shares",
        "description": "Cost share of energy services in manufacturing. Higher values mean final-goods production relies more heavily on energy services.",
    },
    "GammaT_LT": {
        "group": "Production shares",
        "description": "Cost share of land in timber production. Higher values increase the importance of land as an input to timber output.",
    },
    "GammaFi_EFi": {
        "group": "Production shares",
        "description": "Cost share of fossil fuel inputs in fisheries. Higher values make fisheries more sensitive to fossil energy conditions.",
    },
    "GammaEps_EEps": {
        "group": "Production shares",
        "description": "Cost share of fossil fuels in energy-service production. Higher values increase the fossil component of delivered energy services.",
    },
    "GammaEps_AB": {
        "group": "Production shares",
        "description": "Cost share of biofuels in energy-service production. Higher values make energy services more reliant on agricultural biofuel inputs.",
    },
    "GammaP_EP": {
        "group": "Production shares",
        "description": "Cost share of fossil fuels in fertilizer production. Higher values strengthen the link between fertilizer output and fossil energy use.",
    },
    "GammanLA_W": {
        "group": "Production shares",
        "description": "Cost share of water in non-land agricultural inputs. Higher values make agricultural production more dependent on water availability.",
    },
    "GammanLA_P": {
        "group": "Production shares",
        "description": "Cost share of fertilizer in non-land agricultural inputs. Higher values increase the importance of fertilizer for agricultural output.",
    },
    "GammaA_LA": {
        "group": "Production shares",
        "description": "Cost share of land in agricultural production. Higher values make food production more land-intensive.",
    },
    "GammanF_LU": {
        "group": "Production shares",
        "description": "Share of unused land in non-food production. Higher values increase the role of land conversion pressure outside food production.",
    },
    "GammanF_Y": {
        "group": "Production shares",
        "description": "Share of manufacturing goods in non-food production. Higher values make non-food output more dependent on the manufacturing sector.",
    },
    "GammaF_Fi": {
        "group": "Production shares",
        "description": "Share of fisheries in food production. Higher values increase the contribution of fish harvests to the food bundle.",
    },
    "GammaU_F": {
        "group": "Production shares",
        "description": "Share of food in household utility. Higher values make welfare more sensitive to food quantity and food prices.",
    },
    "Q_EFi": {
        "group": "Input requirement coefficients",
        "description": "Input requirement for fossil fuel use in fisheries. Higher values mean fisheries need more fossil energy per unit of output.",
    },
    "Q_EP": {
        "group": "Input requirement coefficients",
        "description": "Input requirement for fossil fuel use in fertilizer production. Higher values make fertilizer production more energy intensive.",
    },
    "Q_EpsA": {
        "group": "Input requirement coefficients",
        "description": "Input requirement for energy use in agriculture. Higher values mean agricultural output needs more energy services.",
    },
    "Q_AB": {
        "group": "Input requirement coefficients",
        "description": "Input requirement linking agriculture to biofuel production. Higher values mean more agricultural output is needed to supply biofuels.",
    },
    "Q_LT": {
        "group": "Input requirement coefficients",
        "description": "Input requirement for land use in timber production. Higher values make timber output more land intensive.",
    },
    "Q_LA": {
        "group": "Input requirement coefficients",
        "description": "Input requirement for land use in agriculture. Higher values make food production more land intensive.",
    },
    "Lambda_MFi": {
        "group": "Supply elasticities",
        "description": "Supply elasticity of intermediate inputs used in fisheries. Higher values mean fisheries intermediates can expand more easily when demand rises.",
    },
    "Lambda_MP": {
        "group": "Supply elasticities",
        "description": "Supply elasticity of intermediate inputs used in fertilizer production. Higher values make those intermediates easier to scale up.",
    },
    "Lambda_MY": {
        "group": "Supply elasticities",
        "description": "Supply elasticity of intermediate inputs used in final-goods production. Higher values reduce bottlenecks in manufacturing intermediates.",
    },
    "Lambda_MT": {
        "group": "Supply elasticities",
        "description": "Supply elasticity of intermediate inputs used in timber production. Higher values let timber intermediates respond more strongly to demand.",
    },
    "Lambda_MA": {
        "group": "Supply elasticities",
        "description": "Supply elasticity of intermediate inputs used in agriculture. Higher values make agricultural intermediates easier to expand.",
    },
    "Lambda_M": {
        "group": "Supply elasticities",
        "description": "Aggregate supply elasticity of intermediate goods. Higher values mean the general intermediate-input sector can respond more flexibly to shocks.",
    },
    "Lambda_Pho": {
        "group": "Supply elasticities",
        "description": "Supply elasticity of phosphate. Higher values make phosphate availability less of a constraint on fertilizer production.",
    },
    "Lambda_W": {
        "group": "Supply elasticities",
        "description": "Supply elasticity of water. Higher values make water supply more responsive to higher demand.",
    },
    "Lambda_E": {
        "group": "Supply elasticities",
        "description": "Supply elasticity of fossil fuels. Higher values make fossil energy supply expand more easily when prices rise.",
    },
    "Lambda_R": {
        "group": "Supply elasticities",
        "description": "Supply elasticity of renewables. Higher values make renewable energy supply more responsive to demand.",
    },
    "sigma_Y": {
        "group": "Elasticities of substitution",
        "description": "Elasticity of substitution between energy services and other inputs in manufacturing. Higher values mean manufacturing can swap away from energy more easily.",
    },
    "sigma_T": {
        "group": "Elasticities of substitution",
        "description": "Elasticity of substitution across inputs in timber production. Higher values mean timber producers can re-optimise input mixes more easily.",
    },
    "sigma_Fi": {
        "group": "Elasticities of substitution",
        "description": "Elasticity of substitution across inputs in fisheries. Higher values mean fisheries can adjust input bundles more flexibly.",
    },
    "sigma_Eps": {
        "group": "Elasticities of substitution",
        "description": "Elasticity of substitution across inputs in energy-service production. Higher values make it easier to shift between fossil, renewable, and biofuel-based energy inputs.",
    },
    "sigma_nLA": {
        "group": "Elasticities of substitution",
        "description": "Elasticity of substitution among non-land agricultural inputs. Higher values mean agriculture can more easily substitute between water, fertilizer, energy, and other intermediates.",
    },
    "sigma_P": {
        "group": "Elasticities of substitution",
        "description": "Elasticity of substitution across inputs in fertilizer production. Higher values mean fertilizer producers can adapt input use more readily.",
    },
    "sigma_A": {
        "group": "Elasticities of substitution",
        "description": "Elasticity of substitution across agricultural inputs, including land. Higher values mean agriculture can better re-balance across scarce inputs.",
    },
    "sigma_nF": {
        "group": "Elasticities of substitution",
        "description": "Elasticity of substitution across non-food inputs. Higher values make non-food production more flexible under changing relative prices.",
    },
    "sigma_F": {
        "group": "Elasticities of substitution",
        "description": "Elasticity of substitution across food sources. Higher values mean consumers or producers can shift more easily between food components such as agricultural and fish products.",
    },
    "sigma_U": {
        "group": "Elasticities of substitution",
        "description": "Elasticity of substitution in utility between food and non-food consumption. Higher values reduce the welfare penalty from changes in relative food scarcity.",
    },
}


def build_parameter_guide(current_params: dict) -> pd.DataFrame:
    """Return a parameter guide with names, groups, descriptions, and values."""
    rows = []
    for key in param_dict:
        meta = PARAM_DETAILS.get(key, {})
        raw_value = param_dict[key]
        rows.append(
            {
                "Parameter": key,
                "Short label": PARAM_DESCRIPTIONS.get(key, key),
                "Group": meta.get("group", "Other"),
                "Description": meta.get("description", ""),
                "Current value": float(current_params[key]),
                "Default value": float(raw_value[-1]) if isinstance(raw_value, list) else float(raw_value),
            }
        )
    return pd.DataFrame(rows)


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
st.markdown(
    "Each heatmap cell shows the percentage response in a planetary-pressure indicator when the parameter in that row is increased by 1%, holding the rest of the model fixed. "
    "A negative value means the 1% parameter increase reduces pressure on that boundary by the magnitude shown. For example, a cell value of -0.25 means a 1% increase in that parameter lowers the corresponding pressure by about 0.25%."
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

parameter_guide_df = build_parameter_guide(st.session_state.user_params)

with st.expander("Parameter guide", expanded=False):
    st.markdown(
        "The table below gives a fuller description of each model parameter, its role in the production structure, and the value currently used in the simulation. "
        "For parameters defined in the source data as ranges, the minimum, maximum, and default values are shown as reference."
    )
    st.dataframe(
        parameter_guide_df.style.format(
            {
                "Current value": "{:.4f}",
                "Default value": "{:.4f}"
            },
            na_rep="",
        ),
        use_container_width=True,
        hide_index=True,
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
    st.caption(
        "Interpretation: negative cells indicate that a 1% increase in the row parameter reduces the planetary pressure on the column boundary by the percentage shown. Positive cells indicate higher pressure."
    )
    fig = render_heatmap(display_df)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Expected value of PB")
    st.dataframe((df_result.sum(axis=0) / 2).to_frame("value").T)

    st.subheader("Raw data")
    st.dataframe(df_result.style.format("{:.5f}"))
else:
    st.info("Click **Run model** to generate the heatmap with the current parameters.")
