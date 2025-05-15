import streamlit as st
import pandas as pd
import plotly.express as px
import math
import datetime
from decimal import Decimal # For potential future formatting needs

# --- 1. SET PAGE CONFIG (MUST BE FIRST STREAMLIT COMMAND) ---
st.set_page_config(layout="wide")

# --- Configuration ---
YEAR_OPTIONS = [2030, 2040, 2050]
MILLION = 1_000_000

TANKER_ROUTES = {
    "vlcc_china": "VLCC (to China)",
    "suez_seasia": "Suezmax (to SE Asia)",
    "suez_sing": "Suezmax (to Singapore)",
    "afra_europe": "Aframax (to Europe)",
    "pana_houston": "Panamax (to Houston)",
    "mr_ny": "MR Tankers (to New York)"
}
ROUTE_KEYS = list(TANKER_ROUTES.keys())

# --- Year-Dependent Owned Ship Categories ---
OWNED_SHIP_CATEGORIES_BY_YEAR = {
    2030: ["Diesel Ships", "B30 Ships", "Methanol Ships", "Ammonia Ships", "B30 EET Ships"],
    2040: ["Diesel Ships", "B50 Ships", "Methanol Ships", "Ammonia Ships", "BlueH2 Ships", "Methane Ships", "VLSFO OCCS Ships", "B50 EET Ships"],
    2050: ["Diesel Ships", "B100 Ships", "Methanol Ships", "Ammonia Ships", "eH2 Ships", "eMethane Ships", "eDiesel Ships", "B100 EET Ships", "Bio Methane Ships"]
}

# Helper to create empty owned_ships dict for a given year's categories
def get_empty_owned_ships_dict_for_year(year):
    categories = OWNED_SHIP_CATEGORIES_BY_YEAR.get(year, [])
    return {cat.lower().replace(' ', '_').replace('(','').replace(')',''): 0 for cat in categories}

# Charter Cost Factors
ALL_CHARTER_FACTORS = {
    2030: {"vlcc_china": {"m1": 4.5, "m2": 6.96}, "suez_seasia": {"m1": 5.8, "m2": 4.66}, "suez_sing": {"m1": 5.8, "m2": 4.66}, "afra_europe": {"m1": 9.2, "m2": 3.68}, "pana_houston": {"m1": 11.4, "m2": 2.63}, "mr_ny": {"m1": 10.5, "m2": 2.25}},
    2040: {"vlcc_china": {"m1": 4.5, "m2": 7.24}, "suez_seasia": {"m1": 5.8, "m2": 4.84}, "suez_sing": {"m1": 5.8, "m2": 4.84}, "afra_europe": {"m1": 9.2, "m2": 3.83}, "pana_houston": {"m1": 11.4, "m2": 2.74}, "mr_ny": {"m1": 10.5, "m2": 2.34}},
    2050: {"vlcc_china": {"m1": 4.5, "m2": 7.52}, "suez_seasia": {"m1": 5.8, "m2": 5.03}, "suez_sing": {"m1": 5.8, "m2": 5.03}, "afra_europe": {"m1": 9.2, "m2": 3.98}, "pana_houston": {"m1": 11.4, "m2": 2.85}, "mr_ny": {"m1": 10.5, "m2": 2.43}}
}

