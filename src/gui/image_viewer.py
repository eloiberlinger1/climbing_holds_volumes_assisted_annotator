from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QImage, QPixmap, QPainter, QTransform, QWheelEvent
import cv2

class ImageViewer(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.zoom_factor = 1.0
        self.is_panning = False
        self.is_dragging = False
        self.last_mouse_pos = None
        self.first_image_load = True
        self.initial_zoom_done = False
        
        # Configuration de la vue
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # Créer une scène vide
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

    def set_image(self, image):
        if image is None:
            return
            
        print(f"[DEBUG] Configuration de l'image. Zoom actuel : {self.zoom_factor}")
        height, width = image.shape[:2]
        bytes_per_line = 3 * width
        q_image = QImage(image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        
        # Sauvegarder le zoom actuel si ce n'est pas le premier chargement
        current_zoom = self.zoom_factor if not self.first_image_load else None
        print(f"[DEBUG] Zoom sauvegardé : {current_zoom}")
        
        self._scene.clear()
        self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(0, 0, width, height)
        
        if self.first_image_load:
            print("[DEBUG] Premier chargement de l'image")
            self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            
            # Calculer le facteur de zoom initial
            viewport_rect = self.viewport().rect()
            scene_rect = self._scene.sceneRect()
            scale_x = viewport_rect.width() / scene_rect.width()
            scale_y = viewport_rect.height() / scene_rect.height()
            self.zoom_factor = min(scale_x, scale_y)
            
            print(f"[DEBUG] Zoom initial calculé : {self.zoom_factor}")
            self.first_image_load = False
            self.initial_zoom_done = True
        else:
            # Restaurer le zoom précédent
            self.zoom_factor = current_zoom
            print(f"[DEBUG] Restauration du zoom précédent : {self.zoom_factor}")
        
        # Appliquer le zoom
        self.setTransform(QTransform().scale(self.zoom_factor, self.zoom_factor))
        print(f"[DEBUG] Transform appliquée avec zoom : {self.zoom_factor}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.initial_zoom_done and self._scene is not None:
            scene_rect = self._scene.sceneRect()
            if scene_rect.width() > 0 and scene_rect.height() > 0:
                self.fitInView(scene_rect, Qt.AspectRatioMode.KeepAspectRatio)
                viewport_rect = self.viewport().rect()
                scale_x = viewport_rect.width() / scene_rect.width()
                scale_y = viewport_rect.height() / scene_rect.height()
                self.zoom_factor = min(scale_x, scale_y)
                self.setTransform(QTransform().scale(self.zoom_factor, self.zoom_factor))
                self.initial_zoom_done = True

    def mousePressEvent(self, event):
        """Gère les événements de clic de souris."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = True
            self.last_mouse_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        else:
            # Transmettre l'événement à la fenêtre principale
            main_window = self.window()
            if main_window:
                main_window.handle_mouse_click(event.pos())

    def mouseReleaseEvent(self, event):
        """Gère les événements de relâchement du bouton de la souris."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = False
            self.last_mouse_pos = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            # Transmettre l'événement à la fenêtre principale
            main_window = self.window()
            if main_window:
                main_window.handle_mouse_release(event.pos())

    def mouseMoveEvent(self, event):
        """Gère les événements de déplacement de la souris."""
        if self.is_panning and self.last_mouse_pos:
            delta = event.pos() - self.last_mouse_pos
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            self.last_mouse_pos = event.pos()
        else:
            # Transmettre l'événement à la fenêtre principale
            main_window = self.window()
            if main_window:
                main_window.handle_mouse_move(event.pos())

    def wheelEvent(self, event: QWheelEvent):
        """Gère le zoom avec Ctrl + molette et le défilement normal avec la molette."""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Zoom avec Ctrl + molette
            zoom_factor = 1.15
            delta = event.angleDelta().y()
            
            if delta > 0:
                self.zoom_factor *= zoom_factor
            else:
                self.zoom_factor /= zoom_factor
                
            # Limiter le zoom entre 0.1 et 10
            self.zoom_factor = max(0.1, min(10.0, self.zoom_factor))
            
            # Appliquer le zoom
            self.setTransform(QTransform().scale(self.zoom_factor, self.zoom_factor))
            
            # Mettre à jour l'affichage via la fenêtre principale
            main_window = self.window()
            if main_window:
                main_window.update_image_display()
        else:
            # Défilement normal
            super().wheelEvent(event) 