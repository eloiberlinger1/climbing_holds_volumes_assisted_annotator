import argparse
import sys
from src.main import main

def parse_args():
    parser = argparse.ArgumentParser(description='Outil d\'annotation pour prises d\'escalade')
    parser.add_argument('--debug', action='store_true', help='Active le mode debug')
    parser.add_argument('--test-dir', type=str, help='Chemin du répertoire de test')
    parser.add_argument('--no-ai', action='store_true', help='Désactive l\'assistance IA')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    
    if args.debug:
        print("Mode debug activé")
        print(f"Arguments reçus : {args}")
    
    try:
        main(args)
    except Exception as e:
        if args.debug:
            print(f"Erreur : {str(e)}")
            import traceback
            traceback.print_exc()
        else:
            print(f"Une erreur est survenue : {str(e)}")
        sys.exit(1)