# --- Default Input Values by Year (Comprehensive) ---
DEFAULT_INPUTS_2030 = {
    "vlcc_china":   {"owned_ships": {"diesel_ships": 4, "b30_ships": 14, "methanol_ships": 0, "ammonia_ships": 0, "b30_eet_ships": 0}, "tco": 538.21,    "ghg": 1.69,     "charter": 12},
    "suez_seasia":  {"owned_ships": {"diesel_ships": 2, "b30_ships": 7,  "methanol_ships": 0, "ammonia_ships": 0, "b30_eet_ships": 0}, "tco": 174.7,     "ghg": 0.4,      "charter": 6},
    "suez_sing":    {"owned_ships": {"diesel_ships": 6, "b30_ships": 14, "methanol_ships": 0, "ammonia_ships": 0, "b30_eet_ships": 0}, "tco": 384.93,    "ghg": 0.91,     "charter": 0},
    "afra_europe":  {"owned_ships": {"diesel_ships": 5, "b30_ships": 0,  "methanol_ships": 0, "ammonia_ships": 0, "b30_eet_ships": 0}, "tco": 52.4165,   "ghg": 0.2437,   "charter": 28},
    "pana_houston": {"owned_ships": {"diesel_ships": 1, "b30_ships": 0,  "methanol_ships": 0, "ammonia_ships": 0, "b30_eet_ships": 0}, "tco": 8.79673,   "ghg": 0.04292,  "charter": 8},
    "mr_ny":        {"owned_ships": {"diesel_ships": 4, "b30_ships": 0,  "methanol_ships": 0, "ammonia_ships": 0, "b30_eet_ships": 0}, "tco": 31.0053,   "ghg": 0.12959,  "charter": 21}
}

# *** ENSURING THESE ARE FULLY DEFINED ***
DEFAULT_INPUTS_2040 = {
    "vlcc_china":   {"owned_ships": {"diesel_ships": 4, "b50_ships": 1, "methanol_ships": 0, "ammonia_ships": 0, "blueh2_ships": 0, "methane_ships": 0, "vlsfo_occs_ships":0, "b50_eet_ships":0}, "tco": 848.85, "ghg": 0.64, "charter": 5},
    "suez_seasia":  {"owned_ships": {"diesel_ships": 2, "b50_ships": 2, "methanol_ships": 0, "ammonia_ships": 0, "blueh2_ships":0, "methane_ships":13, "vlsfo_occs_ships":0, "b50_eet_ships":0 }, "tco": 357.2, "ghg": 0.2, "charter": 2},
    "suez_sing":    {"owned_ships": {"diesel_ships": 0, "b50_ships": 8, "methanol_ships": 2, "ammonia_ships": 0, "blueh2_ships":0, "methane_ships":7, "vlsfo_occs_ships":0, "b50_eet_ships":0 }, "tco": 500.31, "ghg": 0.27, "charter": 4},
    "afra_europe":  {"owned_ships": {"diesel_ships": 5, "b50_ships": 0, "methanol_ships": 0, "ammonia_ships": 0, "blueh2_ships":0, "methane_ships":0, "vlsfo_occs_ships":0, "b50_eet_ships":0 }, "tco": 81.69102, "ghg": 0.239923,"charter": 18},
    "pana_houston": {"owned_ships": get_empty_owned_ships_dict_for_year(2040), "tco": 0.0, "ghg": 0.0, "charter": 7},
    "mr_ny":        {"owned_ships": get_empty_owned_ships_dict_for_year(2040), "tco": 0.0, "ghg": 0.0, "charter": 22}
}

DEFAULT_INPUTS_2050 = {
    "vlcc_china":   {"owned_ships": {"diesel_ships":0, "b100_ships":0, "methanol_ships":0, "ammonia_ships":18, "eh2_ships":0, "emethane_ships":0, "ediesel_ships":0, "b100_eet_ships":0, "bio_methane_ships":0}, "tco": 960.76, "ghg": 0.02376, "charter": 1},
    "suez_seasia":  {"owned_ships": {"diesel_ships":0, "b100_ships":8, "methanol_ships":0, "ammonia_ships":4, "eh2_ships":0, "emethane_ships":0, "ediesel_ships":0, "b100_eet_ships":0, "bio_methane_ships":0}, "tco": 555.78, "ghg": 0.01877, "charter": 1},
    "suez_sing":    {"owned_ships": {"diesel_ships":0, "b100_ships":12, "methanol_ships":0, "ammonia_ships":5, "eh2_ships":0, "emethane_ships":0, "ediesel_ships":0, "b100_eet_ships":0, "bio_methane_ships":0}, "tco": 780.3, "ghg": 0.02754, "charter": 3},
    "afra_europe":  {"owned_ships": get_empty_owned_ships_dict_for_year(2050), "tco": 0.0, "ghg": 0.0, "charter": 18},
    "pana_houston": {"owned_ships": get_empty_owned_ships_dict_for_year(2050), "tco": 0.0, "ghg": 0.0, "charter": 6},
    "mr_ny":        {"owned_ships": get_empty_owned_ships_dict_for_year(2050), "tco": 0.0, "ghg": 0.0, "charter": 20}
}
# ************************************

