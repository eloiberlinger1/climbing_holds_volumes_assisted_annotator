import os
from typing import List, Dict, Tuple

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
    
    def save_annotations(self, image_path: str):
        if image_path not in self.annotations:
            return
        
        # Créer le dossier annotations s'il n'existe pas
        os.makedirs("annotations", exist_ok=True)
        
        # Créer le nom du fichier d'annotation
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        annotation_path = os.path.join("annotations", f"{base_name}.txt")
        
        # Sauvegarder les annotations au format YOLO
        with open(annotation_path, 'w') as f:
            for class_id, x_center, y_center, width, height in self.annotations[image_path]:
                f.write(f"{class_id} {x_center} {y_center} {width} {height}\n")
    
    def load_annotations(self, image_path: str) -> List[Tuple[int, float, float, float, float]]:
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        annotation_path = os.path.join("annotations", f"{base_name}.txt")
        
        if not os.path.exists(annotation_path):
            return []
        
        annotations = []
        with open(annotation_path, 'r') as f:
            for line in f:
                class_id, x_center, y_center, width, height = map(float, line.strip().split())
                annotations.append((int(class_id), x_center, y_center, width, height))
        
        self.annotations[image_path] = annotations
        return annotations 