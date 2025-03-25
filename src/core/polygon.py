import numpy as np
from dataclasses import dataclass
from typing import List, Tuple
import cv2

@dataclass
class Point:
    x: float
    y: float
    is_selected: bool = False
    
    def is_near(self, x: float, y: float, threshold: float = 10) -> bool:
        """Vérifie si un point est proche des coordonnées données."""
        return abs(self.x - x) <= threshold and abs(self.y - y) <= threshold

class Polygon:
    def __init__(self, name: str, class_type: str):
        self.name = name
        self.class_type = class_type
        self.points = []
        self.selected_point_index = -1
        self.is_selected = False  # Pour la sélection du polygone entier
        self.drag_start = None  # Point de départ du déplacement
    
    def add_point(self, x: float, y: float):
        """Ajoute un point au polygone."""
        self.points.append(Point(x, y))
    
    def move_point(self, index: int, x: float, y: float):
        """Déplace un point du polygone."""
        if 0 <= index < len(self.points):
            self.points[index].x = x
            self.points[index].y = y
    
    def move_all_points(self, dx: float, dy: float):
        """Déplace tous les points du polygone."""
        for point in self.points:
            point.x += dx
            point.y += dy
    
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
        """Retourne les points du polygone sous forme de tableau numpy."""
        return np.array([[p.x, p.y] for p in self.points])
    
    def is_point_inside(self, x: float, y: float) -> bool:
        """Vérifie si un point est à l'intérieur du polygone."""
        if len(self.points) < 3:
            return False
            
        points = self.get_points_array()
        point = np.array([x, y])
        
        # Vérifier si le point est proche d'un des points du polygone
        for p in points:
            if np.linalg.norm(p - point) < 10:  # Distance de 10 pixels
                return True
        
        # Utiliser cv2.pointPolygonTest pour une détection précise
        contour = points.reshape((-1, 1, 2)).astype(np.float32)
        distance = cv2.pointPolygonTest(contour, (x, y), False)
        return distance >= 0
    
    def start_drag(self, x: float, y: float):
        """Commence le déplacement du polygone."""
        self.drag_start = (x, y)
    
    def update_drag(self, x: float, y: float):
        """Met à jour la position pendant le déplacement."""
        if self.drag_start is not None:
            dx = x - self.drag_start[0]
            dy = y - self.drag_start[1]
            self.move_all_points(dx, dy)
            self.drag_start = (x, y)
    
    def end_drag(self):
        """Termine le déplacement du polygone."""
        self.drag_start = None 