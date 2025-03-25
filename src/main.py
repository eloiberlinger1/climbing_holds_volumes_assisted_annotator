import sys
import os
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from config import TO_ANNOTATE_DIR

def main(args):
    app = QApplication(sys.argv)
    window = MainWindow()
    
    # Configuration selon les arguments
    if args.test_dir:
        if os.path.exists(args.test_dir):
            window.select_directory(args.test_dir)
        else:
            print(f"Le répertoire de test {args.test_dir} n'existe pas")
    
    if args.no_ai:
        window.ai_assist_checkbox.setChecked(False)
    
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 