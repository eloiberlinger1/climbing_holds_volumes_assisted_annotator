import numpy as np
from dataclasses import dataclass
from typing import List, Tuple
import cv2

@dataclass
class Point:
    x: float
    y: float
    is_selected: bool = False

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
    
    def is_point_inside(self, x: float, y: float) -> int:
        """Vérifie si un point est à l'intérieur du polygone."""
        if len(self.points) < 3:
            return -1
            
        points = self.get_points_array()
        point = np.array([x, y])
        
        # Calculer la distance minimale à un point du polygone
        min_dist = float('inf')
        min_index = -1
        for i, p in enumerate(points):
            dist = np.linalg.norm(p - point)
            if dist < min_dist:
                min_dist = dist
                min_index = i
        
        # Si le point est proche d'un point du polygone, retourner son index
        if min_dist < 10:  # Distance de 10 pixels
            return min_index
            
        # Sinon, vérifier si le point est à l'intérieur du polygone
        if cv2.pointPolygonTest(points.astype(np.float32), (x, y), False) >= 0:
            return len(points)  # Index spécial pour indiquer que le point est à l'intérieur
        return -1 