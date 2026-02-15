# Coach Sportif Virtuel - Documentation Complète

Bienvenue dans le projet **Coach Sportif Virtuel**. Ce document explique en détail le fonctionnement du système, son architecture, ses fonctionnalités et les prérequis nécessaires.

---

## Architecture du Projet

Le projet suit une architecture **Client-Serveur** moderne avec une séparation nette entre le traitement de données (Backend) et l'interface utilisateur (Frontend).

### 1. Structure Globale
- **Backend** : Serveur FastAPI (Python) qui gère la capture de la caméra, traite les flux de données en temps réel et expose un flux vidéo MJPEG.
- **Frontend** : Application React/Next.js qui affiche l'interface, reçoit le flux vidéo du backend et affiche les feedbacks utilisateur.
- **Modèles ML** : Moteurs d'intelligence artificielle pour la détection de pose et la classification d'exercices.

### 2. Flux de Données (Real-time)
1. Le **Backend** capture les images directement de la caméra (via OpenCV).
2. Le **Backend** traite chaque image avec **MediaPipe** pour extraire 33 points clés.
3. Les modèles **LSTM** et **ONNX** analysent ces points pour valider la posture.
4. Le **Backend** envoie les résultats (répétitions, erreurs, confiance) via **WebSockets**.
5. Parallèlement, le **Backend** diffuse le flux vidéo traité (avec squelette) via un endpoint HTTP (`/video_feed`).
6. Le **Frontend** reçoit le flux vidéo et affiche les feedbacks dynamiques.

---

## Fonctionnalités Principales

### 1. Analyse de Pose en Temps Réel
Utilisation de **MediaPipe** et **YOLOv11-Pose** pour suivre les mouvements du corps avec une précision millimétrique, même sur des machines peu puissantes (comme le Raspberry Pi).

### 2. Classification Intelligente (LSTM)
Un modèle de réseau de neurones récurrent (LSTM) analyse les séquences de mouvements pour identifier précisément l'exercice effectué (Squat, Pushup) et sa qualité.

### 3. Validation de Posture & Corrections Vocales
- **Validation** : Le système détecte si le dos est droit, si les genoux sont bien alignés, etc.
- **Feedback Vocal** : Utilisation de l'API **Web Speech** pour donner des conseils en français (ex: "Gardez le dos droit !") sans que l'utilisateur ait besoin de regarder l'écran.

### 4. Suivi des Performances
- **Compteur de répétitions** : Détection automatique des phases de montée et descente.
- **Historique** : Sauvegarde des sessions dans une base de données **SQLite**.
- **Statistiques** : Visualisation des progrès via un tableau de bord.

### 5. Mode Hybride (Pi + PC)
Possibilité de faire tourner le backend sur un Raspberry Pi et le frontend sur un PC, ou tout sur la même machine.

---

## Exigences Techniques

### Logiciels (Software)
- **Python 3.9+** : Pour le moteur de calcul et l'IA.
- **Node.js 18+** : Pour l'interface utilisateur.
- **Bibliothèques Clés** :
  - `mediapipe` : Détection de squelette.
  - `fastapi` : Serveur web haute performance.
  - `ultralytics` (YOLO) : Alternative pour la pose.
  - `tensorflow/keras` : Pour le modèle LSTM.

### Matériel (Hardware)
- **Webcam** : 720p recommandé pour une meilleure détection.
- **Processeur** : CPU moderne (Intel i5/Ryzen 5) ou Raspberry Pi 4/5.
- **Mémoire** : Minimum 4 Go de RAM.

---

## Installation & Utilisation

### 1. Préparation du Backend
```bash
cd backend
python -m venv venv
# Activer le venv (Windows: venv\Scripts\activate)
pip install -r requirements.txt
python main.py
```

### 2. Préparation du Frontend
```bash
cd frontend
npm install
npm run dev
```

Accédez ensuite à `http://localhost:3000` pour commencer votre entraînement.

---

## Structure des Dossiers (Après Nettoyage)
- `/backend/tests` : Tests de validation des modèles.
- `/backend/models` : Modèles IA (.h5, .onnx, .pt, .task).
- `/backend/scripts` : Scripts d'installation et de lancement.
- `/frontend/components` : Composants UI (React).
- `/docs` : Guides détaillés et architecture.

---

*Développé pour offrir une expérience de coaching sportif intelligente et accessible.* 