import sys
import os
from PyQt6.QtWidgets import QApplication
from src.gui.main_window import MainWindow
from config import TO_ANNOTATE_DIR

def main(args):
    app = QApplication(sys.argv)
    window = MainWindow()
    
    # Configuration selon les arguments
    if args.test_dir:
        if os.path.exists(args.test_dir):
            window.image_files = [
                os.path.join(args.test_dir, f) for f in os.listdir(args.test_dir)
                if f.lower().endswith(('.png', '.jpg', '.jpeg'))
            ]
            if window.image_files:
                window.current_image_index = 0
                window.show_current_image()
        else:
            print(f"Le répertoire de test {args.test_dir} n'existe pas")
    
    if args.no_ai:
        window.ai_assist_button.setChecked(False)
    
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 