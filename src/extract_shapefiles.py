import numpy as np
import pandas as pd
import os
import geopandas as gpd

def read_shapefile(file_path):
    """
    Read a shapefile and return a GeoDataFrame.

    Parameters:
    file_path (str): The path to the shapefile.

    Returns:
    gpd.GeoDataFrame: A GeoDataFrame containing the shapefile data.
    """
    return gpd.read_file(file_path)

def write_shapefile(gdf, file_path):
    """
    Write a GeoDataFrame to a shapefile.

    Parameters:
    gdf (gpd.GeoDataFrame): The GeoDataFrame to write.
    file_path (str): The path to write the shapefile.
    """
    gdf.to_file(file_path)

def get_shapefile_columns(gdf):
    """
    Get the columns of a GeoDataFrame.

    Parameters:
    gdf (gpd.GeoDataFrame): The GeoDataFrame to get the columns from.

    Returns:
    list: A list of column names in the GeoDataFrame.
    """
    return gdf.columns.tolist()

def print_first_rows(gdf, num_rows=5):
    """
    Print the first few rows of a GeoDataFrame.

    Parameters:
    gdf (gpd.GeoDataFrame): The GeoDataFrame to print.
    num_rows (int): The number of rows to print. Default is 5.
    """
    print(gdf.head(num_rows))

# def get_shapefile_centroid(file_path):
#     """
#     Get the centroid of a shapefile.

#     Parameters:
#     file_path (str): The path to the shapefile.

#     Returns:
#     tuple: A tuple containing the x and y coordinates of the centroid.
#     """
#     gdf = gpd.read_file(file_path)
#     centroid = gdf.geometry.centroid
#     return (centroid.x[0], centroid.y[0])

def get_shapefile_centroid(shapefile_path):
    """
    Computes the centroid of a shapefile and returns the longitude and latitude in WGS84.
    
    Parameters:
        shapefile_path (str): Path to the input shapefile.

    Returns:
        tuple: (longitude, latitude) of the centroid in WGS84.
    """
    # Load the shapefile
    gdf = gpd.read_file(shapefile_path)
    
    # Check if the CRS is defined
    if gdf.crs is None:
        raise ValueError("The input shapefile does not have a defined CRS.")
    
    # Store original CRS
    original_crs = gdf.crs
    
    # If the CRS is geographic (lat/lon), temporarily project to a suitable projected CRS
    if gdf.crs.to_epsg() == 4326:
        projected_crs = "EPSG:3857"  # Web Mercator, good for global calculations
        gdf = gdf.to_crs(projected_crs)
    
    # Compute the centroid in the projected CRS
    centroid = gdf.geometry.centroid.unary_union
    
    # Convert centroid back to WGS84 (EPSG:4326) for proper longitude/latitude
    centroid_gdf = gpd.GeoDataFrame(geometry=[centroid], crs=gdf.crs)
    centroid_gdf = centroid_gdf.to_crs("EPSG:4326")
    
    # Extract the correct longitude and latitude
    centroid_lon, centroid_lat = centroid_gdf.geometry.x[0], centroid_gdf.geometry.y[0]

    return centroid_lon, centroid_lat

def filter_and_save_regions(shapefile_path, output_directory, regions_to_filter, region_column):
    """
    Filters out specific regions from a shapefile and saves them as individual shapefiles.
    
    Parameters:
        shapefile_path (str): Path to the input shapefile.
        output_directory (str): Directory where individual shapefiles will be saved.
        regions_to_filter (list): List of region identifiers to filter.
        region_column (str): Name of the column containing region identifiers.
    """
    # Load the shapefile
    gdf = gpd.read_file(shapefile_path)

    # Ensure the output directory exists
    os.makedirs(output_directory, exist_ok=True)

    # Filter and save each region separately
    for region in regions_to_filter:
        region_gdf = gdf[gdf[region_column].astype(str) == region]

        if not region_gdf.empty:
            output_path = os.path.join(output_directory, f"{region}.shp")
            region_gdf.to_file(output_path)
            print(f"Saved: {output_path}")
        else:
            print(f"Region {region} not found in the dataset.")


if __name__ == "__main__":
    # Path to the shapefile
    shapefile_path = "shapefiles/US_PCA.shp"

    # Read the shapefile
    gdf = read_shapefile(shapefile_path)

    # Get the columns of the GeoDataFrame
    columns = get_shapefile_columns(gdf)

    # Print the columns
    print(columns)

    # Print the first few rows of the GeoDataFrame
    print_first_rows(gdf)

    # Filter and save specific regions
    regions_to_filter = ["p48", "p57", "p60", "p61", "p62", "p63", "p64", "p65", "p66", "p67"]
    output_directory = "output_shapefiles"

    filter_and_save_regions(shapefile_path, output_directory, regions_to_filter, "rb")