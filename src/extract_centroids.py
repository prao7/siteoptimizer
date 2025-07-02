import geopandas as gpd
import pandas as pd
from shapely.geometry import Point


def calculate_centroids(shapefiles, output_path):
    """
    Calculate centroids of the given shapefiles and save them to a CSV file.

    Parameters:
    shapefiles (dict): A dictionary where keys are zone names and values are paths to shapefiles.
    output_path (str): The path where the output CSV will be saved.
    """
    # Load GeoDataFrames
    zones = {name: gpd.read_file(path) for name, path in shapefiles.items()}

    # Calculate centroids
    centroids = {name: zone.to_crs(epsg=3857).geometry.centroid for name, zone in zones.items()}

    # Compute distances
    zone_names = list(centroids.keys())
    distances = pd.DataFrame(index=zone_names, columns=zone_names)

    for name1, centroid1 in centroids.items():
        for name2, centroid2 in centroids.items():
            # Calculate distance in kilometers
            if name1 != name2:
                distances.loc[name1, name2] = centroid1.distance(centroid2).iloc[0] / 1000  # Convert meters to kilometers
    
    # Save the distances DataFrame to a CSV file
    distances.to_csv(output_path)


if __name__ == "__main__":
    # Load shapefiles into GeoDataFrames
    shapefiles = {"p48": '/Users/pradyrao/VSCode/extract_tx_final/SRP_TVA_data/texas_outputs_shapefiles/p48.shp',
                "p57": '/Users/pradyrao/VSCode/extract_tx_final/SRP_TVA_data/texas_outputs_shapefiles/p57.shp',
                "p60": '/Users/pradyrao/VSCode/extract_tx_final/SRP_TVA_data/texas_outputs_shapefiles/p60.shp',
                "p61": '/Users/pradyrao/VSCode/extract_tx_final/SRP_TVA_data/texas_outputs_shapefiles/p61.shp',
                "p62": '/Users/pradyrao/VSCode/extract_tx_final/SRP_TVA_data/texas_outputs_shapefiles/p62.shp',
                "p63": '/Users/pradyrao/VSCode/extract_tx_final/SRP_TVA_data/texas_outputs_shapefiles/p63.shp',
                "p64": '/Users/pradyrao/VSCode/extract_tx_final/SRP_TVA_data/texas_outputs_shapefiles/p64.shp',
                "p65": '/Users/pradyrao/VSCode/extract_tx_final/SRP_TVA_data/texas_outputs_shapefiles/p65.shp',
                "p66": '/Users/pradyrao/VSCode/extract_tx_final/SRP_TVA_data/texas_outputs_shapefiles/p66.shp',
                "p67": '/Users/pradyrao/VSCode/extract_tx_final/SRP_TVA_data/texas_outputs_shapefiles/p67.shp'
                }

    # Export distances to a CSV
    output_path = "centroids"

    calculate_centroids(shapefiles, output_path)
    

