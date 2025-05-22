import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import math
import datetime
import numpy

# --- 1. SET PAGE CONFIG (MUST BE FIRST STREAMLIT COMMAND) ---
st.set_page_config(layout="wide")

# --- Configuration ---
YEAR_OPTIONS = [2030, 2040, 2050]
BENCHMARK_YEAR = 2024
ANALYSIS_LIFESPAN_YEARS = 25
MILLION = 1_000_000

# ... (Keep TANKER_ROUTES, OWNED_SHIP_CATEGORIES_BY_YEAR, get_empty_owned_ships_dict_for_year,
#      ALL_CHARTER_FACTORS, DEFAULT_INPUTS_2030, DEFAULT_INPUTS_2040, DEFAULT_INPUTS_2050,
#      ALL_YEAR_DEFAULT_INPUTS, FALLBACK_OWNED_SHIP_CATEGORIES, EMPTY_ROUTE_DEFAULTS,
#      ROUTE_REVENUES_BY_YEAR, BENCHMARK_2024, CII_YEARS_DATA, CII_RATING_DATA_BY_TYPE,
#      PETROBRAS_CII_POINTS, CII_CHART_Y_MAX - these should be complete from previous versions) ...
TANKER_ROUTES = {
    "vlcc_china": "VLCC (to China)", "afra_europe": "Aframax (to Europe)",
    "pana_houston": "Panamax (to Houston)", "suez_seasia": "Suezmax (to SE Asia)",
    "suez_sing": "Suezmax (to Singapore)", "mr_ny": "MR Tankers (to New York)"
}
ROUTE_KEYS = list(TANKER_ROUTES.keys())
OWNED_SHIP_CATEGORIES_BY_YEAR = {
    2030: ["Diesel Ships", "B30 Ships", "Methanol Ships", "Ammonia Ships", "B30 EET Ships"],
    2040: ["Diesel Ships", "B50 Ships", "Methanol Ships", "Ammonia Ships", "BlueH2 Ships", "Methane Ships", "VLSFO OCCS Ships", "B50 EET Ships"],
    2050: ["Diesel Ships", "B100 Ships", "Methanol Ships", "Ammonia Ships", "eH2 Ships", "eMethane Ships", "eDiesel Ships", "B100 EET Ships", "Bio Methane Ships"]
}
def get_empty_owned_ships_dict_for_year(year):
    categories = OWNED_SHIP_CATEGORIES_BY_YEAR.get(year, [])
    return {cat.lower().replace(' ', '_').replace('(','').replace(')',''): 0 for cat in categories}
