import streamlit as st
import airportsdata
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import haversine_distances
from math import radians
import itertools  # Added to generate all possible route permutations

# Configure the page
st.set_page_config(page_title="IATA Route Optimizer", page_icon="✈️", layout="wide")

st.title("✈️ Global Flight Route Optimizer (TSP)")
st.markdown("Enter a list of IATA airport codes to calculate all efficient travel routes.")

# --- 1. Data Loading ---
@st.cache_data
def get_airport_db():
    # Loads the offline dictionary of global airports
    return airportsdata.load('IATA')

airports = get_airport_db()

# --- 2. User Input ---
default_route = "PNH, REP, BKK, SGN, NRT"
user_input = st.text_input("Enter IATA Codes (comma-separated):", value=default_route)

if st.button("Optimize Route"):
    # Clean up the input
    codes = [code.strip().upper() for code in user_input.split(',')]
    
    locations_in_radians = []
    valid_codes = []
    
    # --- 3. Coordinate Lookup ---
    for code in codes:
        if code in airports:
            lat = airports[code]['lat']
            lon = airports[code]['lon']
            locations_in_radians.append([radians(lat), radians(lon)])
            valid_codes.append(code)
        else:
            st.error(f"Could not find IATA code: {code}")
            
    # Add a safety limit for brute-force permutations
    if len(valid_codes) > 8:
        st.error("Calculating all permutations for more than 8 airports requires massive computational power. Please reduce the number of airports.")
    elif len(valid_codes) > 2:
        # --- 4. Generate Haversine Matrix ---
        result = haversine_distances(locations_in_radians)
        distance_matrix = result * 6371.0 # Earth's radius in km
        
        # --- 5. Calculate ALL Permutations (Brute Force TSP) ---
        start_node = 0 # Lock the first entered airport as the origin/destination
        other_nodes = list(range(1, len(valid_codes)))
        
        all_journeys = []
        
        # Generate every possible order of the middle stops
        for p in itertools.permutations(other_nodes):
            # Construct the route: Start -> Permutation -> Start
            route_indices = [start_node] + list(p) + [start_node]
            
            total_distance = 0.0
            for i in range(len(route_indices) - 1):
                total_distance += distance_matrix[route_indices[i]][route_indices[i+1]]
                
            # Translate indices back to IATA codes
            route_codes = [valid_codes[i] for i in route_indices]
            route_string = " ➔ ".join(route_codes)
            
            all_journeys.append({
                "Route": route_string, 
                "Distance (km)": total_distance
            })
            
        # Create a DataFrame and sort it from shortest to longest journey
        df_all_journeys = pd.DataFrame(all_journeys).sort_values(by="Distance (km)").reset_index(drop=True)
        
        # Format the distance column for better readability
        df_all_journeys["Distance (km)"] = df_all_journeys["Distance (km)"].apply(lambda x: f"{x:,.0f}")
        
        # --- 6. Display Results ---
        st.success("All routes calculated successfully! Well done on mapping these out.")
        
        # Pull out the absolute best route for the top highlight
        best_route_string = df_all_journeys.iloc[0]["Route"]
        best_route_distance = df_all_journeys.iloc[0]["Distance (km)"]
        
        st.subheader("The Most Optimized Path")
        st.markdown(f"**{best_route_string}**")
        st.metric("Total Distance", f"{best_route_distance} km")
        
        st.divider()
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader(f"All {len(df_all_journeys)} Possible Journeys")
            st.dataframe(df_all_journeys, use_container_width=True)
            
        with col2:
            st.subheader("Raw Distance Matrix (km)")
            df_matrix = pd.DataFrame(distance_matrix, index=valid_codes, columns=valid_codes).round(0)
            st.dataframe(df_matrix, use_container_width=True)
            
    else:
        st.warning("Please enter at least 3 valid IATA codes to calculate routes.")