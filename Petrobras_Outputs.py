import streamlit as st
import pandas as pd
import plotly.express as px
import math
import datetime
from decimal import Decimal # For potential future formatting needs

# --- Configuration ---

YEAR_OPTIONS = [2030, 2040, 2050]

TANKER_ROUTES = {
    "vlcc_china": "VLCC (to China)",
    "suez_seasia": "Suezmax (to SE Asia)",
    "suez_sing": "Suezmax (to Singapore)",
    "afra_europe": "Aframax (to Europe)",
    "pana_houston": "Panamax (to Houston)",
    "mr_ny": "MR Tankers (to New York)"
}
ROUTE_KEYS = list(TANKER_ROUTES.keys())
ROUTE_NAMES = list(TANKER_ROUTES.values())

OWNED_FUEL_TYPES = [
    "VLSFO", "Bio-Methanol", "e-Ammonia", "Bio-Diesel", "e-diesel",
    "Bio-Methane", "e-Hydrogen", "e-Methanol", "e-Methane",
    "B30_EET", "B50_EET", "VLSFO_OCCS", "Blue-Hydrogen"
]

# --- Charter Cost Factors by Year (multiplier2 now in Million USD) ---
CHARTER_FACTORS_2030 = {
    "vlcc_china": {"multiplier1": 4.5, "multiplier2": 6.96}, # 6.96 Million USD
    "suez_seasia": {"multiplier1": 5.8, "multiplier2": 4.66}, # 4.66 Million USD
    "suez_sing": {"multiplier1": 5.8, "multiplier2": 4.66}, # 4.66 Million USD
    "afra_europe": {"multiplier1": 9.2, "multiplier2": 3.68}, # 3.68 Million USD
    "pana_houston": {"multiplier1": 11.4, "multiplier2": 2.63}, # 2.63 Million USD
    "mr_ny": {"multiplier1": 10.5, "multiplier2": 2.25}, # 2.25 Million USD
}
CHARTER_FACTORS_2040 = {
    "vlcc_china": {"multiplier1": 4.5, "multiplier2": 7.24}, # 7.24 Million USD
    "suez_seasia": {"multiplier1": 5.8, "multiplier2": 4.84}, # 4.84 Million USD
    "suez_sing": {"multiplier1": 5.8, "multiplier2": 4.84}, # 4.84 Million USD
    "afra_europe": {"multiplier1": 9.2, "multiplier2": 3.83}, # 3.83 Million USD
    "pana_houston": {"multiplier1": 11.4, "multiplier2": 2.74}, # 2.74 Million USD
    "mr_ny": {"multiplier1": 10.5, "multiplier2": 2.34}, # 2.34 Million USD
}
CHARTER_FACTORS_2050 = {
    "vlcc_china": {"multiplier1": 4.5, "multiplier2": 7.52}, # 7.52 Million USD
    "suez_seasia": {"multiplier1": 5.8, "multiplier2": 5.03}, # 5.03 Million USD
    "suez_sing": {"multiplier1": 5.8, "multiplier2": 5.03}, # 5.03 Million USD
    "afra_europe": {"multiplier1": 9.2, "multiplier2": 3.98}, # 3.98 Million USD
    "pana_houston": {"multiplier1": 11.4, "multiplier2": 2.85}, # 2.85 Million USD
    "mr_ny": {"multiplier1": 10.5, "multiplier2": 2.43}, # 2.43 Million USD
}
# Combine into a single dictionary for easy lookup
ALL_CHARTER_FACTORS = {
    2030: CHARTER_FACTORS_2030,
    2040: CHARTER_FACTORS_2040,
    2050: CHARTER_FACTORS_2050
}

