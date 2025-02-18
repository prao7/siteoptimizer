from models.region import Region
from models.transmission_path import TransmissionPath

class System:
    def __init__(self):
        """
        Initialize an empty System.
        """
        self.regions = {}
        self.transmission_paths = []

    def add_region(self, region: Region):
        """
        Add a region to the system.

        Parameters:
        - region (Region): The region to add.
        """
        if region.name in self.regions:
            raise ValueError(f"Region '{region.name}' already exists in the system.")
        self.regions[region.name] = region

    def add_transmission_path(self, region1_name: str, region2_name: str, capacity: float):
        """
        Add a transmission path between two regions.

        Parameters:
        - region1_name (str): The name of the first region.
        - region2_name (str): The name of the second region.
        - capacity (float): The capacity of the transmission path.
        """
        if region1_name not in self.regions or region2_name not in self.regions:
            raise ValueError("Both regions must be added to the system before creating a transmission path.")
        
        region1 = self.regions[region1_name]
        region2 = self.regions[region2_name]
        path = TransmissionPath(region1, region2, capacity)
        self.transmission_paths.append(path)

    def get_region(self, name: str) -> Region:
        """
        Retrieve a region by its name.

        Parameters:
        - name (str): The name of the region.

        Returns:
        - Region: The region with the specified name.
        """
        return self.regions.get(name)

    def __repr__(self):
        return (f"System with {len(self.regions)} regions and "
                f"{len(self.transmission_paths)} transmission paths.")
