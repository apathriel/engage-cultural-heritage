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
print(monuments_transformed)