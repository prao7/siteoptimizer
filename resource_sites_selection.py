import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt
import contextily as ctx


# Set up shapefile path
reeds_shapefile_path = "/Users/prao/GitHub_Repos/siteoptimizer/input_files/US_PCA.shp"

# Function to calculate centroid paths
def centroid_paths():
    pass

# Function to filter out interested regions in shapefiles
def filter_shapefile(shapefile_path, region):
    # Read shapefile
    gdf = gpd.read_file(shapefile_path)
    # Filter out region
    gdf = gdf[gdf['STATE'].isin(region)]
    return gdf

# Function 