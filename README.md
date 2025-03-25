# Outil d'Annotation pour Prises d'Escalade

Cet outil permet d'annoter des images de prises d'escalade et de volumes en utilisant un modèle YOLO pour l'assistance à l'annotation.

## Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- Clé API Roboflow

## Installation

1. Clonez ce dépôt :
```bash
git clone [URL_DU_REPO]
cd climbing_holds_volumes_assisted_annotator
```

2. Créez un environnement virtuel et activez-le :
```bash
python -m venv venv
source venv/bin/activate  # Sur Unix/macOS
# ou
.\venv\Scripts\activate  # Sur Windows
```

3. Installez les dépendances :
```bash
pip install -r requirements.txt
```

4. Configurez votre clé API Roboflow :
   - Copiez le fichier `config.example.py` en `config.py`
   - Remplacez `your_api_key_here` par votre clé API Roboflow

## Utilisation

1. Lancez l'application :
```bash
python run.py
```

2. Utilisez le bouton "Charger une image" pour sélectionner une image à annoter
3. Le modèle YOLO détectera automatiquement les prises et volumes
4. Vous pouvez ajuster les annotations si nécessaire
5. Sauvegardez les annotations au format YOLO

## Format des annotations

Les annotations sont sauvegardées au format YOLO :
- Un fichier .txt par image
- Chaque ligne représente une annotation : `class_id x_center y_center width height`
- Les coordonnées sont normalisées (0-1) 