# --- Helper Function for Formatting ---
def format_value(value, sig_figs=3):
    """Formats a number to approximately N significant figures, handling zero."""
    if value == 0 or value is None or math.isnan(value):
        return "0.00"
    if abs(value) < 1e-9: # Handle very small numbers close to zero
        return "0.00"

    # Use 'g' format specifier for general significant figure formatting
    try:
        formatted_val = f"{value:.{sig_figs}g}"
        # If 'g' results in scientific notation for very small/large numbers,
        # you might want to force fixed point for consistency in tables/metrics.
        # Example: If forcing fixed point is desired:
        # if 'e' in formatted_val:
        #      return f"{value:.2f}" # Force 2 decimal places if scientific
        return formatted_val
    except (ValueError, TypeError):
        return str(value) # Fallback


# --- Initialize Session State ---
default_values = {
    'selected_year': YEAR_OPTIONS[0],
    'results': None
}
# Add owned vessel keys
for fuel in OWNED_FUEL_TYPES:
    key = f"owned_{fuel.lower().replace('-', '_').replace(' ', '_')}"
    default_values[key] = 0
# Add route-specific keys (Inputs now expected in Millions where specified)
for key in ROUTE_KEYS:
    default_values[f"charter_{key}"] = 0
    default_values[f"tco_{key}"] = 0.0 # Expected input in Million USD
    default_values[f"ghg_{key}"] = 0.0 # Expected input in Million tons CO2e

# Initialize if keys don't exist
for key, default_value in default_values.items():
    if key not in st.session_state:
        st.session_state[key] = default_value


# --- App Layout ---
st.set_page_config(layout="wide")
st.title("Tanker Fleet Cost and Emissions Analyzer")
st.divider()

# --- Input Section ---
st.sidebar.header("⚙️ Input Parameters")
st.sidebar.info("Enter fleet details and external data below.")

# == Global Input ==
st.session_state.selected_year = st.sidebar.selectbox(
    "Select Target Year:",
    options=YEAR_OPTIONS,
    key='year_select_sidebar'
)

# == Owned Fleet Inputs (Sidebar) ==
st.sidebar.subheader("Owned Fleet Composition")
cols_owned = st.sidebar.columns(2)
col_idx = 0
for i, fuel in enumerate(OWNED_FUEL_TYPES):
    key = f"owned_{fuel.lower().replace('-', '_').replace(' ', '_')}"
    with cols_owned[col_idx]:
        st.number_input(
            f"# Owned {fuel}",
            min_value=0,
            step=1,
            key=key
        )
    col_idx = (col_idx + 1) % 2
st.sidebar.divider()

# == Per-Route Inputs (Main Area using Expanders/Columns) ==
st.header("🚢 Route-Specific Inputs")
st.info("Enter Charter numbers and data from external analysis (e.g., Matlab) for each route.")

# Apply CSS to align input boxes - remains the same
st.markdown("""
<style>
div[data-testid="stHorizontalBlock"] div[data-testid="stVerticalBlock"] div[data-baseweb="block"] > label[data-baseweb="form-control-label"] {
    height: 3.5em; display: flex; align-items: center; justify-content: start;
    white-space: normal; overflow: hidden; margin-bottom: -0.5em;
}
</style>
""", unsafe_allow_html=True)


for key, display_name in TANKER_ROUTES.items():
    with st.expander(f"Inputs for: {display_name}"):
        col_in1, col_in2, col_in3 = st.columns(3)
        charter_key = f"charter_{key}"
        tco_key = f"tco_{key}"
        ghg_key = f"ghg_{key}"

        with col_in1:
            st.number_input(
                f"Charter Vessels", # Shortened Label
                min_value=0,
                step=1,
                key=charter_key
            )
        with col_in2:
            st.number_input(
                f"TCO (Million USD)", # **FIX 1: Updated Unit Label**
                min_value=0.0,
                step=0.1, # Adjust step for millions
                format="%.3f", # Allow more precision for input if needed
                key=tco_key,
                help="Enter Total Cost of Ownership in **Million USD** from external analysis." # **FIX 1: Updated Help Text**
            )
        with col_in3:
            st.number_input(
                f"GHG Emission (M tons CO2e)", # **FIX 1: Updated Unit Label**
                min_value=0.0,
                step=0.1, # Adjust step for millions
                format="%.3f", # Allow more precision for input if needed
                key=ghg_key,
                help=f"Enter Owner Fleet GHG Emission in **Million tons CO2e** from external analysis for {st.session_state.selected_year}." # **FIX 1: Updated Help Text**
            )
