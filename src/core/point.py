class Point:
    """Classe représentant un point 2D."""
    
    def __init__(self, x: float, y: float):
        """
        Initialise un point avec ses coordonnées x et y.
        
        Args:
            x (float): Coordonnée x du point
            y (float): Coordonnée y du point
        """
        self.x = float(x)
        self.y = float(y)
    
    def __str__(self) -> str:
        """Retourne une représentation textuelle du point."""
        return f"Point({self.x}, {self.y})"
    
    def __repr__(self) -> str:
        """Retourne une représentation textuelle du point pour le débogage."""
        return self.__str__() 