ALL_CHARTER_FACTORS = {2024: {"vlcc_china": (4.5, 6.96*0.95), "suez_seasia": (5.8, 4.66*0.95), "suez_sing": (5.8, 4.66*0.95), "afra_europe": (9.2, 3.68*0.95), "pana_houston": (11.4, 2.63*0.95), "mr_ny": (10.5, 2.25*0.95)}, 2030: {"vlcc_china": (4.5, 6.96), "suez_seasia": (5.8, 4.66), "suez_sing": (5.8, 4.66), "afra_europe": (9.2, 3.68), "pana_houston": (11.4, 2.63), "mr_ny": (10.5, 2.25)}, 2040: {"vlcc_china": (4.5, 7.24), "suez_seasia": (5.8, 4.84), "suez_sing": (5.8, 4.84), "afra_europe": (9.2, 3.83), "pana_houston": (11.4, 2.74), "mr_ny": (10.5, 2.34)}, 2050: {"vlcc_china": (4.5, 7.52), "suez_seasia": (5.8, 5.03), "suez_sing": (5.8, 5.03), "afra_europe": (9.2, 3.98), "pana_houston": (11.4, 2.85), "mr_ny": (10.5, 2.43)}}
DEFAULT_INPUTS_2030 = {"vlcc_china":   {"owned_ships": {"diesel_ships": 4, "b30_ships": 14, "methanol_ships": 0, "ammonia_ships": 0, "b30_eet_ships": 0}, "tco": 538.21,    "ghg": 1.69,     "charter": 12, "total_fuel_cost_route": 291.8803459},    "suez_seasia":  {"owned_ships": {"diesel_ships": 2, "b30_ships": 7,  "methanol_ships": 0, "ammonia_ships": 0, "b30_eet_ships": 0}, "tco": 174.7,     "ghg": 0.4,      "charter": 6,  "total_fuel_cost_route": 68.43707857},    "suez_sing":    {"owned_ships": {"diesel_ships": 10, "b30_ships": 8, "methanol_ships": 2, "ammonia_ships": 0, "b30_eet_ships": 0}, "tco": 402.75,    "ghg": 0.91,     "charter": 0,  "total_fuel_cost_route": 172.0750921},    "afra_europe":  {"owned_ships": {"diesel_ships": 5, "b30_ships": 0,  "methanol_ships": 0, "ammonia_ships": 0, "b30_eet_ships": 0}, "tco": 52.4165,   "ghg": 0.2437,   "charter": 28, "total_fuel_cost_route": 28.750511},    "pana_houston": {"owned_ships": {"diesel_ships": 1, "b30_ships": 0,  "methanol_ships": 0, "ammonia_ships": 0, "b30_eet_ships": 0}, "tco": 8.79673,   "ghg": 0.04292,  "charter": 8,  "total_fuel_cost_route": 5.251384651},    "mr_ny":        {"owned_ships": {"diesel_ships": 4, "b30_ships": 0,  "methanol_ships": 0, "ammonia_ships": 0, "b30_eet_ships": 0}, "tco": 31.0053,   "ghg": 0.12959,  "charter": 21, "total_fuel_cost_route": 16.41581277}}
DEFAULT_INPUTS_2040 = {"vlcc_china":   {"owned_ships": {"diesel_ships": 4, "b50_ships": 1, "methanol_ships": 0, "ammonia_ships": 0, "blueh2_ships": 0, "methane_ships": 12, "vlsfo_occs_ships":0, "b50_eet_ships":0}, "tco": 848.85, "ghg": 0.64, "charter": 5, "total_fuel_cost_route": 427.8787256},    "suez_seasia":  {"owned_ships": {"diesel_ships": 2, "b50_ships": 2, "methanol_ships": 0, "ammonia_ships": 0, "blueh2_ships":0, "methane_ships":8, "vlsfo_occs_ships":0, "b50_eet_ships":0 }, "tco": 357.2, "ghg": 0.2, "charter": 2, "total_fuel_cost_route": 128.0633766},    "suez_sing":    {"owned_ships": {"diesel_ships": 0, "b50_ships": 8, "methanol_ships": 2, "ammonia_ships": 0, "blueh2_ships":0, "methane_ships":7, "vlsfo_occs_ships":0, "b50_eet_ships":0 }, "tco": 500.31, "ghg": 0.27, "charter": 4, "total_fuel_cost_route": 168.5662639},    "afra_europe":  {"owned_ships": {"diesel_ships": 5, "b50_ships": 0, "methanol_ships": 0, "ammonia_ships": 0, "blueh2_ships":0, "methane_ships":0, "vlsfo_occs_ships":0, "b50_eet_ships":0 }, "tco": 81.69102,  "ghg": 0.239923,"charter": 18, "total_fuel_cost_route": 26.05253146},    "pana_houston": {"owned_ships": get_empty_owned_ships_dict_for_year(2040), "tco": 0.0, "ghg": 0.0, "charter": 7, "total_fuel_cost_route": 0.0},    "mr_ny":        {"owned_ships": get_empty_owned_ships_dict_for_year(2040), "tco": 0.0, "ghg": 0.0, "charter": 22, "total_fuel_cost_route": 0.0}}
DEFAULT_INPUTS_2050 = {"vlcc_china":   {"owned_ships": {"diesel_ships":0, "b100_ships":0, "methanol_ships":0, "ammonia_ships":18, "eh2_ships":0, "emethane_ships":0, "ediesel_ships":0, "b100_eet_ships":0, "bio_methane_ships":0}, "tco": 960.76, "ghg": 0.02376, "charter": 1, "total_fuel_cost_route": 696.2729488},    "suez_seasia":  {"owned_ships": {"diesel_ships":0, "b100_ships":8, "methanol_ships":0, "ammonia_ships":4, "eh2_ships":0, "emethane_ships":0, "ediesel_ships":0, "b100_eet_ships":0, "bio_methane_ships":0}, "tco": 555.78, "ghg": 0.01877, "charter": 1, "total_fuel_cost_route": 150.5271399},    "suez_sing":    {"owned_ships": {"diesel_ships":0, "b100_ships":12, "methanol_ships":0, "ammonia_ships":5, "eh2_ships":0, "emethane_ships":0, "ediesel_ships":0, "b100_eet_ships":0, "bio_methane_ships":0}, "tco": 780.3, "ghg": 0.02754, "charter": 3, "total_fuel_cost_route": 207.6813632},    "afra_europe":  {"owned_ships": get_empty_owned_ships_dict_for_year(2050), "tco": 0.0, "ghg": 0.0, "charter": 18, "total_fuel_cost_route": 0.0},    "pana_houston": {"owned_ships": get_empty_owned_ships_dict_for_year(2050), "tco": 0.0, "ghg": 0.0, "charter": 6, "total_fuel_cost_route": 0.0},    "mr_ny":        {"owned_ships": get_empty_owned_ships_dict_for_year(2050), "tco": 0.0, "ghg": 0.0, "charter": 20, "total_fuel_cost_route": 0.0}}
ALL_YEAR_DEFAULT_INPUTS = {2030: DEFAULT_INPUTS_2030, 2040: DEFAULT_INPUTS_2040, 2050: DEFAULT_INPUTS_2050}
FALLBACK_OWNED_SHIP_CATEGORIES = OWNED_SHIP_CATEGORIES_BY_YEAR[2030]
EMPTY_ROUTE_DEFAULTS = {"owned_ships": {cat.lower().replace(' ', '_').replace('(','').replace(')',''): 0 for cat in FALLBACK_OWNED_SHIP_CATEGORIES}, "charter": 0, "tco": 0.0, "ghg": 0.0, "total_fuel_cost_route": 0.0}
ROUTE_REVENUES_BY_YEAR = {2024: {"vlcc_china": 27022.67, "afra_europe": 20831.95, "pana_houston": 4142.955, "suez_seasia": 8020.872, "suez_sing": 15013.9, "mr_ny": 11989.32}, 2030: {"vlcc_china": 24503.79, "afra_europe": 17409.62, "pana_houston": 3627.734, "suez_seasia": 8040.344, "suez_sing": 15615.21, "mr_ny": 10892.34}, 2040: {"vlcc_china": 22235.63, "afra_europe": 13935.9,  "pana_houston": 3131.833, "suez_seasia": 8379.054, "suez_sing": 19341.65, "mr_ny": 11176.59}, 2050: {"vlcc_china": 19765.16, "afra_europe": 12402.56, "pana_houston": 2965.643, "suez_seasia": 8697.518, "suez_sing": 20668.0,  "mr_ny": 10895.18}}
BENCHMARK_2024_TOTAL_REVENUE = sum(ROUTE_REVENUES_BY_YEAR[2024].values())
BENCHMARK_2024 = {"total_tco_fleet": 161.26, "total_ghg_fleet": 4.9052, "total_charter_cost_fleet": 1902.8, "total_fuel_cost_fleet": 743.81, "total_revenue": BENCHMARK_2024_TOTAL_REVENUE}
CII_YEARS_DATA = [2019, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2034, 2035, 2036, 2037, 2038, 2039, 2040, 2041, 2042, 2043, 2044, 2045, 2046, 2047, 2048, 2049, 2050]
CII_RATING_DATA_BY_TYPE = { "MR Tankers (to New York)": pd.DataFrame({'Year': CII_YEARS_DATA, 'Superior': [16.04,15.24,14.92,14.60,14.28,13.86,13.44,13.02,12.59,12.17,11.75,11.33,10.91,10.49,10.07,9.65,9.23,8.80,8.38,7.96,7.54,7.12,6.70,6.28,5.86,5.44,5.01,4.59,4.17], 'Lower':    [17.73,16.85,16.49,16.14,15.78,15.32,14.85,14.38,13.92,13.45,12.99,12.52,12.06,11.59,11.13,10.66,10.20,9.73,9.26,8.80,8.33,7.87,7.40,6.94,6.47,6.01,5.54,5.08,4.61], 'Upper':    [21.88,20.78,20.34,19.91,19.47,18.89,18.32,17.75,17.17,16.60,16.02,15.45,14.88,14.30,13.73,13.15,12.58,12.00,11.43,10.86,10.28,9.71,9.13,8.56,7.98,7.41,6.84,6.26,5.69], 'Inferior': [30.13,28.62,28.02,27.41,26.81,26.02,25.23,24.44,23.65,22.86,22.07,21.28,20.49,19.69,18.90,18.11,17.32,16.53,15.74,14.95,14.16,13.37,12.58,11.79,11.00,10.20,9.41,8.62,7.83]}), "Panamax (to Houston)": pd.DataFrame({'Year': CII_YEARS_DATA, 'Superior': [13.66,12.97,12.70,12.43,12.15,11.80,11.44,11.08,10.72,10.36,10.00,9.64,9.29,8.93,8.57,8.21,7.85,7.49,7.14,6.78,6.42,6.06,5.70,5.34,4.98,4.63,4.27,3.91,3.55], 'Lower':    [15.09,14.34,14.04,13.73,13.43,13.04,12.64,12.24,11.85,11.45,11.06,10.66,10.26,9.87,9.47,9.07,8.68,8.28,7.89,7.49,7.09,6.70,6.30,5.90,5.51,5.11,4.72,4.32,3.92], 'Upper':    [18.62,17.69,17.32,16.94,16.57,16.08,15.59,15.10,14.62,14.13,13.64,13.15,12.66,12.17,11.68,11.19,10.71,10.22,9.73,9.24,8.75,8.26,7.77,7.28,6.80,6.31,5.82,5.33,4.84], 'Inferior': [25.64,24.36,23.85,23.33,22.82,22.15,21.47,20.80,20.13,19.46,18.78,18.11,17.44,16.76,16.09,15.42,14.74,14.07,13.40,12.72,12.05,11.38,10.71,10.03,9.36,8.69,8.01,7.34,6.67]}), "Aframax (to Europe)": pd.DataFrame({'Year': CII_YEARS_DATA, 'Superior': [10.13,9.62,9.42,9.22,9.01,8.75,8.48,8.22,7.95,7.68,7.42,7.15,6.89,6.62,6.35,6.09,5.82,5.56,5.29,5.03,4.76,4.49,4.23,3.96,3.70,3.43,3.16,2.90,2.63], 'Lower':    [11.19,10.63,10.41,10.18,9.96,9.67,9.37,9.08,8.79,8.49,8.20,7.90,7.61,7.32,7.02,6.73,6.44,6.14,5.85,5.55,5.26,4.97,4.67,4.38,4.08,3.79,3.50,3.20,2.91], 'Upper':    [13.81,13.12,12.84,12.56,12.29,11.93,11.56,11.20,10.84,10.48,10.11,9.75,9.39,9.03,8.66,8.30,7.94,7.58,7.21,6.85,6.49,6.13,5.76,5.40,5.04,4.68,4.31,3.95,3.59], 'Inferior': [19.01,18.06,17.68,17.30,16.92,16.42,15.92,15.42,14.93,14.43,13.93,13.43,12.93,12.43,11.93,11.43,10.93,10.43,9.93,9.44,8.94,8.44,7.94,7.44,6.94,6.44,5.94,5.44,4.94]}), "Suezmax": pd.DataFrame({'Year': CII_YEARS_DATA, 'Superior': [8.02,7.62,7.46,7.30,7.14,6.93,6.72,6.51,6.30,6.09,5.88,5.67,5.46,5.25,5.03,4.82,4.61,4.40,4.19,3.98,3.77,3.56,3.35,3.14,2.93,2.72,2.51,2.30,2.09], 'Lower':    [8.87,8.42,8.25,8.07,7.89,7.66,7.43,7.19,6.96,6.73,6.50,6.26,6.03,5.80,5.56,5.33,5.10,4.87,4.63,4.40,4.17,3.94,3.70,3.47,3.24,3.00,2.77,2.54,2.31], 'Upper':    [10.94,10.39,10.17,9.96,9.74,9.45,9.16,8.87,8.59,8.30,8.01,7.73,7.44,7.15,6.86,6.58,6.29,6.00,5.72,5.43,5.14,4.85,4.57,4.28,3.99,3.71,3.42,3.13,2.84], 'Inferior': [15.07,14.31,14.01,13.71,13.41,13.01,12.62,12.22,11.83,11.43,11.04,10.64,10.24,9.85,9.45,9.06,8.66,8.27,7.87,7.48,7.08,6.69,6.29,5.89,5.50,5.10,4.71,4.31,3.92]}), "VLCC (to China)": pd.DataFrame({'Year': CII_YEARS_DATA, 'Superior': [5.28,5.01,4.91,4.80,4.70,4.56,4.42,4.28,4.14,4.00,3.86,3.73,3.59,3.45,3.31,3.17,3.03,2.89,2.76,2.62,2.48,2.34,2.20,2.06,1.93,1.79,1.65,1.51,1.37], 'Lower':    [5.83,5.54,5.42,5.31,5.19,5.04,4.88,4.73,4.58,4.42,4.27,4.12,3.96,3.81,3.66,3.51,3.35,3.20,3.05,2.89,2.74,2.59,2.43,2.28,2.13,1.97,1.82,1.67,1.52], 'Upper':    [7.19,6.83,6.69,6.55,6.40,6.21,6.02,5.83,5.65,5.46,5.27,5.08,4.89,4.70,4.51,4.32,4.14,3.95,3.76,3.57,3.38,3.19,3.00,2.81,2.63,2.44,2.25,2.06,1.87], 'Inferior': [9.90,9.41,9.21,9.01,8.82,8.56,8.30,8.04,7.78,7.52,7.26,7.00,6.74,6.48,6.22,5.96,5.70,5.44,5.18,4.92,4.66,4.40,4.14,3.88,3.62,3.36,3.10,2.84,2.58]})
}
PETROBRAS_CII_POINTS = {
    2030: {"MR Tankers (to New York)": {"MR Tanker": 6.46}, "Panamax (to Houston)": {"Panamax": 6.81}, "Aframax (to Europe)": {"Aframax": 4.68}, "Suezmax": {"VLSFO": 3.58, "B30": 2.56, "Methanol": 0.68}, "VLCC (to China)": {"VLSFO": 4.05, "B30": 2.89}},
    2040: {"Aframax (to Europe)": {"Aframax": 4.53}, "Suezmax": {"VLSFO": 3.47, "B50": 1.8, "Methanol": 0.28, "Methane": 0.23}, "VLCC (to China)": {"VLSFO": 3.93, "B50": 2.04, "Methane": 0.26}},
    2050: {"Suezmax": {"B100": 0.13, "Ammonia": 0.04}, "VLCC (to China)": {"Ammonia": 0.04}}
}
CII_CHART_Y_MAX = {"MR Tankers (to New York)": 35, "Panamax (to Houston)": 30, "Aframax (to Europe)": 25, "Suezmax": 20, "VLCC (to China)": 15}

