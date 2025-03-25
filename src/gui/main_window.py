from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QGraphicsView,
    QSlider, QGroupBox, QComboBox, QLineEdit,
    QGraphicsScene, QGraphicsPixmapItem, QGraphicsItem
)
from PyQt6.QtCore import Qt, QPoint, QRectF, QPointF
from PyQt6.QtGui import (
    QKeySequence, QShortcut, QMouseEvent, QWheelEvent,
    QPixmap, QImage, QPainter
)
import os
from ..core.image_processor import ImageProcessor
from ..core.annotation_manager import AnnotationManager
from ..core.polygon import Polygon
import cv2
import numpy as np

class ImageViewer(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setMinimumSize(800, 600)
        
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        self.zoom_factor = 1.0
        self.image_item = None
        self.last_mouse_pos = None
        self.is_panning = False
    
    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            zoom_in_factor = 1.1
            zoom_out_factor = 1 / zoom_in_factor
            
            old_pos = self.mapToScene(event.position().toPoint())
            
            # Zoom
            if event.angleDelta().y() > 0:
                zoom_factor = zoom_in_factor
            else:
                zoom_factor = zoom_out_factor
            
            self.scale(zoom_factor, zoom_factor)
            
            # Get the new position
            new_pos = self.mapToScene(event.position().toPoint())
            
            # Move scene to old position
            delta = new_pos - old_pos
            self.translate(delta.x(), delta.y())
            
            event.accept()
        else:
            super().wheelEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.is_panning = True
            self.last_mouse_pos = event.pos()
            event.accept()
        else:
            scene_pos = self.mapToScene(event.pos())
            if isinstance(self.parent(), MainWindow):
                self.parent().handle_mouse_click(scene_pos)
            super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.is_panning = False
            event.accept()
        else:
            scene_pos = self.mapToScene(event.pos())
            if isinstance(self.parent(), MainWindow):
                self.parent().handle_mouse_release(scene_pos)
            super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.is_panning and self.last_mouse_pos:
            delta = event.pos() - self.last_mouse_pos
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            self.last_mouse_pos = event.pos()
            event.accept()
        else:
            scene_pos = self.mapToScene(event.pos())
            if isinstance(self.parent(), MainWindow):
                self.parent().handle_mouse_move(scene_pos)
            super().mouseMoveEvent(event)
    
    def set_image(self, image):
        self.scene.clear()
        if image is not None:
            height, width, channel = image.shape
            bytes_per_line = 3 * width
            q_image = QImage(image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            self.image_item = self.scene.addPixmap(pixmap)
            self.setSceneRect(QRectF(pixmap.rect()))
            self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Annotateur de prises d'escalade")
        self.setMinimumSize(1200, 800)
        
        # Initialisation des composants
        self.image_processor = ImageProcessor()
        self.annotation_manager = AnnotationManager()
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Groupe pour les contrôles de navigation
        navigation_group = QGroupBox("Navigation")
        navigation_layout = QHBoxLayout()
        
        # Boutons de navigation
        self.prev_button = QPushButton("Précédente (p)")
        self.next_button = QPushButton("Suivante (n)")
        self.save_button = QPushButton("Sauvegarder (s)")
        
        # Ajout des boutons au layout de navigation
        navigation_layout.addWidget(self.prev_button)
        navigation_layout.addWidget(self.next_button)
        navigation_layout.addWidget(self.save_button)
        navigation_group.setLayout(navigation_layout)
        
        # Groupe pour les contrôles d'assistance IA
        ai_group = QGroupBox("Assistance IA")
        ai_layout = QVBoxLayout()
        
        # Bouton d'assistance IA
        self.ai_assist_button = QPushButton("Activer l'assistance IA")
        self.ai_assist_button.setCheckable(True)
        
        # Contrôle du seuil de confiance
        confidence_layout = QHBoxLayout()
        confidence_label = QLabel("Seuil de confiance:")
        self.confidence_slider = QSlider(Qt.Orientation.Horizontal)
        self.confidence_slider.setMinimum(0)
        self.confidence_slider.setMaximum(100)
        self.confidence_slider.setValue(80)
        self.confidence_value_label = QLabel("80%")
        confidence_layout.addWidget(confidence_label)
        confidence_layout.addWidget(self.confidence_slider)
        confidence_layout.addWidget(self.confidence_value_label)
        
        # Ajout des contrôles IA au layout
        ai_layout.addWidget(self.ai_assist_button)
        ai_layout.addLayout(confidence_layout)
        ai_group.setLayout(ai_layout)
        
        # Groupe pour les contrôles d'annotation
        annotation_group = QGroupBox("Annotation")
        annotation_layout = QHBoxLayout()
        
        # Contrôles pour l'ajout de polygones
        self.polygon_class = QComboBox()
        self.polygon_class.addItems(["hold", "volume"])
        self.add_polygon_button = QPushButton("Ajouter polygone (p)")
        self.delete_polygon_button = QPushButton("Supprimer (d)")
        
        annotation_layout.addWidget(QLabel("Type:"))
        annotation_layout.addWidget(self.polygon_class)
        annotation_layout.addWidget(self.add_polygon_button)
        annotation_layout.addWidget(self.delete_polygon_button)
        annotation_group.setLayout(annotation_layout)
        
        # Layout horizontal pour les contrôles
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(navigation_group)
        controls_layout.addWidget(ai_group)
        controls_layout.addWidget(annotation_group)
        
        # Ajout des contrôles au layout principal
        main_layout.addLayout(controls_layout)
        
        # Zone d'affichage de l'image
        self.image_viewer = ImageViewer(self)
        main_layout.addWidget(self.image_viewer)
        
        # Connexion des signaux
        self.prev_button.clicked.connect(self.show_previous_image)
        self.next_button.clicked.connect(self.show_next_image)
        self.save_button.clicked.connect(self.save_annotations)
        self.ai_assist_button.clicked.connect(self.toggle_ai_assist)
        self.confidence_slider.valueChanged.connect(self.update_confidence_threshold)
        self.add_polygon_button.clicked.connect(self.start_new_polygon)
        self.delete_polygon_button.clicked.connect(self.enable_polygon_deletion)
        
        # Ajout des raccourcis clavier
        QShortcut(QKeySequence("p"), self).activated.connect(self.start_new_polygon)
        QShortcut(QKeySequence("d"), self).activated.connect(self.enable_polygon_deletion)
        QShortcut(QKeySequence("="), self).activated.connect(self.add_point_to_polygon)
        
        # État initial
        self.current_image_index = -1
        self.image_files = []
        self.current_image_path = None
        self.current_annotations = []
        self.current_polygon = None
        self.is_deleting = False
        self.original_image = None
        self.display_image = None
        
        # Charger les images
        self.load_images()
    
    def start_new_polygon(self):
        """Démarre la création d'un nouveau polygone."""
        if self.original_image is None:
            return
            
        class_type = self.polygon_class.currentText()
        polygon_count = sum(1 for p in self.current_annotations if p.class_type == class_type)
        name = f"{class_type}_{polygon_count + 1}"
        
        # Créer un nouveau polygone
        self.current_polygon = Polygon(name, class_type)
        
        # Calculer les dimensions de l'image
        height, width = self.original_image.shape[:2]
        center_x = width / 2
        center_y = height / 2
        size = min(width, height) / 4  # Taille du carré (1/4 de la plus petite dimension)
        
        # Ajouter les points du carré
        self.current_polygon.add_point(center_x - size, center_y - size)  # Haut gauche
        self.current_polygon.add_point(center_x + size, center_y - size)  # Haut droite
        self.current_polygon.add_point(center_x + size, center_y + size)  # Bas droite
        self.current_polygon.add_point(center_x - size, center_y + size)  # Bas gauche
        
        # Ajouter directement le polygone aux annotations
        self.current_annotations.append(self.current_polygon)
        print(f"Création d'un nouveau polygone : {name} ({class_type})")
        
        # Mettre à jour l'affichage
        self.update_image_display()
    
    def enable_polygon_deletion(self):
        """Active le mode suppression de polygone."""
        self.is_deleting = not self.is_deleting
        print(f"Mode suppression {'activé' if self.is_deleting else 'désactivé'}")
    
    def add_point_to_polygon(self):
        """Ajoute un point au polygone courant."""
        if self.current_polygon is None:
            return
        
        # Convertir les coordonnées de la scène en coordonnées de l'image
        pos = self.image_viewer.mapToScene(self.cursor().pos())
        x = pos.x()
        y = pos.y()
        
        self.current_polygon.add_point(x, y)
        print(f"Point ajouté au polygone {self.current_polygon.name} : ({x}, {y})")
        self.update_image_display()
    
    def handle_mouse_click(self, pos: QPointF):
        """Gère le clic de souris sur l'image."""
        if self.original_image is None:
            return
            
        # Convertir les coordonnées de la scène en coordonnées de l'image
        x = pos.x()
        y = pos.y()
        
        if self.is_deleting:
            # Chercher un polygone à supprimer
            for i, polygon in enumerate(self.current_annotations):
                if polygon.is_point_inside(x, y) >= 0:
                    print(f"Suppression du polygone {polygon.name}")
                    del self.current_annotations[i]
                    self.update_image_display()
                    return
        
        # Désélectionner tous les polygones
        for polygon in self.current_annotations:
            polygon.is_selected = False
            polygon.selected_point_index = -1
            for point in polygon.points:
                point.is_selected = False
        
        # Vérifier si on clique sur un point existant ou à l'intérieur d'un polygone
        for polygon in self.current_annotations:
            point_index = polygon.is_point_inside(x, y)
            if point_index >= 0:
                if point_index < len(polygon.points):
                    # Clic sur un point
                    polygon.selected_point_index = point_index
                    polygon.points[point_index].is_selected = True
                else:
                    # Clic à l'intérieur du polygone
                    polygon.is_selected = True
                    polygon.drag_start = (x, y)
                self.current_polygon = polygon
                self.update_image_display()
                return
    
    def handle_mouse_move(self, pos: QPointF):
        """Gère le déplacement de souris sur l'image."""
        if self.current_polygon is None:
            return
            
        x = pos.x()
        y = pos.y()
        
        if self.current_polygon.selected_point_index >= 0:
            # Déplacer un point
            self.current_polygon.move_point(self.current_polygon.selected_point_index, x, y)
        elif self.current_polygon.is_selected and self.current_polygon.drag_start is not None:
            # Déplacer le polygone entier
            dx = x - self.current_polygon.drag_start[0]
            dy = y - self.current_polygon.drag_start[1]
            self.current_polygon.move_all_points(dx, dy)
            self.current_polygon.drag_start = (x, y)
        
        self.update_image_display()
    
    def update_image_display(self):
        """Met à jour l'affichage de l'image avec les annotations."""
        if self.original_image is None:
            return
        
        # Créer une copie de l'image originale
        self.display_image = self.original_image.copy()
        
        # Dessiner les polygones
        for polygon in self.current_annotations:
            points = polygon.get_points_array()
            if len(points) >= 3:
                # Créer un masque pour le remplissage semi-transparent
                mask = np.zeros_like(self.display_image)
                color = (0, 255, 0) if polygon.class_type == "hold" else (255, 0, 0)
                cv2.fillPoly(mask, [points.astype(np.int32)], color)
                
                # Appliquer le masque avec transparence
                self.display_image = cv2.addWeighted(
                    self.display_image, 1,
                    mask, 0.3,  # 30% d'opacité
                    0
                )
                
                # Dessiner le contour du polygone
                cv2.polylines(
                    self.display_image,
                    [points.astype(np.int32)],
                    True,
                    color,
                    2
                )
                
                # Dessiner les points
                for i, point in enumerate(polygon.points):
                    color = (0, 0, 255) if point.is_selected else (255, 255, 0)
                    cv2.circle(
                        self.display_image,
                        (int(point.x), int(point.y)),
                        5,
                        color,
                        -1
                    )
        
        # Convertir l'image en RGB pour Qt
        self.display_image = cv2.cvtColor(self.display_image, cv2.COLOR_BGR2RGB)
        
        # Mettre à jour l'affichage
        self.image_viewer.set_image(self.display_image)
    
    def update_confidence_threshold(self, value):
        """Met à jour le seuil de confiance et l'affiche."""
        threshold = value / 100.0
        self.image_processor.set_confidence_threshold(threshold)
        self.confidence_value_label.setText(f"{value}%")
        if self.current_image_path and self.ai_assist_button.isChecked():
            self.show_current_image()
    
    def load_images(self):
        """Charge les images du dossier data/to_annotate."""
        images_dir = "data/to_annotate"
        if os.path.exists(images_dir):
            self.image_files = [
                os.path.join(images_dir, f) for f in os.listdir(images_dir)
                if f.lower().endswith(('.png', '.jpg', '.jpeg'))
            ]
            if self.image_files:
                self.current_image_index = 0
                self.show_current_image()
            else:
                QMessageBox.warning(
                    self, "Attention",
                    "Aucune image trouvée dans le dossier data/to_annotate"
                )
        else:
            QMessageBox.warning(
                self, "Erreur",
                "Le dossier data/to_annotate n'existe pas"
            )
    
    def show_current_image(self):
        """Affiche l'image courante avec les annotations."""
        if 0 <= self.current_image_index < len(self.image_files):
            print(f"Affichage de l'image {self.current_image_index + 1}/{len(self.image_files)}")
            self.current_image_path = self.image_files[self.current_image_index]
            print(f"Chemin de l'image : {self.current_image_path}")
            
            self.original_image = self.image_processor.load_image(self.current_image_path)
            if self.original_image is None:
                print(f"Erreur : Impossible de charger l'image {self.current_image_path}")
                return
                
            print(f"Image chargée avec succès : {self.original_image.shape}")
            
            # Exécuter la détection si l'assistance IA est activée
            if self.ai_assist_button.isChecked():
                print("Détection IA en cours...")
                detections, labels = self.image_processor.run_detection(
                    self.current_image_path
                )
                if detections is not None:
                    print(f"Détection réussie : {len(labels)} objets trouvés")
                    self.original_image = self.image_processor.draw_annotations(
                        self.original_image, detections, labels
                    )
                else:
                    print("Aucune détection trouvée")
            
            self.update_image_display()
            print("Image affichée avec succès")
        else:
            print(f"Index d'image invalide : {self.current_image_index} (total: {len(self.image_files)})")
    
    def show_next_image(self):
        """Affiche l'image suivante."""
        if self.current_image_index < len(self.image_files) - 1:
            self.current_image_index += 1
            self.show_current_image()
    
    def show_previous_image(self):
        """Affiche l'image précédente."""
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.show_current_image()
    
    def save_annotations(self):
        """Sauvegarde les annotations courantes."""
        if self.current_image_path:
            self.annotation_manager.save_annotations(
                self.current_image_path,
                self.current_annotations
            )
            QMessageBox.information(
                self, "Succès",
                "Les annotations ont été sauvegardées"
            )
    
    def toggle_ai_assist(self):
        """Active ou désactive l'assistance IA."""
        if self.ai_assist_button.isChecked():
            try:
                self.image_processor.enable_ai_assist()
                self.show_current_image()  # Rafraîchir l'affichage
            except Exception as e:
                QMessageBox.critical(
                    self, "Erreur",
                    f"Erreur lors de l'activation de l'assistance IA : {str(e)}"
                )
                self.ai_assist_button.setChecked(False)
        else:
            self.image_processor.disable_ai_assist()
            self.show_current_image()  # Rafraîchir l'affichage
    
    def handle_mouse_release(self, pos: QPointF):
        """Gère le relâchement de souris."""
        if self.current_polygon is not None:
            self.current_polygon.drag_start = None
            self.update_image_display() 