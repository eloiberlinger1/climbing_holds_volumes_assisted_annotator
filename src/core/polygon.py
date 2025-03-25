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

    def draw(self, image):
        """Dessine le polygone sur l'image."""
        if len(self.points) < 3:
            return

        points = self.get_points_array()
        
        # Créer une copie de l'image pour le dessin
        result = image.copy()
        
        # Créer un masque binaire pour le polygone
        binary_mask = np.zeros((image.shape[0], image.shape[1]), dtype=np.uint8)
        cv2.fillPoly(binary_mask, [points.astype(np.int32)], 255)
        
        # Créer une image RGBA pour le remplissage
        color = (0, 255, 0) if self.class_type == "hold" else (255, 0, 0)
        alpha = 102 if self.is_selected else 51  # 0.4 * 255 = 102, 0.2 * 255 = 51
        
        # Créer un masque RGBA
        overlay = np.zeros((image.shape[0], image.shape[1], 4), dtype=np.uint8)
        overlay[binary_mask > 0] = (*color, alpha)
        
        # Fusionner l'overlay avec l'image
        alpha_channel = overlay[:, :, 3] / 255.0
        alpha_3d = np.stack([alpha_channel] * 3, axis=-1)
        
        # Appliquer la transparence
        result = result * (1 - alpha_3d) + overlay[:, :, :3] * alpha_3d
        result = result.astype(np.uint8)
        
        # Dessiner le contour du polygone
        contour_color = (0, 255, 255) if self.is_selected else color
        contour_thickness = 2 if self.is_selected else 1
        cv2.polylines(
            result,
            [points.astype(np.int32)],
            True,
            contour_color,
            contour_thickness
        )
        
        # Dessiner les points
        for i, point in enumerate(self.points):
            # Ajuster la taille et la couleur des points en fonction de la sélection
            point_color = (0, 0, 255) if point.is_selected else (255, 255, 0)
            point_size = 8 if point.is_selected else 6
            border_size = 10 if point.is_selected else 8
            
            # Dessiner un cercle plus grand pour la bordure
            cv2.circle(
                result,
                (int(point.x), int(point.y)),
                border_size,
                (0, 0, 0),
                1
            )
            # Dessiner le point
            cv2.circle(
                result,
                (int(point.x), int(point.y)),
                point_size,
                point_color,
                -1
            )
            
        # Copier le résultat dans l'image d'entrée
        image[:] = result[:] 