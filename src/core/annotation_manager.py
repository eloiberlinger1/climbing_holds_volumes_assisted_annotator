import os
from typing import List, Dict, Tuple
import supervision as sv
from config import ANNOTATIONS_DIR

class AnnotationManager:
    def __init__(self):
        self.annotations: Dict[str, List[Tuple[int, float, float, float, float]]] = {}
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
    
    def save_annotations(self, image_path: str, detections: sv.Detections, labels: list):
        """Sauvegarde les annotations au format YOLO."""
        if detections is None or labels is None:
            return
        
        # Créer le dossier annotations s'il n'existe pas
        os.makedirs(ANNOTATIONS_DIR, exist_ok=True)
        
        # Créer le nom du fichier d'annotation
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        annotation_path = os.path.join(ANNOTATIONS_DIR, f"{base_name}.txt")
        
        # Convertir les détections au format YOLO
        height, width = detections.xyxy.shape[0], detections.xyxy.shape[1]
        with open(annotation_path, 'w') as f:
            for i, (box, label) in enumerate(zip(detections.xyxy, labels)):
                # Convertir les coordonnées en format YOLO (normalisé)
                x1, y1, x2, y2 = box
                x_center = (x1 + x2) / (2 * width)
                y_center = (y1 + y2) / (2 * height)
                box_width = (x2 - x1) / width
                box_height = (y2 - y1) / height
                
                # TODO: Convertir le label en ID de classe
                class_id = 0  # À adapter selon votre mapping de classes
                
                f.write(f"{class_id} {x_center} {y_center} {box_width} {box_height}\n")
    
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