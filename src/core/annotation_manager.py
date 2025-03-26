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
                
                # Créer la ligne d'annotation
                line = f"{class_id}"
                for x, y in normalized_points:
                    line += f" {x:.6f} {y:.6f}"
                
                # Écrire la ligne dans le fichier
                f.write(line + "\n")
        
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
        
        with open(annotation_file, 'r') as f:
            for line in f:
                # Séparer la classe et les coordonnées
                values = line.strip().split()
                class_id = int(values[0])
                class_type = "hold" if class_id == 0 else "volume"
                
                # Extraire les coordonnées
                points = []
                for i in range(1, len(values), 2):
                    x = float(values[i])
                    y = float(values[i + 1])
                    # Dénormaliser les coordonnées
                    x = x * width
                    y = y * height
                    points.append((x, y))
                
                if points:
                    annotations.append((class_type, points))
        
        print(f"Annotations chargées pour {image_path}: {len(annotations)} polygones")
        return annotations 