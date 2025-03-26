import os
from typing import List, Dict, Tuple
import supervision as sv
from config import ANNOTATIONS_DIR
import json
import cv2

class AnnotationManager:
    def __init__(self):
        self.annotations: Dict[str, List[Tuple[int, float, float, float, float]]] = {}
        self.annotations_dir = "data/annotations/labels"
        os.makedirs(self.annotations_dir, exist_ok=True)
    
    def normalize_coordinates(self, points, image_width, image_height):
        """Normalise les coordonnées des points entre 0 et 1."""
        normalized_points = []
        for point in points:
            x = point.x / image_width
            y = point.y / image_height
            normalized_points.append((x, y))
        return normalized_points
    
    def save_annotations(self, image_path, annotations, labels):
        """Sauvegarde les annotations dans un fichier TXT au format YOLO."""
        # Créer le nom du fichier d'annotations
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        annotation_file = os.path.join(self.annotations_dir, f"{base_name}.txt")
        
        # Obtenir les dimensions de l'image
        image = cv2.imread(image_path)
        if image is None:
            print(f"Erreur : Impossible de lire l'image {image_path}")
            return
        height, width = image.shape[:2]
        
        # Sauvegarder les annotations
        with open(annotation_file, 'w') as f:
            for annotation in annotations:
                # Déterminer la classe (0 pour hold, 1 pour volume)
                class_id = 0 if annotation.class_type == "hold" else 1
                
                # Normaliser les coordonnées des points
                normalized_points = self.normalize_coordinates(annotation.points, width, height)
                
                # Écrire chaque point dans le fichier
                for x, y in normalized_points:
                    f.write(f"{class_id} {x:.6f} {y:.6f}\n")
        
        print(f"Annotations sauvegardées dans {annotation_file}")
    
    def load_annotations(self, image_path: str) -> List[Tuple[int, float, float]]:
        """Charge les annotations depuis le fichier TXT."""
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        annotation_file = os.path.join(self.annotations_dir, f"{base_name}.txt")
        
        if not os.path.exists(annotation_file):
            print(f"Aucune annotation trouvée pour {image_path}")
            return []
        
        # Obtenir les dimensions de l'image
        image = cv2.imread(image_path)
        if image is None:
            print(f"Erreur : Impossible de lire l'image {image_path}")
            return []
        height, width = image.shape[:2]
        
        annotations = []
        current_polygon = []
        current_class = None
        
        with open(annotation_file, 'r') as f:
            for line in f:
                class_id, x, y = map(float, line.strip().split())
                class_id = int(class_id)
                
                # Si on change de classe ou si c'est le premier point
                if current_class is None:
                    current_class = "hold" if class_id == 0 else "volume"
                    current_polygon = []
                elif (class_id == 0 and current_class != "hold") or (class_id == 1 and current_class != "volume"):
                    # Si on change de classe, sauvegarder le polygone actuel et en commencer un nouveau
                    if current_polygon:
                        annotations.append((current_class, current_polygon))
                    current_class = "hold" if class_id == 0 else "volume"
                    current_polygon = []
                
                # Dénormaliser les coordonnées
                x = x * width
                y = y * height
                
                current_polygon.append((x, y))
        
        # Ajouter le dernier polygone s'il existe
        if current_polygon:
            annotations.append((current_class, current_polygon))
        
        print(f"Annotations chargées pour {image_path}: {len(annotations)} polygones")
        return annotations 