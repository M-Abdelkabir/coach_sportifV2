# Guide d'Installation : Virtual Sports Coach sur Raspberry Pi

Ce guide vous accompagne dans l'installation et le lancement du projet sur un Raspberry Pi 5.

## 1. Installation Automatisée (Recommandé)
Nous avons créé un script tout-en-un pour simplifier l'installation.

```bash
# Rendre le script exécutable
chmod +x setup_and_run_pi.sh

# Lancer l'installation et le démarrage
./setup_and_run_pi.sh
```
Ce script s'occupera d'installer les dépendances système, de configurer les environnements virtuels et de compiler le frontend.

## 2. Matériel Requis
- Raspberry Pi 5 (8GB recommandé).
- Caméra USB ou Module Caméra RPi (v2 ou v3).
- LED RGB et Buzzer (Optionnel, pour le feedback physique).
- Disque SSD ou Carte MicroSD (64GB+).

## 2. Préparation du Système
Assurez-vous d'utiliser **Raspberry Pi OS (64-bit)**.

```bash
# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Installation des dépendances système pour OpenCV et MediaPipe
sudo apt install -y libgl1-mesa-glx libglib2.0-0 libatlas-base-dev
```

## 3. Installation du Projet
Clonez le projet et configurez l'environnement Python.

```bash
# Navigation vers le dossier du projet
cd virtual-sports-coach-final

# Création de l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installation des dépendances
pip install -r backend/requirements.txt
pip install gpiozero RPi.GPIO lgpio
```

## 4. Configuration
### Backend
Créez un fichier `backend/.env` :
```env
DATABASE_URL="sqlite:///./coach.db"
ENABLE_HARDWARE=True
```

### Frontend
Créez un fichier `frontend/.env.local` :
```env
# Remplacez <IP_DU_PI> par l'adresse IP réelle de votre Raspberry Pi
NEXT_PUBLIC_API_URL="http://<IP_DU_PI>:8000"
NEXT_PUBLIC_WS_URL="ws://<IP_DU_PI>:8000/ws"
```

## 5. Lancement
Il est recommandé d'ouvrir deux terminaux.

### Terminal 1 : Backend
```bash
source venv/bin/activate
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Terminal 2 : Frontend
```bash
cd frontend
npm install
npm run build
npm start
```

## 6. Configuration Hybride (PC + Raspberry Pi)
Si vous voulez lancer le **Frontend sur votre PC** et le **Backend sur le Pi** :

1. **Sur le Raspberry Pi** :
   - Lancez le backend comme indiqué à l'étape 5 avec `--host 0.0.0.0`.
   - Notez l'adresse IP du Pi (tapez `hostname -I` dans le terminal).

2. **Sur votre PC** :
   - Allez dans le dossier `frontend`.
   - Modifiez (ou créez) le fichier `.env.local`.
   - Remplacez `localhost` par l'adresse IP du Pi :
     ```env
     NEXT_PUBLIC_API_URL="http://192.168.x.x:8000"
     NEXT_PUBLIC_WS_URL="ws://192.168.x.x:8000/ws"
     ```
   - Lancez le frontend : `npm run dev`.

## 7. Branchements Hardware (GPIO)
Si vous utilisez les composants physiques :
- **LED Rouge** : GPIO 17
- **LED Verte** : GPIO 27
- **LED Bleue** : GPIO 22
- **Buzzer** : GPIO 23
- **GND** : N'importe quelle broche Ground (ex: Pin 6).

## 7. Mode Kiosque (Optionnel)
Pour transformer le Pi en borne dédiée, lancez Chromium au démarrage :
```bash
chromium-browser --kiosk http://localhost:3000
```
