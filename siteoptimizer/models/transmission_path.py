from models.region import Region

class TransmissionPath:
    def __init__(self, region1: Region, region2: Region, current_capacity: float, cost_per_mile: float):
        self.region1 = region1
        self.region2 = region2
        self.capacity = current_capacity
        self.cost_per_mile = cost_per_mile

    def get_length(self) -> float:
        """
        Calculate and return the length of the transmission path between the two regions.

        Returns:
        - float: The length of the transmission path in meters.
        """
        centroid1 = self.region1.get_centroid()
        centroid2 = self.region2.get_centroid()

        return centroid1.distance(centroid2)
    
    def get_cost(self) -> float:
        """
        Calculate and return the cost of the transmission path between the two regions.

        Returns:
        - float: The cost of the transmission path in dollars.
        """
        return self.get_length() * self.cost_per_mile
    
    def get_capacity(self) -> float:
        """
        Get the capacity of the transmission path.

        Returns:
        - float: The capacity of the transmission path in MW.
        """
        return self.capacity
    
    def set_capacity(self, new_capacity: float):
        """
        Set the capacity of the transmission path.

        Parameters:
        - new_capacity (float): The new capacity of the transmission path in MW.
        """
        self.capacity = new_capacity
        

    def __repr__(self):
        return (f"TransmissionPath(region1={self.region1.name}, "
                f"region2={self.region2.name}, capacity={self.capacity})")
    