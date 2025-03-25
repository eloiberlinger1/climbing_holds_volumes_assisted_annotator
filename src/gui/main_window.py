from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox,
    QSlider, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
import os
from ..core.image_processor import ImageProcessor
from ..core.annotation_manager import AnnotationManager

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
        self.confidence_slider.setValue(80)  # Valeur par défaut à 80%
        self.confidence_value_label = QLabel("80%")
        confidence_layout.addWidget(confidence_label)
        confidence_layout.addWidget(self.confidence_slider)
        confidence_layout.addWidget(self.confidence_value_label)
        
        # Ajout des contrôles IA au layout
        ai_layout.addWidget(self.ai_assist_button)
        ai_layout.addLayout(confidence_layout)
        ai_group.setLayout(ai_layout)
        
        # Ajout des groupes au layout principal
        main_layout.addWidget(navigation_group)
        main_layout.addWidget(ai_group)
        
        # Zone d'affichage de l'image
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(800, 600)
        self.image_label.setStyleSheet("border: 1px solid black")
        main_layout.addWidget(self.image_label)
        
        # Connexion des signaux
        self.prev_button.clicked.connect(self.show_previous_image)
        self.next_button.clicked.connect(self.show_next_image)
        self.save_button.clicked.connect(self.save_annotations)
        self.ai_assist_button.clicked.connect(self.toggle_ai_assist)
        self.confidence_slider.valueChanged.connect(self.update_confidence_threshold)
        
        # Ajout des raccourcis clavier
        QShortcut(QKeySequence("p"), self).activated.connect(self.prev_button.click)
        QShortcut(QKeySequence("n"), self).activated.connect(self.next_button.click)
        QShortcut(QKeySequence("s"), self).activated.connect(self.save_button.click)
        
        # État initial
        self.current_image_index = -1
        self.image_files = []
        self.current_image_path = None
        self.current_annotations = []
        
        # Charger les images du dossier de test
        self.load_images()
    
    def update_confidence_threshold(self, value):
        """Met à jour le seuil de confiance et l'affiche."""
        threshold = value / 100.0
        self.image_processor.set_confidence_threshold(threshold)
        self.confidence_value_label.setText(f"{value}%")
        if self.current_image_path:
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
            
            image = self.image_processor.load_image(self.current_image_path)
            if image is None:
                print(f"Erreur : Impossible de charger l'image {self.current_image_path}")
                return
                
            print(f"Image chargée avec succès : {image.shape}")
            
            # Exécuter la détection si l'assistance IA est activée
            if self.ai_assist_button.isChecked():
                print("Détection IA en cours...")
                detections, labels = self.image_processor.run_detection(
                    self.current_image_path
                )
                if detections is not None:
                    print(f"Détection réussie : {len(labels)} objets trouvés")
                    image = self.image_processor.draw_annotations(
                        image, detections, labels
                    )
                else:
                    print("Aucune détection trouvée")
            
            self.image_processor.display_image(image, self.image_label)
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