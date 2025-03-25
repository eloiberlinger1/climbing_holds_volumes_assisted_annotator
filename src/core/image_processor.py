import cv2
import numpy as np
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt
from roboflow import Roboflow
import supervision as sv
import sys
import os

# Ajouter le répertoire racine au PYTHONPATH pour pouvoir importer config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import (
    ROBOFLOW_API_KEY, ROBOFLOW_WORKSPACE, ROBOFLOW_PROJECT,
    ROBOFLOW_VERSION
)

class ImageProcessor:
    def __init__(self):
        self.model = None
        self.label_annotator = sv.LabelAnnotator()
        self.bounding_box_annotator = sv.BoxAnnotator()
        self.ai_assist_enabled = False
        self.confidence_threshold = 0.8  # Seuil de confiance par défaut à 80%
    
    def set_confidence_threshold(self, threshold: float):
        """Définit le seuil de confiance pour filtrer les prédictions."""
        self.confidence_threshold = threshold
    
    def enable_ai_assist(self):
        """Active l'assistance IA et initialise le modèle Roboflow."""
        if not self.ai_assist_enabled:
            try:
                print("Initialisation du modèle Roboflow...")
                rf = Roboflow(api_key=ROBOFLOW_API_KEY)
                self.model = rf.workspace(ROBOFLOW_WORKSPACE).project(ROBOFLOW_PROJECT).version(ROBOFLOW_VERSION).model
                self.ai_assist_enabled = True
                print("Modèle Roboflow initialisé avec succès")
            except Exception as e:
                print(f"Erreur lors de l'initialisation du modèle : {str(e)}")
                raise
    
    def disable_ai_assist(self):
        """Désactive l'assistance IA."""
        self.ai_assist_enabled = False
        self.model = None
    
    def load_image(self, image_path: str) -> np.ndarray:
        """Charge une image depuis un chemin."""
        return cv2.imread(image_path)
    
    def display_image(self, image: np.ndarray, label):
        """Affiche une image dans un QLabel."""
        height, width = image.shape[:2]
        bytes_per_line = 3 * width
        q_image = QImage(
            image.data.tobytes(), width, height,
            bytes_per_line, QImage.Format.Format_RGB888
        ).rgbSwapped()
        pixmap = QPixmap.fromImage(q_image)
        label.setPixmap(pixmap.scaled(
            label.size(), Qt.AspectRatioMode.KeepAspectRatio
        ))
    
    def run_detection(self, image_path: str) -> tuple:
        """Exécute la détection sur une image."""
        if not self.ai_assist_enabled or self.model is None:
            return None, None
        
        try:
            # Exécuter la prédiction via l'API Roboflow
            results = self.model.predict(image_path, confidence=40, overlap=30).json()
            
            # Convertir les résultats en format supervision
            boxes = []
            confidences = []
            class_ids = []
            labels = []
            
            for prediction in results['predictions']:
                confidence = prediction['confidence']
                # Ne garder que les prédictions au-dessus du seuil de confiance
                if confidence >= self.confidence_threshold:
                    x = prediction['x']
                    y = prediction['y']
                    width = prediction['width']
                    height = prediction['height']
                    class_name = prediction['class']
                    
                    # Convertir les coordonnées YOLO en format xyxy
                    x1 = x - width/2
                    y1 = y - height/2
                    x2 = x + width/2
                    y2 = y + height/2
                    
                    boxes.append([x1, y1, x2, y2])
                    confidences.append(confidence)
                    class_ids.append(0)  # On utilise 0 car nous n'avons qu'une seule classe
                    labels.append(f"{class_name} ({confidence:.1%})")
            
            if boxes:
                detections = sv.Detections(
                    xyxy=np.array(boxes),
                    confidence=np.array(confidences),
                    class_id=np.array(class_ids)
                )
            else:
                detections = None
            
            return detections, labels
            
        except Exception as e:
            print(f"Erreur lors de la détection : {str(e)}")
            return None, None
    
    def draw_annotations(self, image: np.ndarray, detections: sv.Detections, labels: list) -> np.ndarray:
        """Dessine les annotations sur l'image."""
        if detections is None or labels is None:
            return image
            
        # Dessiner les boîtes englobantes
        image = self.bounding_box_annotator.annotate(
            scene=image,
            detections=detections
        )
        
        # Dessiner les labels
        image = self.label_annotator.annotate(
            scene=image,
            detections=detections,
            labels=labels
        )
        
        return image 