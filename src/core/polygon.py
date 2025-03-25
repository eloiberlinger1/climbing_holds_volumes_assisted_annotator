import numpy as np
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Point:
    x: float
    y: float
    is_selected: bool = False

class Polygon:
    def __init__(self, name: str, class_type: str = "hold"):
        self.name = name
        self.class_type = class_type  # "hold" ou "volume"
        self.points: List[Point] = []
        self.selected_point_index = -1
    
    def add_point(self, x: float, y: float):
        """Ajoute un point au polygone."""
        self.points.append(Point(x, y))
    
    def move_point(self, index: int, x: float, y: float):
        """Déplace un point du polygone."""
        if 0 <= index < len(self.points):
            self.points[index].x = x
            self.points[index].y = y
    
    def select_point(self, index: int):
        """Sélectionne un point du polygone."""
        if 0 <= index < len(self.points):
            self.selected_point_index = index
            self.points[index].is_selected = True
    
    def deselect_point(self):
        """Désélectionne le point actuel."""
        if self.selected_point_index >= 0:
            self.points[self.selected_point_index].is_selected = False
            self.selected_point_index = -1
    
    def get_points_array(self) -> np.ndarray:
        """Retourne les points sous forme de tableau numpy."""
        return np.array([[p.x, p.y] for p in self.points])
    
    def is_point_inside(self, x: float, y: float, tolerance: float = 5.0) -> int:
        """Vérifie si un point est à l'intérieur du polygone ou près d'un point."""
        # Vérifier d'abord si le point est près d'un point du polygone
        for i, point in enumerate(self.points):
            if abs(point.x - x) < tolerance and abs(point.y - y) < tolerance:
                return i
        
        # Si non, vérifier si le point est à l'intérieur du polygone
        if len(self.points) < 3:
            return -1
            
        points = self.get_points_array()
        x_coords = points[:, 0]
        y_coords = points[:, 1]
        
        inside = False
        j = len(points) - 1
        
        for i in range(len(points)):
            if ((y_coords[i] > y) != (y_coords[j] > y) and
                (x < (x_coords[j] - x_coords[i]) * (y - y_coords[i]) /
                (y_coords[j] - y_coords[i]) + x_coords[i])):
                inside = not inside
            j = i
            
        return -1 if not inside else -2 