st.divider()

# --- Calculation Trigger ---
st.header("📊 Calculate & Analyze")
if st.button("Run Analysis", type="primary"):
    # --- Perform Calculations (Values are now directly in Millions where specified) ---
    calculated_charter_costs = {} # Store costs in Million USD
    total_charter_cost = 0.0     # In Million USD
    total_ghg_emissions = 0.0    # In Million tons CO2e
    total_tco = 0.0              # In Million USD

    tco_data_for_chart = {}      # Data in Million USD
    ghg_data_for_chart = {}      # Data in Million tons CO2e

    current_charter_factors = ALL_CHARTER_FACTORS.get(st.session_state.selected_year, CHARTER_FACTORS_2030)
    current_charter_counts = {f"charter_{key}": st.session_state[f"charter_{key}"] for key in ROUTE_KEYS}
    current_tco_values = {f"tco_{key}": st.session_state[f"tco_{key}"] for key in ROUTE_KEYS} # Input is Million USD
    current_ghg_values = {f"ghg_{key}": st.session_state[f"ghg_{key}"] for key in ROUTE_KEYS} # Input is Million tons CO2e

    for key, display_name in TANKER_ROUTES.items():
        charter_count = current_charter_counts[f"charter_{key}"]
        tco_val = current_tco_values[f"tco_{key}"] # Already in Million USD
        ghg_val = current_ghg_values[f"ghg_{key}"] # Already in Million tons CO2e

        # Calculate Charter Cost for the route (result is in Million USD)
        factors = current_charter_factors.get(key)
        route_charter_cost = 0.0 # Default if factors missing
        if factors:
            # multiplier2 is already in Million USD
            route_charter_cost = charter_count * factors["multiplier1"] * factors["multiplier2"]
        else:
             st.warning(f"Charter factors not found for route '{key}' in year {st.session_state.selected_year}. Assuming 0 cost.")

        calculated_charter_costs[display_name] = route_charter_cost # Store Million USD cost
        total_charter_cost += route_charter_cost

        # Sum GHG (Million tons CO2e)
        total_ghg_emissions += ghg_val

        # Sum TCO (Million USD)
        total_tco += tco_val

        # Prepare data for charts (already in Millions)
        tco_data_for_chart[display_name] = tco_val
        ghg_data_for_chart[display_name] = ghg_val

    # Calculate Total Investment (Million USD)
    total_investment = total_tco + total_charter_cost

    # Store results (values are already in millions)
    st.session_state.results = {
        "tco_data": tco_data_for_chart,
        "ghg_data": ghg_data_for_chart,
        "charter_costs_per_route": calculated_charter_costs,
        "total_charter_cost": total_charter_cost,
        "total_ghg_emissions": total_ghg_emissions,
        "total_investment": total_investment,
        "calculated_for_year": st.session_state.selected_year
    }
    st.success("Analysis Complete!")

st.divider()

# --- Output Section ---
st.header("📈 Analysis Outputs")