ALL_YEAR_DEFAULT_INPUTS = {
    2030: DEFAULT_INPUTS_2030,
    2040: DEFAULT_INPUTS_2040,
    2050: DEFAULT_INPUTS_2050
}
FALLBACK_OWNED_SHIP_CATEGORIES = OWNED_SHIP_CATEGORIES_BY_YEAR[2030]
EMPTY_ROUTE_DEFAULTS = {
    "owned_ships": {cat.lower().replace(' ', '_').replace('(','').replace(')',''): 0 for cat in FALLBACK_OWNED_SHIP_CATEGORIES},
    "charter": 0, "tco": 0.0, "ghg": 0.0
}


# --- Helper Function for Formatting ---
def format_value(value, decimal_places=2, is_currency=False, use_sig_figs_non_currency=False, sig_figs=2):
    if value is None or math.isnan(value) or abs(value) < 1e-9: return "$0.00" if is_currency else "0.00"
    try:
        if is_currency: return f"${value:,.{decimal_places}f}"
        elif use_sig_figs_non_currency:
            if value == 0: return "0.00"
            return f"{float(value):.{sig_figs}g}" # Using 'g' for significant figures
        else: return f"{value:,.{decimal_places}f}"
    except (ValueError, TypeError): return str(value)

# --- Initialize Session State ---
def initialize_session_state_once():
    if 'app_initialized_fleet_v2' not in st.session_state: # New unique flag
        st.session_state.app_initialized_fleet_v2 = True
        st.session_state.selected_year = YEAR_OPTIONS[0]
        st.session_state.results = None
        st.session_state.show_results = False
        st.session_state.reset_trigger_flag = False

        initial_year_to_load = st.session_state.selected_year
        defaults_for_init_year_master = ALL_YEAR_DEFAULT_INPUTS.get(initial_year_to_load, {})
        for route_key in ROUTE_KEYS:
            route_data = defaults_for_init_year_master.get(route_key, EMPTY_ROUTE_DEFAULTS)
            st.session_state[f"charter_{route_key}"] = route_data['charter']
            st.session_state[f"tco_{route_key}"] = route_data['tco']
            st.session_state[f"ghg_{route_key}"] = route_data['ghg']
            current_owned_categories = OWNED_SHIP_CATEGORIES_BY_YEAR.get(initial_year_to_load, FALLBACK_OWNED_SHIP_CATEGORIES)
            owned_ship_defaults_for_route = route_data.get("owned_ships", {})
            for ship_cat_display_name in current_owned_categories:
                ship_cat_internal_key = ship_cat_display_name.lower().replace(' ', '_').replace('(','').replace(')','')
                session_key = f"owned_{route_key}_{ship_cat_internal_key}"
                st.session_state[session_key] = owned_ship_defaults_for_route.get(ship_cat_internal_key, 0)
initialize_session_state_once()