# --- GFI Data ---
GFI_YEARS_DATA = [2028, 2029, 2030, 2031, 2032, 2033, 2034, 2035, 2036, 2037, 2038, 2039, 2040, 2041, 2042, 2043, 2044, 2045, 2046, 2047, 2048, 2049, 2050]
GFI_COMPLIANCE_ZONES_DF = pd.DataFrame({
    'Year': GFI_YEARS_DATA,
    'GFI Base': [89.568,87.702,85.836,81.7308,77.6256,73.5204,69.4152,65.31,58.779,52.248,45.717,39.186,32.655,31.0689,29.4828,27.8967,26.3106,24.7245,23.1384,21.5523,19.9662,18.3801,16.794],
    'GFI DC':   [77.439,75.573,73.707,69.6018,65.4966,61.3914,57.2862,53.181,46.65,40.119,32.655,27.057,20.526,18.9399,17.3538,15.7677,14.1816,12.5955,11.0094,9.4233,7.8372,6.2511,4.665],
    'GFI_Credit_Upper_Limit': [19,19,19,19,19,19,19,19,19,19,19,19,14,14,14,14,3,3,3,3,3,3,3]
})
PETROBRAS_FLEET_GFI_POINTS = {2030: 75.08, 2040: 31.51, 2050: 2.67}


# --- Helper Functions & Callbacks (Keep as before) ---
# ... (format_value, initialize_session_state_once, Process Reset, Callbacks as is) ...
def format_value(value, decimal_places=2, is_currency=False, use_sig_figs_non_currency=False, sig_figs=2):
    if value is None or math.isnan(value) or abs(value) < 1e-9: return "$0.00" if is_currency else "0.00"
    try:
        if is_currency: return f"${value:,.{decimal_places}f}"
        elif use_sig_figs_non_currency:
            if value == 0: return "0.00"
            return f"{float(value):.{sig_figs}g}"
        else: return f"{value:,.{decimal_places}f}"
    except (ValueError, TypeError): return str(value)
