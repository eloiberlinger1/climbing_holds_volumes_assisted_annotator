from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QFileDialog,
                            QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from src.core.annotation_manager import AnnotationManager
from src.core.image_processor import ImageProcessor
import os
from config import TO_ANNOTATE_DIR

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Outil d'Annotation pour Prises d'Escalade")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialisation des gestionnaires
        self.annotation_manager = AnnotationManager()
        self.image_processor = ImageProcessor()
        
        # Variables
        self.current_image = None
        self.current_image_path = None
        self.current_detections = None
        self.current_labels = None
        self.image_files = []
        self.current_image_index = -1
        
        self.init_ui()
        
    def init_ui(self):
        # Widget principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Zone d'affichage de l'image
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image_label, stretch=2)
        
        # Panneau de contrôle
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        
        # Option d'assistance IA
        self.ai_assist_checkbox = QCheckBox("Activer l'assistance IA")
        self.ai_assist_checkbox.stateChanged.connect(self.toggle_ai_assist)
        control_layout.addWidget(self.ai_assist_checkbox)
        
        # Sélection du répertoire
        self.select_dir_button = QPushButton("Sélectionner un répertoire d'images")
        self.select_dir_button.clicked.connect(self.select_directory)
        control_layout.addWidget(self.select_dir_button)
        
        # Navigation
        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("Image précédente")
        self.prev_button.clicked.connect(self.previous_image)
        self.next_button = QPushButton("Image suivante")
        self.next_button.clicked.connect(self.next_image)
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)
        control_layout.addLayout(nav_layout)
        
        # Informations sur la progression
        self.progress_label = QLabel("Aucune image sélectionnée")
        control_layout.addWidget(self.progress_label)
        
        # Boutons d'action
        self.save_button = QPushButton("Sauvegarder et passer à la suivante")
        self.save_button.clicked.connect(self.save_and_next)
        control_layout.addWidget(self.save_button)
        
        layout.addWidget(control_panel, stretch=1)
        
        # Désactiver les boutons de navigation initialement
        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.save_button.setEnabled(False)
    
    def select_directory(self, dir_path=None):
        """Sélectionne un répertoire contenant des images à annoter."""
        if dir_path is None:
            dir_path = QFileDialog.getExistingDirectory(
                self, "Sélectionner un répertoire d'images", TO_ANNOTATE_DIR
            )
        
        if dir_path:
            # Récupérer la liste des images
            self.image_files = [
                os.path.join(dir_path, f) for f in os.listdir(dir_path)
                if f.lower().endswith(('.png', '.jpg', '.jpeg'))
            ]
            
            if not self.image_files:
                QMessageBox.warning(self, "Attention", "Aucune image trouvée dans le répertoire")
                return
            
            # Activer les boutons de navigation
            self.prev_button.setEnabled(True)
            self.next_button.setEnabled(True)
            self.save_button.setEnabled(True)
            
            # Charger la première image
            self.current_image_index = 0
            self.load_current_image()
    
    def load_current_image(self):
        """Charge l'image courante."""
        if 0 <= self.current_image_index < len(self.image_files):
            self.current_image_path = self.image_files[self.current_image_index]
            self.current_image = self.image_processor.load_image(self.current_image_path)
            self.display_image()
            self.run_detection()
            self.update_progress_label()
    
    def update_progress_label(self):
        """Met à jour le label de progression."""
        if self.image_files:
            self.progress_label.setText(
                f"Image {self.current_image_index + 1}/{len(self.image_files)}"
            )
    
    def previous_image(self):
        """Charge l'image précédente."""
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.load_current_image()
    
    def next_image(self):
        """Charge l'image suivante."""
        if self.current_image_index < len(self.image_files) - 1:
            self.current_image_index += 1
            self.load_current_image()
    
    def save_and_next(self):
        """Sauvegarde les annotations et passe à l'image suivante."""
        if self.current_image_path and self.current_detections is not None:
            self.annotation_manager.save_annotations(
                self.current_image_path,
                self.current_detections,
                self.current_labels
            )
            self.next_image()
    
    def toggle_ai_assist(self, state):
        """Active ou désactive l'assistance IA."""
        if state == Qt.CheckState.Checked.value:
            try:
                self.image_processor.enable_ai_assist()
                QMessageBox.information(self, "Succès", "L'assistance IA a été activée")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'activation de l'assistance IA : {str(e)}")
                self.ai_assist_checkbox.setChecked(False)
        else:
            self.image_processor.disable_ai_assist()
            QMessageBox.information(self, "Info", "L'assistance IA a été désactivée")
    
    def display_image(self):
        if self.current_image is not None:
            self.image_processor.display_image(self.current_image, self.image_label)
    
    def run_detection(self):
        if self.current_image_path:
            self.current_detections, self.current_labels = self.image_processor.run_detection(self.current_image_path)
            if self.current_detections is not None:
                # Créer une copie de l'image pour afficher les détections
                display_image = self.current_image.copy()
                display_image = self.image_processor.draw_annotations(
                    display_image, self.current_detections, self.current_labels
                )
                self.image_processor.display_image(display_image, self.image_label) 