# --- Process Reset (if triggered, AFTER set_page_config, BEFORE other st commands) ---
if st.session_state.get('reset_trigger_flag', False):
    year_to_reset = st.session_state.selected_year
    # print(f"DEBUG: Processing reset for year {year_to_reset} at top of script.")
    defaults_for_year = ALL_YEAR_DEFAULT_INPUTS.get(year_to_reset, {})
    for route_key in ROUTE_KEYS:
        route_defaults = defaults_for_year.get(route_key, EMPTY_ROUTE_DEFAULTS)
        st.session_state[f"charter_{route_key}"] = route_defaults['charter']
        st.session_state[f"tco_{route_key}"] = route_defaults['tco']
        st.session_state[f"ghg_{route_key}"] = route_defaults['ghg']
        owned_ship_defaults_for_route = route_defaults.get("owned_ships", {})
        current_owned_categories_for_reset = OWNED_SHIP_CATEGORIES_BY_YEAR.get(year_to_reset, FALLBACK_OWNED_SHIP_CATEGORIES)
        for ship_cat_display_name in current_owned_categories_for_reset:
            ship_cat_internal_key = ship_cat_display_name.lower().replace(' ', '_').replace('(','').replace(')','')
            session_key = f"owned_{route_key}_{ship_cat_internal_key}"
            st.session_state[session_key] = owned_ship_defaults_for_route.get(ship_cat_internal_key, 0)
    st.session_state.reset_trigger_flag = False
    st.session_state.results = None
    st.session_state.show_results = False
    st.success(f"All inputs reset to {year_to_reset} default values.")


# --- Callbacks ---
def clear_results_on_input_change():
    st.session_state.results = None
    st.session_state.show_results = False
def trigger_reset_all_inputs_and_clear_results():
    st.session_state.reset_trigger_flag = True
    # Rerun will happen naturally.

# --- App Layout ---
st.title("Tanker Fleet Decision Support: Costs & Emissions")
st.divider()

# --- Input Section ---
# (Keep the rest of the input section as is)
st.sidebar.header("⚙️ Input Parameters")
st.sidebar.info("Define fleet composition and scenario inputs.")
selected_year_from_ui = st.sidebar.selectbox( # Renamed to avoid conflict
    "Select Target Year:", options=YEAR_OPTIONS, key='selected_year',
    on_change=clear_results_on_input_change
)
st.sidebar.button(f"Reset ALL Inputs to {st.session_state.selected_year} Defaults", on_click=trigger_reset_all_inputs_and_clear_results)
st.sidebar.divider()
st.sidebar.subheader("Owned Fleet Composition (Per Route)")
current_owned_ship_categories_for_display = OWNED_SHIP_CATEGORIES_BY_YEAR.get(st.session_state.selected_year, [])
if not current_owned_ship_categories_for_display:
    st.sidebar.warning(f"No owned ship categories defined for {st.session_state.selected_year}.")
for route_key, route_display_name in TANKER_ROUTES.items():
    with st.sidebar.expander(f"Owned Ships for: {route_display_name}"):
        if not current_owned_ship_categories_for_display: st.caption("Categories not set.")
        else:
            for ship_category_display_name in current_owned_ship_categories_for_display:
                ship_cat_internal_key = ship_category_display_name.lower().replace(' ', '_').replace('(','').replace(')','')
                session_key = f"owned_{route_key}_{ship_cat_internal_key}"
                if session_key not in st.session_state: st.session_state[session_key] = 0
                st.number_input(f"{ship_category_display_name}", min_value=0, step=1, key=session_key, on_change=clear_results_on_input_change)