def initialize_session_state_once():
    if 'app_initialized_fleet_v22' not in st.session_state: # New unique flag
        st.session_state.app_initialized_fleet_v22 = True
        st.session_state.selected_year = YEAR_OPTIONS[0]
        st.session_state.results = None
        st.session_state.show_results = False
        st.session_state.reset_trigger_button_flag = False
        st.session_state.analysis_period_years = ANALYSIS_LIFESPAN_YEARS
        st.session_state.discount_rate_percent = 5.0
        initial_year_to_load = st.session_state.selected_year
        defaults_for_init_year_master = ALL_YEAR_DEFAULT_INPUTS.get(initial_year_to_load, {})
        for route_key_init in ROUTE_KEYS:
            route_data = defaults_for_init_year_master.get(route_key_init, EMPTY_ROUTE_DEFAULTS)
            st.session_state[f"charter_{route_key_init}"] = route_data['charter']
            st.session_state[f"tco_{route_key_init}"] = route_data['tco']
            st.session_state[f"ghg_{route_key_init}"] = route_data['ghg']
            st.session_state[f"fuel_cost_route_{route_key_init}"] = route_data.get('total_fuel_cost_route', 0.0)
            current_owned_categories = OWNED_SHIP_CATEGORIES_BY_YEAR.get(initial_year_to_load, FALLBACK_OWNED_SHIP_CATEGORIES)
            owned_ship_defaults_for_route = route_data.get("owned_ships", {})
            for ship_cat_display_name in current_owned_categories:
                ship_cat_internal_key = ship_cat_display_name.lower().replace(' ', '_').replace('(','').replace(')','')
                session_key = f"owned_{route_key_init}_{ship_cat_internal_key}"
                st.session_state[session_key] = owned_ship_defaults_for_route.get(ship_cat_internal_key, 0)
initialize_session_state_once()
if st.session_state.get('reset_trigger_button_flag', False):
    year_to_reset = st.session_state.selected_year
    defaults_for_year = ALL_YEAR_DEFAULT_INPUTS.get(year_to_reset, {})
    for route_key in ROUTE_KEYS:
        route_defaults = defaults_for_year.get(route_key, EMPTY_ROUTE_DEFAULTS)
        st.session_state[f"charter_{route_key}"] = route_defaults['charter']
        st.session_state[f"tco_{route_key}"] = route_defaults['tco']
        st.session_state[f"ghg_{route_key}"] = route_defaults['ghg']
        st.session_state[f"fuel_cost_route_{route_key}"] = route_defaults.get('total_fuel_cost_route', 0.0)
        owned_ship_defaults_for_route = route_defaults.get("owned_ships", {})
        current_owned_categories_for_reset = OWNED_SHIP_CATEGORIES_BY_YEAR.get(year_to_reset, FALLBACK_OWNED_SHIP_CATEGORIES)
        for ship_cat_display_name in current_owned_categories_for_reset:
            ship_cat_internal_key = ship_cat_display_name.lower().replace(' ', '_').replace('(','').replace(')','')
            session_key = f"owned_{route_key}_{ship_cat_internal_key}"
            st.session_state[session_key] = owned_ship_defaults_for_route.get(ship_cat_internal_key, 0)
    st.session_state.analysis_period_years = ANALYSIS_LIFESPAN_YEARS
    st.session_state.discount_rate_percent = 5.0
    st.session_state.reset_trigger_button_flag = False
    st.session_state.results = None; st.session_state.show_results = False
    st.success(f"All inputs reset to {year_to_reset} default values.")
def clear_results_on_input_change(): st.session_state.results = None; st.session_state.show_results = False
def trigger_reset_all_inputs_and_clear_results(): st.session_state.reset_trigger_button_flag = True

# --- App Layout & Inputs ---
# (Keep App Layout and Input Sections as before)
st.title("Tanker Fleet Decision Support: Costs & Emissions")
st.divider()
st.sidebar.header("⚙️ Input Parameters")
st.sidebar.info("Define fleet composition and scenario inputs.")
selected_year = st.sidebar.selectbox("Select Target Year:", options=YEAR_OPTIONS, key='selected_year', on_change=clear_results_on_input_change)
st.sidebar.button(f"Reset ALL Inputs to {st.session_state.selected_year} Defaults", on_click=trigger_reset_all_inputs_and_clear_results)
st.sidebar.divider()
st.sidebar.subheader("Owned Fleet Composition (Per Route)")
current_owned_ship_categories_for_display = OWNED_SHIP_CATEGORIES_BY_YEAR.get(st.session_state.selected_year, [])
if not current_owned_ship_categories_for_display: st.sidebar.warning(f"No owned ship categories defined for {st.session_state.selected_year}.")
for route_key, route_display_name in TANKER_ROUTES.items():
    with st.sidebar.expander(f"Owned Ships for: {route_display_name}"):
        if not current_owned_ship_categories_for_display: st.caption("Categories not set.")
        else:
            for ship_category_display_name in current_owned_ship_categories_for_display:
                ship_cat_internal_key = ship_category_display_name.lower().replace(' ', '_').replace('(','').replace(')','')
                session_key = f"owned_{route_key}_{ship_cat_internal_key}"
                if session_key not in st.session_state: st.session_state[session_key] = 0
                st.number_input(f"{ship_category_display_name}", min_value=0, step=1, key=session_key, on_change=clear_results_on_input_change)
with st.sidebar.expander("Financial Analysis Assumptions (for NPV/Payback)", expanded=True):
    st.number_input("Analysis Period (Years):", min_value=1, max_value=50, step=1, key='analysis_period_years', on_change=clear_results_on_input_change)
    st.number_input("Annual Discount Rate (%):", min_value=0.0, max_value=20.0, step=0.5, format="%.1f", key='discount_rate_percent', on_change=clear_results_on_input_change)
st.header("🚢 Route-Specific Data (TCO, GHG, Charter, Fuel Cost)")
st.markdown("""<style>div[data-testid="stHorizontalBlock"] div[data-testid="stVerticalBlock"] div[data-baseweb="block"] > label[data-baseweb="form-control-label"] {height: 4.5em; display: flex; align-items: center; justify-content: start; white-space: normal; overflow: hidden; margin-bottom: -0.8em;}</style>""", unsafe_allow_html=True)
for key, display_name in TANKER_ROUTES.items():
    with st.expander(f"Data for: {display_name}"):
        col_in1, col_in2, col_in3, col_in4 = st.columns(4)
        charter_key = f"charter_{key}"; tco_key = f"tco_{key}"; ghg_key = f"ghg_{key}"; fuel_cost_route_key = f"fuel_cost_route_{key}"
        with col_in1: st.number_input(f"Charter Vessels", min_value=0, step=1, key=charter_key, on_change=clear_results_on_input_change)
        with col_in2: st.number_input(f"TCO (M USD)", min_value=0.0, step=0.01, format="%.5f", key=tco_key, help="Annualized TCO.", on_change=clear_results_on_input_change)
        with col_in3: st.number_input(f"GHG (M Tons CO2e)", min_value=0.0, step=0.001, format="%.5f", key=ghg_key, help=f"Total GHG for {st.session_state.selected_year}.", on_change=clear_results_on_input_change)
        with col_in4: st.number_input(f"Fuel Cost (M USD)", min_value=0.0, step=0.01, format="%.5f", key=fuel_cost_route_key, help="Route-specific total annual fuel cost.", on_change=clear_results_on_input_change)
