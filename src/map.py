# Import required libraries
import os
import folium
import geopandas as gpd
import pandas as pd

# Install required packages (if not already installed)
os.system("pip install geopandas folium")

# Load data
monuments = gpd.read_file("../data/anlaeg_all_25832.shp")
monuments_transformed = monuments.to_crs(epsg=4326)

test_rundhøj = monuments_transformed[monuments_transformed['anlaegsbet'] == 'Rundhøj']
print(test_rundhøj)

# Mapbox authentication
with open("mytoken.txt", 'r') as f:
    api_token = f.read()

# Create a Mapbox map
m = folium.Map(location=[56.2639, 10.2717], zoom_start=6.5, tiles='Stamen Terrain')

# Split data by group
data_split = [group for _, group in monuments_transformed.groupby('anlaegsbet')]

# Add markers and cluster for each group
for layer_data in data_split:
    group_name = layer_data['anlaegsbet'].iloc[0]
    feature_group = folium.FeatureGroup(name=group_name)
    m.add_child(feature_group)
    for index, row in layer_data.iterrows():
        folium.CircleMarker(location=[row['geometry'].y, row['geometry'].x],
                            radius=8,
                            color='red',
                            fill_opacity=0.8,
                            popup=row['anlaegsbet'],
                            tooltip=row['stednavn']).add_to(feature_group)

# Add layer control
folium.LayerControl().add_to(m)

# Add custom buttons
folium.Button(location="topleft", button_type="zoom-out", tooltip="Zoom out").add_to(m)
folium.Button(location="topleft", button_type="locate", tooltip="Locate Me").add_to(m)

# Display the map
m