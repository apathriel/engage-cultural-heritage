# Import required libraries
import os
import folium
from folium.elements import JavascriptLink
import geopandas as gpd
import pandas as pd

# Install required packages (if not already installed)
os.system("pip install geopandas folium")

# Load data
monuments = gpd.read_file("./data/anlaeg_all_25832.shp")
monuments_transformed = monuments.to_crs(epsg=4326)

test_rundhøj = monuments_transformed[monuments_transformed['anlaegsbet'] == 'Rundhøj']
print(test_rundhøj)

# Mapbox authentication
with open("src/mytoken.txt", 'r') as f:
    api_token = f.read()

# Create a Mapbox map
m = folium.Map(location=[56.2639, 10.2717], zoom_start=6.5, tiles='Stamen Terrain', attr='Map data © OpenStreetMap contributors')

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
zoom_out_button = """
    <button onclick="map.setZoom(7);" title="Zoom out" style="position:absolute;top:10px;left:10px;z-index:1000;">
        <i class="fa fa-globe" aria-hidden="true"></i> Zoom out
    </button>
"""
m.get_root().html.add_child(folium.Element(zoom_out_button))

# Add locate me button
locate_me_button = """
    <button onclick="map.locate({setView: true});" title="Locate Me" style="position:absolute;top:40px;left:10px;z-index:1000;">
        <i class="fa fa-crosshairs" aria-hidden="true"></i> Locate Me
    </button>
"""
m.get_root().html.add_child(folium.Element(locate_me_button))

m.save("index.html")