st.divider()

# --- Calculation Trigger ---
st.header("📊 Calculate & Analyze")
if st.button("Run Analysis", type="primary"):
    current_year_calc = st.session_state.selected_year
    # (Snapshot calculation logic: TCO, GHG, Charter, Fuel Costs - as before)
    current_year_factors = ALL_CHARTER_FACTORS.get(current_year_calc, {})
    route_level_data_list = []
    calculated_total_owned_vessels_all_routes = 0
    total_tco_fleet = 0.0; total_ghg_fleet = 0.0; total_charter_cost_fleet = 0.0
    total_fleet_fuel_cost_from_routes = 0.0
    total_fleet_revenue_scenario = 0.0
    with st.spinner(f"Analyzing for {current_year_calc}..."):
        current_owned_ship_categories_for_sum = OWNED_SHIP_CATEGORIES_BY_YEAR.get(current_year_calc, [])
        scenario_revenue_data = ROUTE_REVENUES_BY_YEAR.get(current_year_calc, {})
        for route_key_iter in ROUTE_KEYS:
            for ship_cat_display_name in current_owned_ship_categories_for_sum:
                cat_key_internal = ship_cat_display_name.lower().replace(' ', '_').replace('(','').replace(')','')
                session_key_owned = f"owned_{route_key_iter}_{cat_key_internal}"
                calculated_total_owned_vessels_all_routes += st.session_state.get(session_key_owned, 0)
            total_fleet_revenue_scenario += scenario_revenue_data.get(route_key_iter, 0.0)
        for key, display_name in TANKER_ROUTES.items():
            route_owned_ships_sum = 0
            for ship_cat_display_name in current_owned_ship_categories_for_sum:
                cat_key_internal = ship_cat_display_name.lower().replace(' ', '_').replace('(','').replace(')','')
                session_key_owned = f"owned_{key}_{cat_key_internal}"
                route_owned_ships_sum += st.session_state.get(session_key_owned, 0)
            charter_count = st.session_state[f"charter_{key}"]
            tco_val = st.session_state[f"tco_{key}"]
            ghg_val = st.session_state[f"ghg_{key}"]
            fuel_cost_route_val = st.session_state[f"fuel_cost_route_{key}"]
            route_revenue_val = scenario_revenue_data.get(key, 0.0)
            factors_tuple = current_year_factors.get(key)
            route_charter_cost = 0.0
            if factors_tuple and charter_count > 0: route_charter_cost = charter_count * factors_tuple[0] * factors_tuple[1]
            elif charter_count > 0: st.warning(f"Charter factors missing for {display_name}.")
            total_charter_cost_fleet += route_charter_cost; total_tco_fleet += tco_val; total_ghg_fleet += ghg_val
            total_fleet_fuel_cost_from_routes += fuel_cost_route_val
            route_level_data_list.append({"Route": display_name, "Total Owned Ships": route_owned_ships_sum, "Charter Vessels": charter_count, "Revenue (M USD)": route_revenue_val, "TCO (M USD)": tco_val, "GHG (M Tons CO2e)": ghg_val, "Charter Cost (M USD)": route_charter_cost, "Total Fuel Cost (M USD)": fuel_cost_route_val})

    # *** UPDATED Financial Calculations for NPV/Payback ***
    initial_investment_for_npv = total_tco_fleet * ANALYSIS_LIFESPAN_YEARS
    constant_annual_net_cash_flow = 4000.0 # Million USD

    payback_period_proj = "N/A"
    if constant_annual_net_cash_flow > 1e-9 and initial_investment_for_npv > 1e-9 :
        payback_period_val = initial_investment_for_npv / constant_annual_net_cash_flow
        payback_period_proj = f"{payback_period_val:.2f} Years"
    elif initial_investment_for_npv <= 1e-9 and constant_annual_net_cash_flow > 1e-9:
        payback_period_proj = "Immediate"
    else:
        payback_period_proj = "No Payback (Annual NCF ≤ 0)"

    npv_str_proj = "N/A"
    discount_r = st.session_state.discount_rate_percent / 100.0
    analysis_horizon = ANALYSIS_LIFESPAN_YEARS

    try:
        initial_investment_npv_val = float(initial_investment_for_npv)
        ncf_proj_npv_val = float(constant_annual_net_cash_flow)
        discount_r_npv_val = float(discount_r)

        if not (math.isnan(initial_investment_npv_val) or \
                math.isnan(ncf_proj_npv_val) or \
                math.isnan(discount_r_npv_val)) and \
                analysis_horizon > 0 and discount_r_npv_val > -1:
            cash_flows_for_npv_proj = [-initial_investment_npv_val] + [ncf_proj_npv_val] * analysis_horizon
            npv_val_proj = numpy.npv(discount_r_npv_val, cash_flows_for_npv_proj)
            if math.isnan(npv_val_proj) or math.isinf(npv_val_proj):
                 npv_str_proj = "NPV Result Invalid"
            else:
                npv_str_proj = f"{format_value(npv_val_proj, decimal_places=2, is_currency=True)}"
        else:
            npv_str_proj = "NPV Error: Invalid inputs to calc"
    except Exception: # Catch any other error during conversion or npv calc
        npv_str_proj = "NPV Calc Error"

    st.session_state.results = {
        "route_data_df": pd.DataFrame(route_level_data_list),
        "total_tco_fleet": total_tco_fleet, "total_ghg_fleet": total_ghg_fleet,
        "total_charter_cost_fleet": total_charter_cost_fleet,
        "total_investment_fleet_snapshot": total_tco_fleet + total_charter_cost_fleet,
        "calculated_total_owned_vessels_all_routes": calculated_total_owned_vessels_all_routes,
        "total_annual_fuel_expenditure_fleet_million": total_fleet_fuel_cost_from_routes,
        "total_fleet_revenue_scenario": total_fleet_revenue_scenario,
        "initial_investment_for_npv": initial_investment_for_npv,
        "constant_annual_net_cash_flow_for_projection": constant_annual_net_cash_flow, # Store for cumulative chart
        "payback_period_projected": payback_period_proj,
        "npv_projected": npv_str_proj,
        "calculated_for_year": current_year_calc
    }
    st.session_state.show_results = True
    st.success(f"Analysis Complete for {current_year_calc}!")

st.divider()

