import streamlit as st
import airportsdata
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import haversine_distances
from math import radians
import itertools  # Added to generate all possible route permutations

# --- 1. Data Loading ---
@st.cache_data
def get_airport_db():
    # Loads the offline dictionary of global airports
    return airportsdata.load('IATA')

airports = get_airport_db()

# --- 2. User Input ---
default_route = "KTI, BKK, SIN,RGN"
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
            
    if len(valid_codes) > 2:
        # --- 4. Generate Haversine Matrix ---
        result = haversine_distances(locations_in_radians)
        distance_matrix = result * 6371.0 # Earth's radius in km
        
        # --- 5. Solve TSP (Nearest Neighbor Algorithm) ---
        unvisited = list(range(1, len(valid_codes)))
        current_node = 0
        route_indices = [current_node]
        total_distance = 0.0
        
        while unvisited:
            # Find the closest unvisited node
            next_node = min(unvisited, key=lambda node: distance_matrix[current_node][node])
            
            # Update distance and move to the next node
            total_distance += distance_matrix[current_node][next_node]
            route_indices.append(next_node)
            unvisited.remove(next_node)
            current_node = next_node
            
        # Add the return trip to complete the loop
        total_distance += distance_matrix[current_node][route_indices[0]]
        route_indices.append(route_indices[0])
        
        # Translate indices back to IATA codes
        optimized_route = [valid_codes[i] for i in route_indices]
        
        # --- 6. Display Results ---
        st.success("Route optimized successfully! Well done on mapping this out.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Your Optimized Path")
            st.markdown(f"**{' ➔ '.join(optimized_route)}**")
            st.metric("Total Distance", f"{total_distance:,.0f} km")
            
        with col2:
            st.subheader("Raw Distance Matrix (km)")
            # Create a readable dataframe
            df_matrix = pd.DataFrame(distance_matrix, index=valid_codes, columns=valid_codes).round(0)
            st.dataframe(df_matrix, use_container_width=True)
            
    else:
        st.warning("Please enter at least 3 valid IATA codes to optimize a route.")