st.header("🚢 Route-Specific Data (TCO, GHG, Charter)")
st.markdown("""<style>div[data-testid="stHorizontalBlock"] div[data-testid="stVerticalBlock"] div[data-baseweb="block"] > label[data-baseweb="form-control-label"] {height: 4em; display: flex; align-items: center; justify-content: start; white-space: normal; overflow: hidden; margin-bottom: -0.7em;}</style>""", unsafe_allow_html=True)
for key, display_name in TANKER_ROUTES.items():
    with st.expander(f"Data for: {display_name}"):
        col_in1, col_in2, col_in3 = st.columns(3)
        charter_key = f"charter_{key}"; tco_key = f"tco_{key}"; ghg_key = f"ghg_{key}"
        with col_in1: st.number_input(f"Charter Vessels", min_value=0, step=1, key=charter_key, on_change=clear_results_on_input_change)
        with col_in2: st.number_input(f"Annualized TCO (Million USD)", min_value=0.0, step=0.01, format="%.5f", key=tco_key, help="Input from external analysis.", on_change=clear_results_on_input_change)
        with col_in3: st.number_input(f"Total GHG (Million Tons CO2e)", min_value=0.0, step=0.001, format="%.5f", key=ghg_key, help=f"Input from external analysis for {st.session_state.selected_year}.", on_change=clear_results_on_input_change)
st.divider()

# --- Calculation Trigger ---
# (Calculation logic remains the same)
st.header("📊 Calculate & Analyze")
if st.button("Run Analysis", type="primary"):
    current_year_calc = st.session_state.selected_year
    current_year_factors = ALL_CHARTER_FACTORS.get(current_year_calc, {})
    route_level_data_list = []
    calculated_total_owned_vessels_all_routes = 0
    total_tco_fleet = 0.0; total_ghg_fleet = 0.0; total_charter_cost_fleet = 0.0
    with st.spinner(f"Analyzing for {current_year_calc}..."):
        current_owned_ship_categories_for_sum = OWNED_SHIP_CATEGORIES_BY_YEAR.get(current_year_calc, [])
        for route_key_iter in ROUTE_KEYS:
            for ship_cat_display_name in current_owned_ship_categories_for_sum:
                cat_key_internal = ship_cat_display_name.lower().replace(' ', '_').replace('(','').replace(')','')
                session_key_owned = f"owned_{route_key_iter}_{cat_key_internal}"
                calculated_total_owned_vessels_all_routes += st.session_state.get(session_key_owned, 0)
        for key, display_name in TANKER_ROUTES.items():
            route_owned_ships_sum = 0
            for ship_cat_display_name in current_owned_ship_categories_for_sum:
                cat_key_internal = ship_cat_display_name.lower().replace(' ', '_').replace('(','').replace(')','')
                session_key_owned = f"owned_{key}_{cat_key_internal}"
                route_owned_ships_sum += st.session_state.get(session_key_owned, 0)
            charter_count = st.session_state[f"charter_{key}"]
            tco_val = st.session_state[f"tco_{key}"]
            ghg_val = st.session_state[f"ghg_{key}"]
            factors = current_year_factors.get(key)
            route_charter_cost = 0.0
            if factors and charter_count > 0: route_charter_cost = charter_count * factors["m1"] * factors["m2"]
            elif charter_count > 0: st.warning(f"Charter factors missing for {display_name}.")
            total_charter_cost_fleet += route_charter_cost; total_tco_fleet += tco_val; total_ghg_fleet += ghg_val
            route_level_data_list.append({"Route": display_name, "Total Owned Ships": route_owned_ships_sum, "Charter Vessels": charter_count, "TCO (M USD)": tco_val, "GHG (M Tons CO2e)": ghg_val, "Charter Cost (M USD)": route_charter_cost})
    total_investment_fleet = total_tco_fleet + total_charter_cost_fleet
    st.session_state.results = {"route_data_df": pd.DataFrame(route_level_data_list), "total_tco_fleet": total_tco_fleet, "total_ghg_fleet": total_ghg_fleet, "total_charter_cost_fleet": total_charter_cost_fleet, "total_investment_fleet": total_investment_fleet, "calculated_total_owned_vessels_all_routes": calculated_total_owned_vessels_all_routes, "calculated_for_year": current_year_calc}
    st.session_state.show_results = True
    st.success(f"Analysis Complete for {current_year_calc}!")

st.divider()