# --- Output Section ---
st.header("📈 Analysis Outputs")
if st.session_state.show_results and st.session_state.results:
    results = st.session_state.results; calc_year = results["calculated_for_year"]
    # (Metrics, Route Summary Table, Visual Insights, Benchmark - as before, ensure correct keys and formatting)
    st.subheader(f"Fleet Summary & Snapshot Financials (Scenario Year: {calc_year})")
    m_r1c1, m_r1c2, m_r1c3 = st.columns(3)
    with m_r1c1: st.metric(label="Total Owned Vessels", value=f"{results['calculated_total_owned_vessels_all_routes']}")
    with m_r1c2: st.metric(label="Total Annualized TCO (M USD)", value=f"{format_value(results['total_tco_fleet'], decimal_places=2, is_currency=True)}")
    with m_r1c3: st.metric(label="Total GHG (M Tons CO2e)", value=f"{format_value(results['total_ghg_fleet'], decimal_places=2, use_sig_figs_non_currency=False)}")
    m_r2c1, m_r2c2, m_r2c3 = st.columns(3)
    with m_r2c1: st.metric(label="Total Annual Charter Cost (M USD)", value=f"{format_value(results['total_charter_cost_fleet'], decimal_places=2, is_currency=True)}")
    with m_r2c2: st.metric(label="Total Annual Fuel Cost (M USD)", value=f"{format_value(results['total_annual_fuel_expenditure_fleet_million'], decimal_places=2, is_currency=True)}")
    with m_r2c3: st.metric(label="Total Annual Investment (TCO+Charter, M USD)", value=f"{format_value(results['total_investment_fleet_snapshot'], decimal_places=2, is_currency=True)}")

    st.subheader(f"Projected Financial Performance ({ANALYSIS_LIFESPAN_YEARS}-Year Horizon, Starting {calc_year})")
    fin_cols = st.columns(3)
    with fin_cols[0]: st.metric(label=f"Assumed Initial Investment (M USD)", value=f"{format_value(results.get('initial_investment_for_npv', 0.0), decimal_places=2, is_currency=True)}")
    with fin_cols[1]: st.metric(label="Projected Payback Period", value=results.get('payback_period_projected', "N/A"))
    with fin_cols[2]: st.metric(label=f"Projected NPV @ {st.session_state.discount_rate_percent}% (M USD)", value=results.get('npv_projected', "N/A"))
    st.divider()
    st.subheader("Route-Level Summary Table (Scenario Year Snapshot)")
    df_routes = results["route_data_df"]
    if not df_routes.empty:
        df_routes_display = df_routes[(df_routes["Total Owned Ships"] > 0) | (df_routes["Charter Vessels"] > 0) | (abs(df_routes["Revenue (M USD)"]) > 1e-9) | (abs(df_routes["TCO (M USD)"]) > 1e-9) | (abs(df_routes["GHG (M Tons CO2e)"]) > 1e-9) | (abs(df_routes["Charter Cost (M USD)"]) > 1e-9) | (abs(df_routes["Total Fuel Cost (M USD)"]) > 1e-9) ]
        column_order = ["Route", "Total Owned Ships", "Charter Vessels", "Revenue (M USD)", "TCO (M USD)", "Total Fuel Cost (M USD)", "Charter Cost (M USD)", "GHG (M Tons CO2e)"]
        df_routes_display = df_routes_display.reindex(columns=column_order, fill_value=0)
        st.dataframe(df_routes_display.style.format({"Total Owned Ships": "{:,.0f}", "Charter Vessels": "{:,.0f}", "Revenue (M USD)": lambda x: format_value(x, decimal_places=2, is_currency=True), "TCO (M USD)": lambda x: format_value(x, decimal_places=2, is_currency=True), "Total Fuel Cost (M USD)": lambda x: format_value(x, decimal_places=2, is_currency=True), "Charter Cost (M USD)": lambda x: format_value(x, decimal_places=2, is_currency=True), "GHG (M Tons CO2e)": lambda x: format_value(x, decimal_places=2, use_sig_figs_non_currency=False)}), use_container_width=True)
    else: st.info("No route data.")
    st.divider()

    st.subheader("Visual Insights (Scenario Year Snapshot)")
    # --- Figure for Percentage of Owned Ship Types ---
    owned_ship_aggregation_for_plot = {}
    current_owned_categories_for_plot = OWNED_SHIP_CATEGORIES_BY_YEAR.get(calc_year, [])
    for route_k_plot in ROUTE_KEYS:
        for ship_cat_dp_name_plot in current_owned_categories_for_plot:
            ship_cat_internal_key_plot = ship_cat_dp_name_plot.lower().replace(' ', '_').replace('(','').replace(')','')
            session_key_plot = f"owned_{route_k_plot}_{ship_cat_internal_key_plot}"
            count_plot = st.session_state.get(session_key_plot, 0)
            if ship_cat_dp_name_plot not in owned_ship_aggregation_for_plot:
                owned_ship_aggregation_for_plot[ship_cat_dp_name_plot] = 0
            owned_ship_aggregation_for_plot[ship_cat_dp_name_plot] += count_plot
    owned_ship_aggregation_plot_filtered = {k: v for k,v in owned_ship_aggregation_for_plot.items() if v > 0}
    if owned_ship_aggregation_plot_filtered:
        df_owned_ship_dist = pd.DataFrame(list(owned_ship_aggregation_plot_filtered.items()), columns=['Ship Category', 'Number of Vessels'])
        fig_owned_dist = px.pie(df_owned_ship_dist, values='Number of Vessels', names='Ship Category', title=f'Owned Fleet Composition by Ship Type ({calc_year})', hole=0.3)
        fig_owned_dist.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_owned_dist, use_container_width=True)
    else: st.caption("No owned vessels to display in distribution chart.")
    st.divider()

    # (Other Visual Insights charts as before)
    viz_r1c1, viz_r1c2, viz_r1c3 = st.columns(3)
    with viz_r1c1:
        st.markdown("**Annualized TCO by Route (M USD)**");
        if not df_routes[abs(df_routes['TCO (M USD)']) > 1e-9].empty: fig_tco = px.bar(df_routes, x='Route', y='TCO (M USD)', text_auto='.2f', title="TCO"); fig_tco.update_layout(xaxis_tickangle=-45, yaxis_title="M USD", height=350, margin=dict(b=100)); st.plotly_chart(fig_tco, use_container_width=True)
        else: st.caption("No TCO data.")
        st.markdown("**Owned vs. Chartered Vessels by Route**")
        df_own_charter = df_routes[['Route', 'Total Owned Ships', 'Charter Vessels']]; df_own_charter_melted = df_own_charter.melt(id_vars=['Route'], value_vars=['Total Owned Ships', 'Charter Vessels'], var_name='Vessel Source', value_name='Number'); df_own_charter_plot = df_own_charter_melted[df_own_charter_melted['Number'] > 0]
        if not df_own_charter_plot.empty: fig_own_charter = px.bar(df_own_charter_plot, x='Route', y='Number', color='Vessel Source', barmode='group', text_auto=True, title="Owned vs. Chartered"); fig_own_charter.update_layout(xaxis_tickangle=-45, yaxis_title="Number of Vessels", height=350, margin=dict(b=100)); fig_own_charter.update_traces(texttemplate='%{y:.0f}'); st.plotly_chart(fig_own_charter, use_container_width=True)
        else: st.caption("No owned/chartered data.")
    with viz_r1c2:
        st.markdown("**GHG Emissions by Route (M Tons CO2e)**")
        if not df_routes[abs(df_routes['GHG (M Tons CO2e)']) > 1e-9].empty: fig_ghg = px.bar(df_routes, x='Route', y='GHG (M Tons CO2e)', text_auto='.2f', title="GHG Emissions"); fig_ghg.update_layout(xaxis_tickangle=-45, yaxis_title="M Tons CO2e", height=350, margin=dict(b=100)); st.plotly_chart(fig_ghg, use_container_width=True)
        else: st.caption("No GHG data.")
        st.markdown("**Calculated Charter Cost by Route (M USD)**")
        if not df_routes[abs(df_routes['Charter Cost (M USD)']) > 1e-9].empty: fig_charter_cost = px.bar(df_routes, x='Route', y='Charter Cost (M USD)', text_auto='.2f', title="Charter Cost"); fig_charter_cost.update_layout(xaxis_tickangle=-45, yaxis_title="M USD", height=350, margin=dict(b=100)); st.plotly_chart(fig_charter_cost, use_container_width=True)
        else: st.caption("No charter costs.")
    with viz_r1c3:
        st.markdown("**Total Fuel Cost by Route (M USD)**")
        if not df_routes[abs(df_routes['Total Fuel Cost (M USD)']) > 1e-9].empty: fig_fuel_route = px.bar(df_routes, x='Route', y='Total Fuel Cost (M USD)', text_auto='.2f', title="Fuel Cost by Route"); fig_fuel_route.update_layout(xaxis_tickangle=-45, yaxis_title="Fuel Cost (M USD)", height=350, margin=dict(b=100)); st.plotly_chart(fig_fuel_route, use_container_width=True)
        else: st.caption("No route fuel cost data.")
        st.markdown("**Cost Comparison: TCO, Charter, Fuel by Route (M USD)**")
        df_cost_comp_all = df_routes[((abs(df_routes['Charter Cost (M USD)']) > 1e-9) | (abs(df_routes['TCO (M USD)']) > 1e-9) | (abs(df_routes['Total Fuel Cost (M USD)']) > 1e-9) )]
        if not df_cost_comp_all.empty: df_melted_costs_all = df_cost_comp_all.melt(id_vars=['Route'], value_vars=['TCO (M USD)', 'Charter Cost (M USD)', 'Total Fuel Cost (M USD)'], var_name='Cost Type', value_name='Cost (M USD)'); fig_cost_comp_all = px.bar(df_melted_costs_all, x='Route', y='Cost (M USD)', color='Cost Type', barmode='group', text_auto='.2f', title="Key Costs by Route"); fig_cost_comp_all.update_layout(xaxis_tickangle=-45, yaxis_title="Cost (M USD)", height=350, margin=dict(b=100)); st.plotly_chart(fig_cost_comp_all, use_container_width=True)
        else: st.caption("No cost data for comparison.")

    with st.expander("Projected Cumulative Net Cash Flow Over Analysis Period (Constant NCF)"):
        constant_ncf_for_chart = results.get('constant_annual_net_cash_flow_for_projection', 0.0)
        initial_investment_chart = results.get('initial_investment_for_npv', 0.0)
        if st.session_state.analysis_period_years > 0:
            cumulative_data = [-initial_investment_chart] # Year 0 is just the investment
            for _ in range(st.session_state.analysis_period_years):
                cumulative_data.append(cumulative_data[-1] + constant_ncf_for_chart)
            df_cumulative = pd.DataFrame({
                'Year': list(range(st.session_state.analysis_period_years + 1)), # 0 to N years
                'Cumulative Net Cash Flow (M USD)': cumulative_data
            })
            fig_cumulative = px.line(df_cumulative, x='Year', y='Cumulative Net Cash Flow (M USD)',
                                     title=f"Cumulative Net Cash Flow (Constant Annual NCF of {format_value(constant_ncf_for_chart,2,True)} M)", markers=True)
            fig_cumulative.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Breakeven")
            fig_cumulative.update_layout(height=400)
            st.plotly_chart(fig_cumulative, use_container_width=True)
        else:
            st.caption("Cannot plot cumulative cash flow (Analysis period is 0).")
    st.divider()

    # --- CII Chart Section ---
    st.subheader("CII Rating Projection vs. Petrobras Tanker Targets")
    # (CII chart logic as before)
    cii_chart_cols = st.columns(min(3, len(CII_RATING_DATA_BY_TYPE)))
    cii_col_idx = 0
    for cii_vessel_type_key_display_name, cii_df_to_plot in CII_RATING_DATA_BY_TYPE.items():
        with cii_chart_cols[cii_col_idx % len(cii_chart_cols)]:
            st.markdown(f"**{cii_vessel_type_key_display_name}**")
            if cii_df_to_plot is not None and not cii_df_to_plot.empty:
                fig_cii = go.Figure()
                max_y_cii = CII_CHART_Y_MAX.get(cii_vessel_type_key_display_name, 35)
                fig_cii.add_trace(go.Scatter(x=cii_df_to_plot['Year'], y=[max_y_cii] * len(cii_df_to_plot['Year']), fill=None, mode='lines', line_color='rgba(255,0,0,0)', showlegend=False))
                fig_cii.add_trace(go.Scatter(x=cii_df_to_plot['Year'], y=cii_df_to_plot['Inferior'], fill='tonexty', mode='lines', line_color='rgba(255,0,0,0.3)', fillcolor='rgba(255,100,100,0.3)', name='E (Inferior+)'))
                fig_cii.add_trace(go.Scatter(x=cii_df_to_plot['Year'], y=cii_df_to_plot['Upper'], fill='tonexty', mode='lines', line_color='rgba(255,165,0,0.3)', fillcolor='rgba(255,200,100,0.3)', name='D (Upper-Inferior)'))
                fig_cii.add_trace(go.Scatter(x=cii_df_to_plot['Year'], y=cii_df_to_plot['Lower'], fill='tonexty', mode='lines', line_color='rgba(255,255,0,0.3)', fillcolor='rgba(255,255,150,0.3)', name='C (Lower-Upper)'))
                fig_cii.add_trace(go.Scatter(x=cii_df_to_plot['Year'], y=cii_df_to_plot['Superior'], fill='tonexty', mode='lines', line_color='rgba(0,0,255,0.3)', fillcolor='rgba(100,100,255,0.3)', name='B (Superior-Lower)'))
                fig_cii.add_trace(go.Scatter(x=cii_df_to_plot['Year'], y=[0] * len(cii_df_to_plot['Year']), fill='tonexty', mode='lines', line_color='rgba(0,128,0,0.3)', fillcolor='rgba(100,200,100,0.3)', name='A (Below Superior)'))
                petrobras_points_for_year_and_vessel = PETROBRAS_CII_POINTS.get(calc_year, {}).get(cii_vessel_type_key_display_name, {})
                if petrobras_points_for_year_and_vessel:
                    for label, cii_value in petrobras_points_for_year_and_vessel.items():
                        fig_cii.add_trace(go.Scatter(x=[calc_year], y=[cii_value], mode='markers+text', name=f"Petrobras {calc_year}: {label} ({cii_value})", marker=dict(symbol='star', size=12, color="black"), text=[f"{label} ({cii_value})"], textposition="top center", textfont=dict(size=10)))
                fig_cii.update_layout(title=f'CII Bands ({calc_year} Targets)', xaxis_title='Year', yaxis_title='CII Value', yaxis_range=[0, max_y_cii], height=400, legend_title_text='Rating', plot_bgcolor='white', margin=dict(t=50, b=50))
                st.plotly_chart(fig_cii, use_container_width=True)
            else: st.info(f"CII data for '{cii_vessel_type_key_display_name}' not available.")
        cii_col_idx +=1
    st.divider()
    st.divider()
    st.subheader("GFI Trajectory & Compliance Zones vs. Petrobras Fleet Optimal WtW")

    # --- GFI Compliance Zone Chart ---
    if not GFI_COMPLIANCE_ZONES_DF.empty:
        fig_gfi = go.Figure()
        max_y_gfi = 95  # As specified

        # Zone 1 (Red): Above GFI Base
        fig_gfi.add_trace(go.Scatter(
            x=GFI_COMPLIANCE_ZONES_DF['Year'],
            y=[max_y_gfi] * len(GFI_COMPLIANCE_ZONES_DF['Year']),
            fill=None, mode='lines', line_color='rgba(255,0,0,0)', showlegend=False
        ))
        fig_gfi.add_trace(go.Scatter(
            x=GFI_COMPLIANCE_ZONES_DF['Year'], y=GFI_COMPLIANCE_ZONES_DF['GFI Base'],
            fill='tonexty', mode='lines', line_color='rgba(220,20,60,0.5)',  # Crimson for boundary
            fillcolor='rgba(255,100,100,0.3)', name='Zone 1 (> GFI Base)'  # Red fill
        ))

        # Zone 2 (Orange): GFI Base to GFI DC
        fig_gfi.add_trace(go.Scatter(
            x=GFI_COMPLIANCE_ZONES_DF['Year'], y=GFI_COMPLIANCE_ZONES_DF['GFI DC'],
            fill='tonexty', mode='lines', line_color='rgba(255,140,0,0.5)',  # DarkOrange for boundary
            fillcolor='rgba(255,200,100,0.3)', name='Zone 2 (GFI Base - DC)'  # Orange fill
        ))

        # Zone 3 (Light Green): GFI DC to GFI_Credit_Upper_Limit
        fig_gfi.add_trace(go.Scatter(
            x=GFI_COMPLIANCE_ZONES_DF['Year'], y=GFI_COMPLIANCE_ZONES_DF['GFI_Credit_Upper_Limit'],
            fill='tonexty', mode='lines', line_color='rgba(144,238,144,0.5)',  # LightGreen for boundary
            fillcolor='rgba(152,251,152,0.3)', name='Zone 3 (GFI DC - Credit Limit)'  # Light Green fill
        ))

        # Zone 4 (Dark Green): GFI_Credit_Upper_Limit to 0
        fig_gfi.add_trace(go.Scatter(
            x=GFI_COMPLIANCE_ZONES_DF['Year'], y=[0] * len(GFI_COMPLIANCE_ZONES_DF['Year']),
            fill='tonexty', mode='lines', line_color='rgba(0,100,0,0.5)',  # DarkGreen for boundary
            fillcolor='rgba(60,179,113,0.3)', name='Zone 4 (< GFI Credit Limit)'  # Dark Green / MediumSeaGreen fill
        ))

        # Plot Petrobras Fleet Optimal WtW points
        gfi_points_x = []
        gfi_points_y = []
        gfi_points_text = []
        for year_pt, gfi_val in PETROBRAS_FLEET_GFI_POINTS.items():
            if year_pt in GFI_COMPLIANCE_ZONES_DF['Year'].values:  # Only plot if year is in our GFI data range
                gfi_points_x.append(year_pt)
                gfi_points_y.append(gfi_val)
                gfi_points_text.append(f"WtW: {gfi_val}<br>Year: {year_pt}")

        if gfi_points_x:
            fig_gfi.add_trace(go.Scatter(
                x=gfi_points_x, y=gfi_points_y,
                mode='markers+text', name='Petrobras Fleet Optimal WtW',
                marker=dict(symbol='diamond', size=12, color="black"),
                text=gfi_points_text, textposition="top right",
                textfont=dict(size=10, color="black")
            ))

        fig_gfi.update_layout(
            title='GFI Compliance Zones vs. Petrobras Fleet Optimal WtW',
            xaxis_title='Year',
            yaxis_title='GFI Value (gCO2eq/MJ) - Lower is Better',
            yaxis_range=[0, max_y_gfi],
            height=500,
            legend_title_text='Compliance Zones',
            plot_bgcolor='white',
            yaxis_gridcolor='lightgrey',
            xaxis_gridcolor='lightgrey'
        )
        st.plotly_chart(fig_gfi, use_container_width=True)
    else:
        st.info("GFI boundary data not available to plot.")
    # --- Benchmark Comparison Section ---
    # (Benchmark plotting as before)
    st.subheader(f"Overall Benchmark Comparison ({calc_year} vs. {BENCHMARK_YEAR})")
    bench_col1, bench_col2, bench_col3, bench_col4 = st.columns(4)
    plot_height_bench = 300
    def create_benchmark_chart(metric_name, scenario_value, benchmark_value_dict_key, unit_label):
        benchmark_val = BENCHMARK_2024[benchmark_value_dict_key]
        if benchmark_val == 0 and scenario_value == 0: percent_change = "0.0%"
        elif abs(benchmark_val) < 1e-9 : percent_change = "N/A (Benchmark is ~0)"
        else: percent_change_val = ((scenario_value - benchmark_val) / abs(benchmark_val)) * 100; percent_change = f"{percent_change_val:+.1f}%"
        data_bench = [{'Category': f'{BENCHMARK_YEAR} Benchmark', 'Value': benchmark_val, '% Change': 'Benchmark'}, {'Category': f'{calc_year} Scenario', 'Value': scenario_value, '% Change': percent_change}]
        df_bench = pd.DataFrame(data_bench)
        fig_b = px.bar(df_bench, x='Category', y='Value', text_auto='.2f', title=f"Total {metric_name} ({unit_label})", height=plot_height_bench, hover_data={'Category': True, 'Value': ':.2f', '% Change': True})
        fig_b.update_layout(xaxis_title=None, yaxis_title=unit_label); return fig_b
    with bench_col1: fig = create_benchmark_chart("TCO", results['total_tco_fleet'], 'total_tco_fleet', "M USD"); st.plotly_chart(fig, use_container_width=True)
    with bench_col2: fig = create_benchmark_chart("GHG Emissions", results['total_ghg_fleet'], 'total_ghg_fleet', "M Tons CO2e"); st.plotly_chart(fig, use_container_width=True)
    with bench_col3: fig = create_benchmark_chart("Charter Cost", results['total_charter_cost_fleet'], 'total_charter_cost_fleet', "M USD"); st.plotly_chart(fig, use_container_width=True)
    with bench_col4: fig = create_benchmark_chart("Fuel Cost", results['total_annual_fuel_expenditure_fleet_million'], 'total_fuel_cost_fleet', "M USD"); st.plotly_chart(fig, use_container_width=True)
    with st.expander("Exploratory: GHG vs. Charter Vessels (Bubble Size by TCO)"):
        df_scatter = df_routes[(df_routes['Charter Vessels'] > 0) & (abs(df_routes['GHG (M Tons CO2e)']) > 1e-9)]
        if not df_scatter.empty:
            df_scatter_copy = df_routes[(df_routes['Charter Vessels'] > 0) & (abs(df_routes['GHG (M Tons CO2e)']) > 1e-9)].copy() # Ensure it's a copy for modification
            df_scatter_copy.loc[:, 'TCO for Sizing (M USD)'] = df_scatter_copy['TCO (M USD)'].apply(lambda x: max(x, 0.1))
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
