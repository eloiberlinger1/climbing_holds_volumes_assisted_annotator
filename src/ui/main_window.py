from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QFileDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from ..core.annotation_manager import AnnotationManager
from ..core.image_processor import ImageProcessor

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
        
        # Boutons
        self.load_button = QPushButton("Charger une image")
        self.load_button.clicked.connect(self.load_image)
        control_layout.addWidget(self.load_button)
        
        self.save_button = QPushButton("Sauvegarder les annotations")
        self.save_button.clicked.connect(self.save_annotations)
        control_layout.addWidget(self.save_button)
        
        layout.addWidget(control_panel, stretch=1)
        
    def load_image(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Choisir une image", "", "Images (*.png *.jpg *.jpeg)"
        )
        if file_name:
            self.current_image_path = file_name
            self.current_image = self.image_processor.load_image(file_name)
            self.display_image()
            self.run_detection()
    
    def display_image(self):
        if self.current_image is not None:
            self.image_processor.display_image(self.current_image, self.image_label)
    
    def run_detection(self):
        if self.current_image_path:
            results = self.image_processor.run_detection(self.current_image_path)
            # TODO: Afficher les résultats de détection sur l'image
    
    def save_annotations(self):
        if self.current_image_path:
            self.annotation_manager.save_annotations(self.current_image_path) 