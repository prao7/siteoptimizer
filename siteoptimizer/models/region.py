import geopandas as gpd
from shapely.geometry import Point

class Region:
    def __init__(self, name: str, load: float, shapefile_filepath: str):
        """
        Initialize a Region.

        Parameters:
        - name (str): The name of the region.
        - shapefile_filepath (str): The file path to the region's shapefile.
        """
        self.name = name
        self.load = load
        try:
            self.shapefile = gpd.read_file(shapefile_filepath)
        except Exception as e:
            raise ValueError(f"Unable to read the shapefile at {shapefile_filepath}: {e}")

    def get_centroid(self) -> Point:
        """
        Calculate and return the centroid of the region's shapefile.

        Returns:
        - Point: The centroid of the region as a Shapely Point object.
        """
        if self.shapefile.empty:
            raise ValueError("Shapefile is empty. Cannot compute centroid.")
        
        # Ensure the shapefile is in a projected coordinate system
        if self.shapefile.crs.is_geographic:
            self.shapefile = self.shapefile.to_crs(epsg=3395)  # World Mercator projection

        # Calculate the centroid of the combined geometry
        combined_geometry = self.shapefile.unary_union
        centroid = combined_geometry.centroid

        return centroid
    
    def get_area(self) -> float:
        """
        Calculate and return the area of the region's shapefile.

        Returns:
        - float: The area of the region in square meters.
        """
        if self.shapefile.empty:
            raise ValueError("Shapefile is empty. Cannot compute area.")
        
        # Ensure the shapefile is in a projected coordinate system
        if self.shapefile.crs.is_geographic:
            self.shapefile = self.shapefile.to_crs(epsg=3395)
        
        # Calculate the area of the combined geometry
        combined_geometry = self.shapefile.unary_union
        area = combined_geometry.area

        return area
    
    def get_load(self) -> float:
        """
        Get the load of the region.

        Returns:
        - float: The load of the region in MW.
        """
        return self.load
    
    def set_load(self, load: float):
        """
        Set the load of the region.

        Parameters:
        - load (float): The new load of the region in MW.
        """
        self.load = load
    
    def set_name(self, name: str):
        """
        Set the name of the region.

        Parameters:
        - name (str): The new name of the region.
        """
        self.name = name
    
    def set_shapefile(self, shapefile_filepath: str):
        """
        Set the shapefile of the region.

        Parameters:
        - shapefile_filepath (str): The new file path to the region's shapefile.
        """
        try:
            self.shapefile = gpd.read_file(shapefile_filepath)
        except Exception as e:
            raise ValueError(f"Unable to read the shapefile at {shapefile_filepath}: {e}")

    def __repr__(self):
        return f"Region(name={self.name}, shapefile=GeoDataFrame with {len(self.shapefile)} features)"