# --- Output Section ---
# (Output formatting fixes as requested)
st.header("📈 Analysis Outputs")
if st.session_state.show_results and st.session_state.results:
    results = st.session_state.results; calc_year = results["calculated_for_year"]
    st.subheader(f"Fleet Summary (Year: {calc_year})")
    # Metrics in two rows
    row1_metrics_cols = st.columns(3)
    with row1_metrics_cols[0]: st.metric(label="Total Owned Vessels (All Routes)", value=f"{results['calculated_total_owned_vessels_all_routes']}")
    with row1_metrics_cols[1]: st.metric(label="Total TCO (Fleet, M USD)", value=f"{format_value(results['total_tco_fleet'], 2, True, sig_figs=2)}") # Use sig_figs for metrics
    with row1_metrics_cols[2]: st.metric(label="Total GHG Emissions (Fleet, M Tons CO2e)", value=f"{format_value(results['total_ghg_fleet'], 2, use_sig_figs_non_currency=True, sig_figs=2)}")

    row2_metrics_cols = st.columns(2)
    with row2_metrics_cols[0]: st.metric(label="Total Charter Cost (Fleet, M USD)", value=f"{format_value(results['total_charter_cost_fleet'], 2, True, sig_figs=2)}")
    with row2_metrics_cols[1]: st.metric(label="Total Investment (Fleet, M USD)", value=f"{format_value(results['total_investment_fleet'], 2, True, sig_figs=2)}")
    st.divider()

    st.subheader("Route-Level Summary")
    df_routes = results["route_data_df"]
    if not df_routes.empty:
        df_routes_display = df_routes[(df_routes["Total Owned Ships"] > 0) | (df_routes["Charter Vessels"] > 0) | (abs(df_routes["TCO (M USD)"]) > 1e-9) | (abs(df_routes["GHG (M Tons CO2e)"]) > 1e-9) | (abs(df_routes["Charter Cost (M USD)"]) > 1e-9)]
        column_order = ["Route", "Total Owned Ships", "Charter Vessels", "TCO (M USD)", "GHG (M Tons CO2e)", "Charter Cost (M USD)"]
        df_routes_display = df_routes_display.reindex(columns=column_order, fill_value=0)
        st.dataframe(df_routes_display.style.format({
            "Total Owned Ships": "{:,.0f}", "Charter Vessels": "{:,.0f}",
            "TCO (M USD)": lambda x: format_value(x, 2, True, sig_figs=2), # More consistent sig fig
            "GHG (M Tons CO2e)": lambda x: format_value(x, 2, use_sig_figs_non_currency=True, sig_figs=2),
            "Charter Cost (M USD)": lambda x: format_value(x, 2, True, sig_figs=2)
        }), use_container_width=True)
    else: st.info("No route data.")
    st.divider()

    st.subheader("Visual Insights")
    viz_col1, viz_col2 = st.columns(2)
    with viz_col1:
        st.markdown("**Annualized TCO by Route (M USD)**")
        if not df_routes[abs(df_routes['TCO (M USD)']) > 1e-9].empty:
            fig_tco = px.bar(df_routes, x='Route', y='TCO (M USD)', text_auto='.2f', title="TCO by Route")
            fig_tco.update_layout(xaxis_tickangle=-45, yaxis_title="TCO (Million USD)", height=400); st.plotly_chart(fig_tco, use_container_width=True)
        else: st.caption("No TCO data.")
        st.markdown("**Calculated Charter Cost by Route (M USD)**")
        if not df_routes[abs(df_routes['Charter Cost (M USD)']) > 1e-9].empty:
            fig_charter_cost = px.bar(df_routes, x='Route', y='Charter Cost (M USD)', text_auto='.2f', title="Charter Cost by Route")
            fig_charter_cost.update_layout(xaxis_tickangle=-45, yaxis_title="Charter Cost (Million USD)", height=400); st.plotly_chart(fig_charter_cost, use_container_width=True)
        else: st.caption("No charter costs.")
        st.markdown("**Owned vs. Chartered Vessels by Route**")
        df_own_charter = df_routes[['Route', 'Total Owned Ships', 'Charter Vessels']]; df_own_charter_melted = df_own_charter.melt(id_vars=['Route'], value_vars=['Total Owned Ships', 'Charter Vessels'], var_name='Vessel Source', value_name='Number of Vessels')
        df_own_charter_plot = df_own_charter_melted[df_own_charter_melted['Number of Vessels'] > 0]
        if not df_own_charter_plot.empty:
            fig_own_charter = px.bar(df_own_charter_plot, x='Route', y='Number of Vessels', color='Vessel Source', barmode='group', text_auto=True, title="Owned vs. Chartered Vessels")
            fig_own_charter.update_layout(xaxis_tickangle=-45, yaxis_title="Number of Vessels", height=400); fig_own_charter.update_traces(texttemplate='%{y:.0f}')
            st.plotly_chart(fig_own_charter, use_container_width=True)
        else: st.caption("No owned/chartered data.")
    with viz_col2:
        st.markdown("**GHG Emissions by Route (M Tons CO2e)**")
        if not df_routes[abs(df_routes['GHG (M Tons CO2e)']) > 1e-9].empty:
            fig_ghg = px.bar(df_routes, x='Route', y='GHG (M Tons CO2e)', text_auto='.2f', title="GHG Emissions by Route")
            fig_ghg.update_layout(xaxis_tickangle=-45, yaxis_title="GHG (Million Tons CO2e)", height=400); st.plotly_chart(fig_ghg, use_container_width=True)
        else: st.caption("No GHG data.")
        st.markdown("**Cost Comparison: Charter vs. TCO by Route (M USD)**")
        df_cost_comp = df_routes[((abs(df_routes['Charter Cost (M USD)']) > 1e-9) | (abs(df_routes['TCO (M USD)']) > 1e-9))]
        if not df_cost_comp.empty:
            df_melted_costs = df_cost_comp.melt(id_vars=['Route'], value_vars=['TCO (M USD)', 'Charter Cost (M USD)'], var_name='Cost Type', value_name='Cost (Million USD)')
            fig_cost_comp = px.bar(df_melted_costs, x='Route', y='Cost (Million USD)', color='Cost Type', barmode='group', text_auto='.2f', title="TCO vs. Charter Cost")
            fig_cost_comp.update_layout(xaxis_tickangle=-45, yaxis_title="Cost (Million USD)", height=400); st.plotly_chart(fig_cost_comp, use_container_width=True)
        else: st.caption("No cost data for comparison.")
    with st.expander("Exploratory: GHG vs. Charter Vessels (Bubble Size by TCO)"):
        df_scatter = df_routes[(df_routes['Charter Vessels'] > 0) & (abs(df_routes['GHG (M Tons CO2e)']) > 1e-9)]
        if not df_scatter.empty:
            df_scatter_copy = df_scatter.copy(); df_scatter_copy.loc[:, 'TCO for Sizing (M USD)'] = df_scatter_copy['TCO (M USD)'].apply(lambda x: max(x, 0.1))
            fig_scatter = px.scatter(df_scatter_copy, x="Charter Vessels", y="GHG (M Tons CO2e)", color="Route", size="TCO for Sizing (M USD)", hover_name="Route", size_max=60, title="GHG Emissions vs. Charter Vessels (Bubble Size = TCO)")
            fig_scatter.update_layout(height=500); st.plotly_chart(fig_scatter, use_container_width=True)
        else: st.caption("Not enough data for scatter plot.")
else:
    if not st.session_state.show_results: st.info("Click 'Run Analysis' after entering parameters.")

# --- Footer ---
st.divider()
current_year = datetime.datetime.now().year
st.caption(f"© {current_year} [ABS Energy Analytics Lab: Dr. Chenxi Ji]. All rights reserved.") # Replace placeholder
st.caption("Calculations based on user inputs and predefined factors. Verify external data sources.")
