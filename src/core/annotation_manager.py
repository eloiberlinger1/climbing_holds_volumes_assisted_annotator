import os
from typing import List, Dict, Tuple
import supervision as sv
from config import ANNOTATIONS_DIR
import json

class AnnotationManager:
    def __init__(self):
        self.annotations: Dict[str, List[Tuple[int, float, float, float, float]]] = {}
        self.annotations_dir = ANNOTATIONS_DIR
        # Format: {image_path: [(class_id, x_center, y_center, width, height), ...]}
    
    def add_annotation(self, image_path: str, class_id: int, 
                      x_center: float, y_center: float, 
                      width: float, height: float):
        if image_path not in self.annotations:
            self.annotations[image_path] = []
        self.annotations[image_path].append((class_id, x_center, y_center, width, height))
    
    def remove_annotation(self, image_path: str, index: int):
        if image_path in self.annotations and 0 <= index < len(self.annotations[image_path]):
            self.annotations[image_path].pop(index)
    
    def save_annotations(self, image_path, annotations, labels):
        """Sauvegarde les annotations dans un fichier JSON."""
        # Créer le dossier annotations s'il n'existe pas
        os.makedirs(self.annotations_dir, exist_ok=True)
        
        # Créer le nom du fichier d'annotations
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        annotation_file = os.path.join(self.annotations_dir, f"{base_name}.json")
        
        # Convertir les annotations en format JSON
        json_annotations = []
        for annotation in annotations:
            # Convertir les points en liste de coordonnées
            points = [[float(p.x), float(p.y)] for p in annotation.points]
            
            # Créer l'annotation au format JSON
            json_annotation = {
                "class": annotation.class_type,
                "points": points
            }
            json_annotations.append(json_annotation)
        
        # Créer le dictionnaire final
        data = {
            "image_path": image_path,
            "annotations": json_annotations,
            "labels": labels
        }
        
        # Sauvegarder dans le fichier JSON
        with open(annotation_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    def load_annotations(self, image_path: str) -> List[Tuple[int, float, float, float, float]]:
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        annotation_path = os.path.join(ANNOTATIONS_DIR, f"{base_name}.txt")
        
        if not os.path.exists(annotation_path):
            return []
        
        annotations = []
        with open(annotation_path, 'r') as f:
            for line in f:
                class_id, x_center, y_center, width, height = map(float, line.strip().split())
                annotations.append((int(class_id), x_center, y_center, width, height))
        
        self.annotations[image_path] = annotations
        return annotations 