if st.session_state.results:
    results = st.session_state.results
    calc_year = results["calculated_for_year"]

    st.subheader(f"Visualizations (Year: {calc_year})")
    plot_col1, plot_col2 = st.columns(2)

    # Chart 1: TCO
    with plot_col1:
        # Check for non-zero values before plotting
        if results["tco_data"] and any(abs(v) > 1e-9 for v in results["tco_data"].values()):
            tco_df = pd.DataFrame(list(results["tco_data"].items()), columns=['Route', 'TCO (Million USD)'])
            tco_df_plot = tco_df[abs(tco_df['TCO (Million USD)']) > 1e-9]
            if not tco_df_plot.empty:
                fig_tco = px.bar(tco_df_plot, x='Route', y='TCO (Million USD)',
                                 title='Total Cost of Ownership by Route',
                                 labels={'TCO (Million USD)': 'TCO (Million USD)'}, # **FIX 3: Updated Y-axis Label**
                                 text_auto='.3s') # SI notation for bar labels
                fig_tco.update_layout(xaxis_tickangle=-45)
                fig_tco.update_yaxes(tickformat=",.2f") # Keep explicit format
                st.plotly_chart(fig_tco, use_container_width=True)
            else:
                 st.info("TCO values are effectively zero.")
        else:
            st.info("No TCO data entered to plot.")

    # Chart 2: GHG
    with plot_col2:
        # Check for non-zero values before plotting
        if results["ghg_data"] and any(abs(v) > 1e-9 for v in results["ghg_data"].values()):
            ghg_df = pd.DataFrame(list(results["ghg_data"].items()), columns=['Route', 'GHG (Million tons CO2e)'])
            ghg_df_plot = ghg_df[abs(ghg_df['GHG (Million tons CO2e)']) > 1e-9]
            if not ghg_df_plot.empty:
                fig_ghg = px.bar(ghg_df_plot, x='Route', y='GHG (Million tons CO2e)',
                                 title=f'Owner Fleet GHG Emissions by Route ({calc_year})',
                                 labels={'GHG (Million tons CO2e)': 'GHG (Million tons CO2e)'},
                                 # *** FIX: Change text_auto format specifier ***
                                 text_auto='.2f')  # Use fixed 2 decimal places for labels on bars
                # *********************************************
                fig_ghg.update_layout(xaxis_tickangle=-45)
                fig_ghg.update_yaxes(tickformat=",.2f")  # Keep explicit format for y-axis
                st.plotly_chart(fig_ghg, use_container_width=True)
            else:
                st.info("GHG Emission values are effectively zero.")
        else:
            st.info("No GHG Emission data entered to plot.")

    st.divider()

    # --- Calculated Metrics ---
    st.subheader(f"Calculated Totals (Year: {calc_year})")
    metric_col1, metric_col2, metric_col3 = st.columns(3)

    with metric_col1:
        val = results['total_charter_cost'] # Already in Million USD
        st.metric(label="Total Charter Cost (Million USD)", # **FIX 1: Updated Unit Label**
                  value=format_value(val, 3)) # **FIX 2: Format using helper**
    with metric_col2:
        val = results['total_ghg_emissions'] # Already in Million tons CO2e
        st.metric(label="Total Owner Fleet GHG (M tons CO2e)", # **FIX 1: Updated Unit Label**
                  value=format_value(val, 3)) # **FIX 2: Format using helper**
    with metric_col3:
        val = results['total_investment'] # Already in Million USD
        st.metric(label="Total Investment (Million USD)", # **FIX 1: Updated Unit Label**
                  value=format_value(val, 3)) # **FIX 2: Format using helper**

    # Optional: Detailed Charter Costs
    with st.expander("View Detailed Charter Costs by Route"):
        if results['charter_costs_per_route']:
             # Values are already in Million USD
             charter_df = pd.DataFrame(list(results['charter_costs_per_route'].items()), columns=['Route', 'Charter Cost (Million USD)'])
             st.dataframe(charter_df.style.format({"Charter Cost (Million USD)": lambda x: format_value(x, 3)}), use_container_width=True) # **FIX 2: Format using helper**
        else:
             st.write("No charter costs calculated.")

else:
    st.info("Click 'Run Analysis' after entering all required inputs.")

# --- Footer ---
st.divider()
current_year = datetime.datetime.now().year
st.caption(f"© {current_year} [ABS Energy Analytics Lab: Dr. Chenxi Ji]. All rights reserved.") # Replace placeholder
st.caption("Calculations based on user inputs and predefined factors. Verify external data sources.")
