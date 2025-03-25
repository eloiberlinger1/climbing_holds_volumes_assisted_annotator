import cv2
import numpy as np
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt
from ultralytics import YOLO
from roboflow import Roboflow
import sys
import os

# Ajouter le répertoire racine au PYTHONPATH pour pouvoir importer config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import ROBOFLOW_API_KEY

class ImageProcessor:
    def __init__(self):
        # Initialisation de Roboflow
        self.rf = Roboflow(api_key=ROBOFLOW_API_KEY)
        self.project = self.rf.workspace("chiang-mai-university-i0wly").project("neuralclimb")
        self.version = self.project.version(1)
        self.dataset = self.version.download("yolov12")
        
        # Initialisation du modèle YOLO
        self.model = YOLO('yolo12n.pt')
    
    def load_image(self, image_path: str) -> np.ndarray:
        """Charge une image depuis un chemin."""
        return cv2.imread(image_path)
    
    def display_image(self, image: np.ndarray, label):
        """Affiche une image dans un QLabel."""
        height, width = image.shape[:2]
        bytes_per_line = 3 * width
        q_image = QImage(
            image.data, width, height,
            bytes_per_line, QImage.Format.Format_RGB888
        ).rgbSwapped()
        pixmap = QPixmap.fromImage(q_image)
        label.setPixmap(pixmap.scaled(
            label.size(), Qt.AspectRatioMode.KeepAspectRatio
        ))
    
    def run_detection(self, image_path: str):
        """Exécute la détection YOLO sur une image."""
        return self.model(image_path)
    
    def draw_annotations(self, image: np.ndarray, annotations: list) -> np.ndarray:
        """Dessine les annotations sur l'image."""
        height, width = image.shape[:2]
        for class_id, x_center, y_center, box_width, box_height in annotations:
            # Conversion des coordonnées normalisées en pixels
            x1 = int((x_center - box_width/2) * width)
            y1 = int((y_center - box_height/2) * height)
            x2 = int((x_center + box_width/2) * width)
            y2 = int((y_center + box_height/2) * height)
            
            # Dessiner le rectangle
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Ajouter le label de la classe
            cv2.putText(image, f"Class {class_id}", (x1, y1-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return image 