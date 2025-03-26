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
        self.confidence_threshold = 0.4  # Seuil de confiance par défaut à 40%
    
    def set_confidence_threshold(self, threshold: float):
        """Définit le seuil de confiance pour filtrer les prédictions."""
        self.confidence_threshold = threshold
    
    def enable_ai_assist(self):
        """Active l'assistance IA et initialise le modèle Roboflow."""
        if not self.ai_assist_enabled:
            try:
                print("Initialisation du modèle Roboflow...")
                print(f"API Key : {ROBOFLOW_API_KEY[:5]}...")
                print(f"Workspace : {ROBOFLOW_WORKSPACE}")
                print(f"Project : {ROBOFLOW_PROJECT}")
                print(f"Version : {ROBOFLOW_VERSION}")
                
                rf = Roboflow(api_key=ROBOFLOW_API_KEY)
                print("Roboflow initialisé")
                
                workspace = rf.workspace(ROBOFLOW_WORKSPACE)
                print("Workspace chargé")
                
                project = workspace.project(ROBOFLOW_PROJECT)
                print("Projet chargé")
                
                self.model = project.version(ROBOFLOW_VERSION).model
                print("Modèle chargé")
                
                self.ai_assist_enabled = True
                print("Modèle Roboflow initialisé avec succès")
            except Exception as e:
                print(f"Erreur lors de l'initialisation du modèle : {str(e)}")
                print(f"Type de l'erreur : {type(e)}")
                import traceback
                print(f"Traceback complet :\n{traceback.format_exc()}")
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
            print("Exécution de la prédiction via l'API Roboflow...")
            result = self.model.predict(image_path, confidence=40, overlap=30)
            print(f"Résultat brut : {result}")
            
            if result is None:
                raise Exception("La prédiction a retourné None")
                
            if isinstance(result, dict):
                results = result
            else:
                results = result.json()
                
            print(f"Résultats de la prédiction : {results}")
            
            # Convertir les résultats en format supervision
            boxes = []
            confidences = []
            class_ids = []
            labels = []
            
            # Obtenir les dimensions de l'image
            image = cv2.imread(image_path)
            image_height, image_width = image.shape[:2]
            print(f"Dimensions de l'image : {image_width}x{image_height}")
            
            for prediction in results['predictions']:
                confidence = prediction['confidence']
                if confidence >= self.confidence_threshold:
                    # Calculer la boîte englobante
                    x = float(prediction['x'])
                    y = float(prediction['y'])
                    width = float(prediction['width'])
                    height = float(prediction['height'])
                    
                    # Calculer les coordonnées des coins
                    x1 = max(0, x - width/2)
                    y1 = max(0, y - height/2)
                    x2 = min(image_width, x + width/2)
                    y2 = min(image_height, y + height/2)
                    
                    print(f"Boîte englobante : x={x}, y={y}, w={width}, h={height}")
                    print(f"Coins : ({x1}, {y1}), ({x2}, {y2})")
                    
                    boxes.append([x1, y1, x2, y2])
                    confidences.append(confidence)
                    class_ids.append(0)  # 0 pour "hold"
                    labels.append(f"Hold ({confidence*100:.1f}%)")
            
            if not boxes:
                print("Aucune détection ne dépasse le seuil de confiance")
                return None, None
                
            # Créer l'objet Detections
            boxes = np.array(boxes, dtype=np.float32)
            confidences = np.array(confidences, dtype=np.float32)
            class_ids = np.array(class_ids, dtype=np.int32)
            
            print(f"Boxes shape: {boxes.shape}")
            print(f"Confidences shape: {confidences.shape}")
            print(f"Class IDs shape: {class_ids.shape}")
            
            detections = sv.Detections(
                xyxy=boxes,
                confidence=confidences,
                class_id=class_ids
            )
            
            print(f"Nombre de détections trouvées : {len(detections)}")
            return detections, labels
            
        except Exception as e:
            print(f"Erreur lors de la détection : {str(e)}")
            print(f"Type de l'erreur : {type(e)}")
            import traceback
            print(f"Traceback complet :\n{traceback.format_exc()}")
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