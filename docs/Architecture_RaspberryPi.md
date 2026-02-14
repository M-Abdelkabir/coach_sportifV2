# Rapport Architectural : Virtual Sports Coach sur Raspberry Pi 5

## 1. Introduction
Ce rapport détaille la structure technique et l'implémentation du système **Virtual Sports Coach** sur la plateforme Raspberry Pi 5. L'objectif est de transformer un micro-ordinateur en un coach sportif intelligent capable d'analyser les mouvements en temps réel et de fournir un retour physiologique via des capteurs.

## 2. Architecture du Système
Le système repose sur une architecture découplée offrant une grande flexibilité :

### A. Backend (Cœur de l'IA)
- **Framework** : FastAPI (Python 3.11+) pour une gestion asynchrone performante des flux de données.
- **Vision par Ordinateur** : Utilisation de **MediaPipe** et **OpenCV** pour la détection de squelette (33 points clés).
- **Moteur d'Exercice** : Un algorithme propriétaire (`exercise_engine.py`) qui valide les répétitions en fonction de seuils angulaires personnalisés (calculés lors de la calibration).
- **Base de Données** : SQLite (`aiosqlite`) pour le stockage local des profils et de l'historique des sessions.

### B. Frontend (Interface Utilisateur)
- **Framework** : Next.js 15+ avec React 19.
- **Communication** : WebSockets pour une synchronisation instantanée (latence < 50ms) entre les feedbacks de l'IA et l'affichage.
- **Design** : Interface moderne avec Glassmorphism, optimisée pour un affichage fluide sur écran tactile ou moniteur externe.

## 3. Écosystème Hardware
L'intégration du Raspberry Pi permet une interaction physique unique :

- **Visual Feedback** : Une LED RGB (GPIO 17, 27, 22) indique l'état de la séance :
  - **Vert** : Forme parfaite.
  - **Orange** : Correction nécessaire.
  - **Rouge** : Alerte de sécurité.
- **Audio Feedback** : Un Buzzer (GPIO 23) signale la fin des répétitions et les erreurs critiques.
- **Sécurité** : Intégration de capteurs simulés (via `hardware_sim.py`) ou réels pour monitorer la fréquence cardiaque et les tremblements musculaires (IMU).

## 4. Optimisations pour Raspberry Pi 5
Pour garantir une expérience fluide à 30+ FPS :
1. **Inférence Hybrid** : Possibilité de déporter l'analyse d'image du CPU vers les WebSockets si nécessaire.
2. **Throttling des Trames** : Gestion intelligente du débit d'images pour éviter la saturation thermique.
3. **Audio Offline** : Utilisation de `pyttsx3` pour la synthèse vocale sans dépendance au cloud.

## 5. Conclusion
Le Virtual Sports Coach sur Raspberry Pi 5 représente une solution de coaching "Edge AI" robuste, privée et réactive, capable de fonctionner sans connexion internet permanente tout en offrant des performances de niveau professionnel.
