from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox,
    QSlider, QGroupBox, QComboBox, QLineEdit,
    QGraphicsScene, QGraphicsPixmapItem, QGraphicsItem
)
from PyQt6.QtCore import Qt, QPoint, QRectF, QPointF
from PyQt6.QtGui import (
    QKeySequence, QShortcut, QMouseEvent, QWheelEvent,
    QPixmap, QImage, QPainter, QTransform
)
import os
from ..core.image_processor import ImageProcessor
from ..core.annotation_manager import AnnotationManager
from ..core.polygon import Polygon, Point
from .image_viewer import ImageViewer
import cv2
import numpy as np

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
        self.finish_button = QPushButton("Terminer l'annotation")
        
        # Ajout des boutons au layout de navigation
        navigation_layout.addWidget(self.prev_button)
        navigation_layout.addWidget(self.next_button)
        navigation_layout.addWidget(self.save_button)
        navigation_layout.addWidget(self.finish_button)
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
        annotation_layout = QVBoxLayout()
        
        # Ajouter un label pour la prévisualisation
        self.preview_label = QLabel()
        self.preview_label.setMinimumSize(200, 200)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("border: 1px solid gray;")
        annotation_layout.addWidget(self.preview_label)
        
        # Sélection du type de polygone
        self.polygon_class = QComboBox()
        self.polygon_class.addItems(["hold", "volume"])
        annotation_layout.addWidget(self.polygon_class)
        
        # Boutons d'annotation
        self.new_polygon_button = QPushButton("Nouveau polygone (:)")
        self.delete_polygon_button = QPushButton("Supprimer (d)")
        self.delete_polygon_button.setEnabled(False)
        annotation_layout.addWidget(self.new_polygon_button)
        annotation_layout.addWidget(self.delete_polygon_button)
        
        # Ajouter un label pour la touche =
        help_label = QLabel("Appuyez sur = pour ajouter des points au milieu de chaque ligne du polygone sélectionné")
        help_label.setWordWrap(True)
        annotation_layout.addWidget(help_label)
        
        annotation_group.setLayout(annotation_layout)
        
        # Layout pour les contrôles
        controls_layout = QVBoxLayout()
        controls_layout.addWidget(navigation_group)
        controls_layout.addWidget(ai_group)
        controls_layout.addWidget(annotation_group)
        controls_layout.addStretch()
        
        # Layout horizontal principal
        h_layout = QHBoxLayout()
        
        # Viewer d'image
        self.image_viewer = ImageViewer()
        h_layout.addWidget(self.image_viewer, stretch=1)
        
        # Ajouter les contrôles
        controls_widget = QWidget()
        controls_widget.setLayout(controls_layout)
        controls_widget.setFixedWidth(300)
        h_layout.addWidget(controls_widget)
        
        main_layout.addLayout(h_layout)
        
        # Variables d'état
        self.image_files = []
        self.current_image_index = -1
        self.original_image = None
        self.display_image = None
        self.current_annotations = []
        self.current_polygon = None
        self.selected_point = None
        self.selected_polygon = None
        self.is_dragging = False
        self.current_zoom = 1.0
        self.image_item = None
        self.scene = QGraphicsScene()
        self.labels = ["hold", "volume"]  # Ajout des labels disponibles
        
        # Connecter les signaux
        self.setup_connections()
        
        # Charger les images
        self.load_images()
        
        # Créer les dossiers nécessaires
        os.makedirs("data/annotations/images", exist_ok=True)
        os.makedirs("data/annotations/labels", exist_ok=True)
    
    def setup_connections(self):
        # Connexion des signaux
        self.prev_button.clicked.connect(self.show_previous_image)
        self.next_button.clicked.connect(self.show_next_image)
        self.save_button.clicked.connect(self.save_annotations)
        self.finish_button.clicked.connect(self.finish_annotation)
        self.ai_assist_button.clicked.connect(self.toggle_ai_assist)
        self.confidence_slider.valueChanged.connect(self.update_confidence_threshold)
        self.new_polygon_button.clicked.connect(self.start_new_polygon)
        self.delete_polygon_button.clicked.connect(self.enable_polygon_deletion)
        
        print("Configuration des raccourcis clavier...")
        # Ajout des raccourcis clavier
        QShortcut(QKeySequence("p"), self).activated.connect(self.show_previous_image)
        print("Raccourci 'p' configuré")
        QShortcut(QKeySequence("n"), self).activated.connect(self.show_next_image)
        print("Raccourci 'n' configuré")
        QShortcut(QKeySequence("d"), self).activated.connect(self.enable_polygon_deletion)
        print("Raccourci 'd' configuré")
        QShortcut(QKeySequence(":"), self).activated.connect(self.start_new_polygon)
        print("Raccourci ':' configuré")
        QShortcut(QKeySequence("="), self).activated.connect(self.add_midpoints_to_polygon)
        print("Raccourci '=' configuré")
        print("Configuration des raccourcis clavier terminée")
    
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
        """Active le mode suppression de polygone ou de point."""
        if self.selected_point is not None:
            # Supprimer le point sélectionné
            polygon, point_index = self.selected_point
            print(f"Suppression du point {point_index} du polygone {polygon.name}")
            polygon.points.pop(point_index)
            if len(polygon.points) < 3:
                # Si le polygone n'a plus assez de points, le supprimer
                self.current_annotations.remove(polygon)
            self.selected_point = None
        elif self.current_polygon is not None:
            # Supprimer le polygone sélectionné
            print(f"Suppression du polygone {self.current_polygon.name}")
            self.current_annotations.remove(self.current_polygon)
            self.current_polygon = None
        
        self.update_image_display()
    
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
    
    def handle_mouse_click(self, pos):
        if self.original_image is None:
            return
        
        # Convertir QPointF en QPoint
        point = QPoint(int(pos.x()), int(pos.y()))
        scene_pos = self.image_viewer.mapToScene(point)
        
        # Vérifier si on clique sur un point d'un polygone
        for polygon in self.current_annotations:
            for i, point in enumerate(polygon.points):
                if abs(point.x - scene_pos.x()) < 10 and abs(point.y - scene_pos.y()) < 10:
                    self.selected_point = (polygon, i)
                    self.selected_polygon = polygon
                    polygon.start_drag(scene_pos.x(), scene_pos.y())
                    self.select_polygon(polygon)
                    return
                
        # Vérifier si on clique sur un polygone
        for polygon in self.current_annotations:
            if polygon.is_point_inside(scene_pos.x(), scene_pos.y()):
                self.selected_polygon = polygon
                polygon.start_drag(scene_pos.x(), scene_pos.y())
                self.select_polygon(polygon)
                return
            
        # Si on ne clique sur rien, désélectionner tout
        self.deselect_all()
    
    def handle_mouse_move(self, pos):
        if self.original_image is None:
            return
        
        # Convertir QPointF en QPoint
        point = QPoint(int(pos.x()), int(pos.y()))
        scene_pos = self.image_viewer.mapToScene(point)
        
        if self.selected_point:
            polygon, point_index = self.selected_point
            polygon.move_point(point_index, scene_pos.x(), scene_pos.y())
            self.update_image_display()
        elif self.selected_polygon:
            self.selected_polygon.update_drag(scene_pos.x(), scene_pos.y())
            self.update_image_display()
    
    def handle_mouse_release(self, pos):
        """Gère le relâchement du bouton de la souris."""
        if self.selected_point:
            polygon, _ = self.selected_point
            polygon.end_drag()
            self.selected_point = None
            self.update_image_display()
        elif self.selected_polygon:
            self.selected_polygon.end_drag()
            self.update_image_display()
    
    def deselect_all(self):
        """Désélectionne tous les éléments."""
        # Désélectionner tous les polygones et points
        for polygon in self.current_annotations:
            polygon.is_selected = False
            polygon.selected_point_index = -1
            polygon.drag_start = None
            for point in polygon.points:
                point.is_selected = False
        
        # Réinitialiser les variables d'état
        self.current_polygon = None
        self.selected_polygon = None
        self.selected_point = None
        self.delete_polygon_button.setEnabled(False)
        self.update_image_display()
    
    def update_image_display(self):
        """Met à jour l'affichage de l'image avec les annotations."""
        if self.original_image is None:
            return

        # Créer une copie profonde de l'image originale
        display_image = self.original_image.copy()
        
        # Calculer l'épaisseur des lignes en fonction du zoom
        line_thickness = max(1, int(2 * self.current_zoom))
        point_radius = max(3, int(5 * self.current_zoom))

        # Dessiner tous les polygones
        for polygon in self.current_annotations:
            # Ajuster l'opacité en fonction de la sélection
            opacity = 0.1 if polygon.is_selected else 0.05
            polygon.draw(display_image, line_thickness=line_thickness, point_radius=point_radius, opacity=opacity)
            
            # Si c'est le polygone sélectionné, créer la prévisualisation
            if polygon.is_selected:
                preview_image = self.create_preview_image(polygon)
                if preview_image is not None:
                    preview_pixmap = QPixmap.fromImage(preview_image)
                    self.preview_label.setPixmap(preview_pixmap.scaled(
                        self.preview_label.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    ))

        # Convertir l'image en QImage pour l'affichage
        height, width, channel = display_image.shape
        bytes_per_line = 3 * width
        
        # S'assurer que l'image est au format RGB
        if channel == 4:  # Si l'image a un canal alpha
            display_image = cv2.cvtColor(display_image, cv2.COLOR_BGRA2RGB)
        elif channel == 3:  # Si l'image est en BGR
            display_image = cv2.cvtColor(display_image, cv2.COLOR_BGR2RGB)
            
        # Créer le QImage
        q_image = QImage(display_image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)

        # Mettre à jour l'image dans le QGraphicsScene
        if self.image_item is None:
            self.image_item = QGraphicsPixmapItem(QPixmap.fromImage(q_image))
            self.scene.addItem(self.image_item)
        else:
            self.image_item.setPixmap(QPixmap.fromImage(q_image))

        # Mettre à jour la scène
        self.scene.setSceneRect(self.image_item.boundingRect())
        self.image_viewer.setScene(self.scene)
        
        # Restaurer le zoom précédent
        if self.current_zoom != 1.0:
            self.image_viewer.setTransform(QTransform().scale(self.current_zoom, self.current_zoom))

    def create_preview_image(self, polygon):
        """Crée une prévisualisation de l'image à l'intérieur du polygone sélectionné."""
        if self.original_image is None:
            return None

        # Créer une copie de l'image originale
        preview = self.original_image.copy()
        
        # Créer un masque pour le polygone
        mask = np.zeros(preview.shape[:2], dtype=np.uint8)
        points = np.array([[int(p.x), int(p.y)] for p in polygon.points], dtype=np.int32)
        cv2.fillPoly(mask, [points], 255)
        
        # Appliquer le masque à l'image
        preview = cv2.bitwise_and(preview, preview, mask=mask)
        
        # Trouver les limites du polygone
        x, y, w, h = cv2.boundingRect(points)
        
        # Recadrer l'image sur le polygone
        preview = preview[y:y+h, x:x+w]
        
        # Convertir en QImage
        height, width, channel = preview.shape
        bytes_per_line = 3 * width
        if channel == 4:
            preview = cv2.cvtColor(preview, cv2.COLOR_BGRA2RGB)
        elif channel == 3:
            preview = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
            
        return QImage(preview.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
    
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
            # Sauvegarder les annotations actuelles si nécessaire
            if self.current_annotations:
                self.save_annotations()
            self.current_image_index += 1
            self.current_annotations = []  # Réinitialiser les annotations
            self.current_polygon = None
            self.selected_point = None
            self.show_current_image()
    
    def show_previous_image(self):
        """Affiche l'image précédente."""
        if self.current_image_index > 0:
            # Sauvegarder les annotations actuelles si nécessaire
            if self.current_annotations:
                self.save_annotations()
            self.current_image_index -= 1
            self.current_annotations = []  # Réinitialiser les annotations
            self.current_polygon = None
            self.selected_point = None
            self.show_current_image()
    
    def save_annotations(self):
        """Sauvegarde les annotations actuelles."""
        if self.current_image_path:
            self.annotation_manager.save_annotations(
                self.current_image_path,
                self.current_annotations,
                self.labels
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
    
    def select_polygon(self, polygon):
        """Sélectionne un polygone."""
        print(f"Sélection du polygone {polygon.name}")
        
        # Désélectionner tous les autres polygones
        for p in self.current_annotations:
            p.is_selected = False
            p.selected_point_index = -1
            for point in p.points:
                point.is_selected = False
        
        # Sélectionner le polygone
        polygon.is_selected = True
        self.selected_polygon = polygon
        self.current_polygon = polygon
        self.delete_polygon_button.setEnabled(True)
        
        print(f"Polygone sélectionné : {polygon.name}")
        print(f"Nombre de points : {len(polygon.points)}")
        self.update_image_display()
    
    def select_point(self, polygon, point_index):
        """Sélectionne un point d'un polygone."""
        # Désélectionner tous les autres points
        for p in self.current_annotations:
            p.selected_point_index = -1
            for point in p.points:
                point.is_selected = False
        
        # Sélectionner le point
        polygon.select_point(point_index)
        self.current_polygon = polygon
        self.delete_polygon_button.setEnabled(True)
        self.update_image_display()
    
    def add_midpoints_to_polygon(self):
        """Ajoute des points au milieu de chaque ligne du polygone sélectionné."""
        print("Appel de la méthode add_midpoints_to_polygon")
        if self.selected_polygon is None:
            print("Aucun polygone sélectionné")
            return
        
        print(f"Tentative d'ajout de points au milieu des lignes du polygone {self.selected_polygon.name}")
        print(f"Nombre de points actuels : {len(self.selected_polygon.points)}")
        
        # Créer une liste pour stocker les nouveaux points avec leurs indices d'insertion
        new_points = []
        
        # Pour chaque paire de points consécutifs
        n_points = len(self.selected_polygon.points)
        for i in range(n_points):
            current_point = self.selected_polygon.points[i]
            next_point = self.selected_polygon.points[(i + 1) % n_points]
            
            # Calculer le point milieu
            mid_x = (current_point.x + next_point.x) / 2
            mid_y = (current_point.y + next_point.y) / 2
            
            print(f"Point milieu {i} calculé entre ({current_point.x}, {current_point.y}) et ({next_point.x}, {next_point.y}) : ({mid_x}, {mid_y})")
            new_points.append((i + 1, Point(mid_x, mid_y)))
        
        print(f"Nombre de points milieux calculés : {len(new_points)}")
        
        # Insérer les nouveaux points après chaque point existant
        # On parcourt la liste en sens inverse pour ne pas perturber les indices
        for insert_index, point in reversed(new_points):
            print(f"Insertion du point milieu à l'index {insert_index}")
            self.selected_polygon.points.insert(insert_index, point)
        
        print(f"Nombre de points après ajout : {len(self.selected_polygon.points)}")
        
        # Mettre à jour l'affichage
        self.update_image_display()
    
    def finish_annotation(self):
        """Termine l'annotation de l'image courante en la déplaçant vers le dossier des images annotées."""
        if not self.current_image_path:
            return
            
        # Sauvegarder les annotations actuelles
        self.save_annotations()
        
        # Déplacer l'image
        image_name = os.path.basename(self.current_image_path)
        new_image_path = os.path.join("data/annotations/images", image_name)
        
        try:
            os.rename(self.current_image_path, new_image_path)
            print(f"Image déplacée avec succès : {new_image_path}")
            
            # Mettre à jour la liste des images
            self.image_files.remove(self.current_image_path)
            
            # Passer à l'image suivante
            if self.image_files:
                self.current_image_index = 0
                self.show_current_image()
            else:
                QMessageBox.information(
                    self, "Terminé",
                    "Toutes les images ont été annotées !"
                )
                self.close()
        except Exception as e:
            QMessageBox.critical(
                self, "Erreur",
                f"Erreur lors du déplacement de l'image : {str(e)}"
            ) 