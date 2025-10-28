# 🎮 Conduite Accessible par Mouvements de Tête

> Jouez à Forza Horizon et autres jeux de course **uniquement avec votre tête**
> Spécialement conçu pour les personnes en situation de handicap moteur

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green)
![MediaPipe](https://img.shields.io/badge/MediaPipe-latest-orange)

---

## 📖 Table des Matières

1. [C'est quoi ?](#-cest-quoi-)
2. [Installation (5 minutes)](#-installation-5-minutes)
3. [Première Utilisation (30 secondes)](#-première-utilisation-30-secondes)
4. [Comment ça Marche](#-comment-ça-marche)
5. [Modes de Contrôle](#-modes-de-contrôle)
6. [Personnalisation](#-personnalisation)
7. [Conseils d'Accessibilité](#-conseils-daccessibilité)
8. [Dépannage](#-dépannage)
9. [Configuration Avancée](#-configuration-avancée)

---

## 🎯 C'est quoi ?

Un système qui transforme les **mouvements de votre tête** en commandes de jeu. Vous bougez la tête, votre personnage dans le jeu tourne, accélère ou freine.

### ✨ Ce qui le rend spécial :

| Fonctionnalité | Description |
|----------------|-------------|
| **🎯 Calibration personnalisée** | S'adapte à VOTRE posture en 3 secondes |
| **🛡️ Zones mortes** | Ignore les tremblements et petits mouvements involontaires |
| **🌊 Mouvements fluides** | Technologie de lissage avancée (pas de saccades) |
| **🎨 3 modes** | Position / Vitesse / Simplifié (avance automatique) |
| **📊 Interface claire** | Vous voyez en direct ce que vous faites |
| **🔒 Sécurité** | Pause automatique si vous vous éloignez |
| **⚙️ Personnalisable** | Ajustez tout en temps réel |

### 👥 Pour qui ?

- ✅ Personnes avec handicap moteur des membres supérieurs
- ✅ Personnes avec mobilité limitée des bras/mains
- ✅ Personnes avec tremblements
- ✅ Gamers cherchant des contrôles alternatifs
- ✅ Toute personne voulant essayer une nouvelle façon de jouer

---

## 🚀 Installation (5 minutes)

### Prérequis

- **Windows, Linux ou Mac**
- **Python 3.8+** → [Télécharger Python](https://www.python.org/downloads/)
- **Une webcam** (intégrée ou USB)

### Méthode 1 : Automatique (Windows)

1. Double-cliquez sur **`installer.bat`**
2. Attendez la fin de l'installation
3. C'est prêt !

### Méthode 2 : Manuel

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Tester que tout fonctionne
python test_setup.py
```

**Dépendances installées** :
- `opencv-python` → Capture vidéo
- `mediapipe` → Détection du visage
- `pyautogui` → Simulation des touches
- `numpy` → Calculs

---

## 🎮 Première Utilisation (30 secondes)

### Étape 1 : Lancer le programme

**Windows** : Double-cliquez sur `lancer.bat`
**Autres** : `python accessible_face_drive.py`

### Étape 2 : Calibration (3 secondes)

Une fenêtre s'ouvre. Vous voyez votre visage.

1. **Installez-vous confortablement**
2. **Positionnez votre tête en position naturelle**
3. **Restez immobile 3 secondes** (un compte à rebours s'affiche)
4. ✅ **C'est calibré !**

> 💡 **Important** : Cette position devient votre "position neutre". Tous vos mouvements seront mesurés à partir de là.

### Étape 3 : Jouer !

- **Lancez votre jeu** (Forza Horizon ou autre)
- **Cliquez dans la fenêtre du jeu** pour lui donner le focus
- **Bougez votre tête** :
  - 👈 Tête à gauche → Tourne à gauche
  - 👉 Tête à droite → Tourne à droite
  - ⬆️ Tête en avant → Accélère
  - ⬇️ Tête en arrière → Freine

---

## 🕹️ Comment ça Marche

### L'Interface

Quand vous lancez le programme, vous voyez :

```
┌─────────────────────────────────────────┐
│  Votre visage (webcam)                  │
│  ┌───────┐                              │
│  │ Cadre │  ← Votre visage détecté      │
│  │ vert  │                              │
│  └───────┘                              │
│                                         │
│  FPS: 30        Statut: ACTIF           │
│  Mode: position                         │
│                                         │
│  ┌─┐                                    │
│  │Z│  ← Touches actives                 │
│ Q┌┘└┐D    (vert = pressé)               │
│  │S│                                    │
│  └─┘                                    │
│                                         │
│  C:Calibrer P:Pause Q:Quitter          │
└─────────────────────────────────────────┘
```

### Les Commandes

| Touche | Action | Quand l'utiliser |
|--------|--------|------------------|
| **C** | Recalibrer | Si vous avez bougé, si les contrôles sont bizarres |
| **P** | Pause/Reprendre | Pour faire une pause sans quitter |
| **M** | Changer de mode | Pour essayer les 3 modes de contrôle |
| **+** | Plus sensible | Si vous devez bouger trop la tête |
| **-** | Moins sensible | Si ça réagit trop vite |
| **Q** | Quitter | Pour fermer le programme |

---

## 🎨 Modes de Contrôle

Appuyez sur **M** pour changer de mode. Il y en a 3 :

### 1️⃣ Mode Position (par défaut)

**Comment ça marche** : La position de votre tête contrôle la direction

- Tête à gauche de la position neutre → Tourne à gauche
- Tête à droite → Tourne à droite
- Tête en avant → Accélère
- Tête en arrière → Freine

**Idéal pour** : Contrôle précis et complet

**Exemple** : Si vous inclinez la tête 5cm à droite, la voiture tourne à droite. Si vous revenez au centre, elle avance tout droit.

---

### 2️⃣ Mode Vélocité

**Comment ça marche** : La vitesse de mouvement contrôle l'intensité

- Mouvement rapide → Action forte
- Mouvement lent → Action douce

**Idéal pour** : Conduite dynamique, ajustements fins

**Exemple** : Vous tournez la tête rapidement à gauche = virage serré. Vous la tournez lentement = virage doux.

---

### 3️⃣ Mode Simplifié ⭐ (Recommandé pour mobilité limitée)

**Comment ça marche** :
- ✅ **Avance TOUJOURS automatiquement** (touche Z pressée en permanence)
- 👈👉 **Seulement gauche/droite** avec votre tête
- ❌ **Pas de contrôle avant/arrière**

**Idéal pour** :
- Personnes avec mobilité très limitée
- Réduire la fatigue (moins de mouvements)
- Débutants
- Sessions longues

**Exemple** : Vous n'avez qu'à tourner la tête à gauche ou à droite. La voiture avance toute seule.

---

## ⚙️ Personnalisation

### Réglages Rapides (en jeu)

| Besoin | Solution |
|--------|----------|
| **Trop sensible** | Appuyez sur **-** plusieurs fois |
| **Pas assez sensible** | Appuyez sur **+** plusieurs fois |
| **Contrôles bizarres** | Appuyez sur **C** pour recalibrer |
| **Tester autre mode** | Appuyez sur **M** |
| **Faire une pause** | Appuyez sur **P** |

### Configuration Complète (fichier config.json)

Ouvrez le fichier `config.json` avec un éditeur de texte :

```json
{
  "sensitivity": {
    "horizontal": 30,    ← Plus c'est BAS, plus c'est SENSIBLE
    "vertical": 30       ← 10-20 = très sensible, 50+ = peu sensible
  },

  "dead_zone": {
    "horizontal": 15,    ← Zone où rien ne se passe (évite tremblements)
    "vertical": 20       ← Plus c'est HAUT, moins ça réagit aux petits mouvements
  },

  "control_mode": "position"  ← "position", "velocity", ou "simplified"
}
```

**Exemples concrets** :

#### Pour personnes avec tremblements
```json
"sensitivity": {
  "horizontal": 40,  ← Moins sensible
  "vertical": 40
},
"dead_zone": {
  "horizontal": 25,  ← Zone morte plus grande
  "vertical": 30
}
```

#### Pour mobilité limitée
```json
"sensitivity": {
  "horizontal": 15,  ← Très sensible (petits mouvements suffisent)
  "vertical": 15
},
"control_mode": "simplified"  ← Avance automatique
```

#### Pour contrôle précis
```json
"sensitivity": {
  "horizontal": 25,
  "vertical": 25
},
"dead_zone": {
  "horizontal": 10,  ← Zone morte petite
  "vertical": 10
}
```

---

## ♿ Conseils d'Accessibilité

### 🤝 Pour Mobilité Très Limitée

**Configuration recommandée** :
1. Mode **Simplifié** (touche M)
2. Sensibilité **élevée** (valeurs 10-20 dans config.json)
3. Zones mortes **normales** (15-20)

**Pourquoi** : Vous n'aurez qu'à tourner légèrement la tête à gauche/droite. La voiture avance toute seule.

**Astuce** : Recalibrez (touche C) dans votre position la plus confortable, même si elle est inhabituelle.

---

### 🫨 Pour Tremblements / Mouvements Involontaires

**Configuration recommandée** :
1. Mode **Position**
2. Sensibilité **basse** (valeurs 40-50)
3. Zones mortes **grandes** (25-35)
4. Activer **lissage maximum** dans config.json :

```json
"smoothing": {
  "enable_kalman": true,
  "enable_ema": true,
  "ema_alpha": 0.2    ← Plus c'est bas, plus c'est lisse (0.1-0.3)
}
```

**Pourquoi** : Les petits mouvements involontaires sont ignorés. Les mouvements intentionnels sont lissés.

**Astuce** : Recalibrez souvent (touche C) pour réajuster votre position neutre.

---

### 😓 Pour Réduire la Fatigue

**Recommandations** :
1. ✅ Mode **Simplifié** (moins de mouvements nécessaires)
2. ✅ **Pauses régulières** (touche P toutes les 10-15 min)
3. ✅ **Recalibrez** après chaque pause pour retrouver une position confortable
4. ✅ **Sessions courtes** au début (15-20 min max)
5. ✅ **Zones mortes augmentées** (20-30) pour éviter de maintenir une position

**Astuce** : Si vous sentez de la fatigue, recalibrez (C) dans une position plus détendue, même si c'est différent de votre position initiale.

---

### 💡 Conseils Généraux

#### Éclairage
- ✅ Éclairez votre visage de face
- ❌ Évitez le contre-jour (fenêtre derrière vous)
- ✅ Lumière stable (pas de lumière qui clignote)

#### Position de la Caméra
- ✅ À hauteur des yeux
- ✅ Distance 50-80 cm
- ✅ Caméra stable (pas qui bouge)

#### Environnement
- ✅ Fond uni si possible
- ✅ Position assise stable et confortable
- ✅ Support pour la tête si besoin (appui-tête)

#### Avant de Jouer
1. Testez d'abord avec le programme seul
2. Calibrez plusieurs fois pour trouver la meilleure position
3. Testez les 3 modes
4. Ajustez la sensibilité
5. Puis lancez le jeu

---

## 📷 Sélection de Caméra (Nouveau!)

### Si vous avez plusieurs caméras

Le système détecte automatiquement la meilleure caméra disponible, mais vous pouvez choisir manuellement :

**Option 1 : Automatique** (par défaut)
- Le système teste toutes les caméras
- Choisit celle avec le meilleur score de qualité
- Sauvegarde le choix dans `config.json`

**Option 2 : Manuelle**
1. Ouvrez `config.json`
2. Modifiez `"camera": {"index": X}` où X est 0, 1, 2, etc.
3. Relancez le programme

**Exemples** :
```json
// Détection automatique
"camera": {"index": -1}

// Utiliser caméra 0
"camera": {"index": 0}

// Utiliser caméra 1
"camera": {"index": 1}
```

**Comment savoir quel index ?**
Le programme affiche au démarrage :
```
[0] Camera trouvee - Resolution: 640x480 @ 30fps
[1] Camera trouvee - Resolution: 1920x1080 @ 30fps
Meilleure camera: 1 (score: 0.85)
```

---

## 🔧 Dépannage

### 📷 Mauvaise caméra sélectionnée

**Problème** : Le système choisit une caméra occupée ou mauvaise

**Solutions** :
1. Fermez les applications utilisant la webcam (Skype, Teams, Zoom)
2. Spécifiez manuellement la caméra dans `config.json` :
```json
"camera": {"index": 1}  // Essayez 0, 1, 2, etc.
```
3. Relancez le programme
4. La caméra choisie sera mémorisée

---

### ❌ "No available camera"

**Problème** : La webcam n'est pas détectée

**Solutions** :
1. Vérifiez que la webcam est branchée
2. Testez avec une autre app (Skype, Zoom, etc.)
3. Vérifiez les permissions :
   - Windows : Paramètres → Confidentialité → Caméra
   - Mac : Préférences Système → Sécurité → Caméra
4. Redémarrez l'ordinateur
5. Essayez un autre port USB

---

### 📷 Le visage n'est pas détecté (pas de cadre vert)

**Problème** : Le programme ne voit pas votre visage

**Solutions** :
1. **Améliorez l'éclairage** → Allumez une lampe devant vous
2. **Ajustez la distance** → 50-80 cm de la caméra
3. **Regardez la caméra** → Face à face
4. **Nettoyez l'objectif** → Poussière sur la webcam
5. **Retirez obstacles** → Masque, mains devant le visage, cheveux
6. **Fond uni** → Éloignez-vous d'un fond complexe

---

### ⚡ Détection instable (le cadre vert clignote)

**Problème** : La détection n'est pas stable

**Solutions** :
1. Améliorez l'éclairage (le plus important !)
2. Ne bougez pas trop vite
3. Augmentez le lissage dans `config.json` :
```json
"ema_alpha": 0.2  (au lieu de 0.3)
```
4. Vérifiez que rien ne cache partiellement votre visage
5. Fermez d'autres applications qui utilisent la webcam

---

### 🎮 Le jeu ne réagit pas

**Problème** : Les touches s'affichent dans le programme mais le jeu ne bouge pas

**Solutions** :
1. **Donnez le focus au jeu** → Cliquez dans la fenêtre du jeu
2. **Mode fenêtré** → Lancez le jeu en mode fenêtré (pas plein écran)
3. **Vérifiez les touches** :
   - Le jeu utilise-t-il ZQSD ? (ou WASD ?)
   - Si non, modifiez dans `config.json` :
```json
"keys": {
  "forward": "w",    ← Changez selon votre jeu
  "backward": "s",
  "left": "a",
  "right": "d"
}
```
4. **Administrateur** → Lancez Python en administrateur (clic droit → Exécuter en tant qu'administrateur)

---

### 🐌 Programme lent (FPS < 15)

**Problème** : Le programme est saccadé, lent

**Solutions** :
1. Fermez les autres applications
2. Débranchez autres webcams
3. Désactivez des éléments d'interface dans `config.json` :
```json
"ui": {
  "show_dead_zone": false,
  "show_active_keys": false
}
```
4. Vérifiez l'utilisation CPU (Gestionnaire des tâches)

---

### 🎯 Contrôles imprécis

**Problème** : La voiture ne fait pas ce que vous voulez

**Solutions** :
1. **Recalibrez** → Appuyez sur **C**
2. **Ajustez sensibilité** → Appuyez sur **+** ou **-**
3. **Changez de mode** → Appuyez sur **M**
4. **Augmentez zones mortes** → Dans `config.json` :
```json
"dead_zone": {
  "horizontal": 25,
  "vertical": 30
}
```
5. **Position stable** → Asseyez-vous bien, ne bougez pas tout le corps

---

### 💾 Mes réglages ne sont pas sauvegardés

**Problème** : Après fermeture, les réglages sont perdus

**Solutions** :
1. Vérifiez que `config.json` existe dans le dossier
2. Ne fermez pas brutalement (utilisez **Q** pour quitter proprement)
3. Vérifiez les permissions d'écriture du dossier
4. Modifiez directement `config.json` au lieu des touches +/-

---

### ⚠️ Le programme plante au démarrage

**Problème** : Erreur Python au lancement

**Solutions** :
1. Vérifiez les dépendances → `python test_setup.py`
2. Réinstallez les dépendances → `pip install -r requirements.txt --upgrade`
3. Vérifiez la version de Python → `python --version` (doit être 3.8+)
4. Regardez le message d'erreur et cherchez le problème

---

## 🎓 Configuration Avancée

### Fichier config.json complet

```json
{
  "camera": {
    "index": -1,                     // Index de caméra (-1 = auto, 0-9 = caméra spécifique)
    "auto_select": true,             // Détection automatique de la meilleure caméra
    "show_preview": true             // Afficher aperçu lors de la sélection
  },

  "calibration": {
    "duration_seconds": 3,           // Durée de calibration (secondes)
    "neutral_position": null         // Position neutre (auto-calculée)
  },

  "sensitivity": {
    "horizontal": 30,                // Sensibilité gauche/droite (5-100)
    "vertical": 30,                  // Sensibilité haut/bas (5-100)
    "adaptive": true                 // Sensibilité adaptative (true/false)
  },

  "dead_zone": {
    "horizontal": 15,                // Zone morte horizontale (pixels)
    "vertical": 20                   // Zone morte verticale (pixels)
  },

  "smoothing": {
    "enable_kalman": true,           // Filtre de Kalman (true/false)
    "enable_ema": true,              // Lissage EMA (true/false)
    "ema_alpha": 0.3,                // Poids du lissage (0.1-0.5)
    "kalman_R": 0.5,                 // Bruit du processus (0.1-1.0)
    "kalman_Q": 0.5                  // Bruit de mesure (0.1-1.0)
  },

  "control_mode": "position",        // "position", "velocity", "simplified"

  "safety": {
    "enable_auto_pause": true,       // Pause auto si visage perdu
    "pause_delay_seconds": 3,        // Délai avant pause auto
    "mouth_open_pause": false        // Pause par bouche ouverte (future)
  },

  "ui": {
    "show_calibration_guide": true,  // Afficher guide calibration
    "show_dead_zone": true,          // Afficher zone morte
    "show_active_keys": true,        // Afficher touches actives
    "show_fps": true,                // Afficher FPS
    "mirror_video": true             // Effet miroir de la vidéo
  },

  "keys": {
    "forward": "z",                  // Touche avancer
    "backward": "s",                 // Touche reculer
    "left": "q",                     // Touche gauche
    "right": "d"                     // Touche droite
  },

  "logging": {
    "enable": true,                  // Activer le logging
    "log_file": "driving_sessions.csv"  // Fichier de log
  }
}
```

### Explication des Paramètres

#### Sensibilité (sensitivity)
- **Plus le nombre est BAS, plus c'est SENSIBLE**
- 10-20 : Très sensible (petits mouvements = grandes actions)
- 30-40 : Sensibilité moyenne (recommandé)
- 50+ : Peu sensible (grands mouvements nécessaires)

#### Zones Mortes (dead_zone)
- Zone autour de la position neutre où rien ne se passe
- **Plus le nombre est HAUT, moins ça réagit**
- Utile pour tremblements ou mouvements involontaires
- 10-15 : Zone petite (réactif)
- 20-30 : Zone grande (stable)

#### Lissage (smoothing)
- **ema_alpha** :
  - 0.1 = Très lisse mais lent à réagir
  - 0.3 = Équilibré (recommandé)
  - 0.5 = Très réactif mais moins lisse
- **enable_kalman** : Réduit le bruit de détection
- **enable_ema** : Lisse les transitions

---

## 📊 Avant/Après

### Version Basique (face drive.py)
❌ Pas de calibration
❌ Pas de zones mortes
❌ Mouvements saccadés
❌ 1 seul mode
❌ Interface minimale
❌ Pas de sécurité

### Version Accessible (accessible_face_drive.py)
✅ Calibration personnalisée en 3s
✅ Zones mortes configurables
✅ Lissage Kalman + EMA
✅ 3 modes de contrôle
✅ Interface complète avec feedback
✅ Pause automatique + manuelle
✅ Configuration sauvegardée
✅ Ajustement en temps réel

---

## 🎁 Fichiers du Projet

```
📁 accessible forza horizont/
├── 🎮 accessible_face_drive.py  ← PROGRAMME PRINCIPAL (utilisez celui-ci !)
├── 📷 camera_handler.py          ← Gestion de la webcam
├── 👤 face_detector.py           ← Détection du visage
├── ⚙️ config.json                ← Votre configuration
├── 📦 requirements.txt           ← Liste des dépendances
├── 🧪 test_setup.py              ← Test de votre installation
├── 🪟 installer.bat              ← Installation automatique (Windows)
├── 🚀 lancer.bat                 ← Lanceur rapide (Windows)
├── 📖 README.md                  ← Ce fichier (guide complet)
├── 🔧 CLAUDE.md                  ← Documentation développeur
├── 🕹️ face drive.py              ← Version basique (legacy)
└── 🖱️ mouse drive.py             ← Contrôle par souris
```

---

## 💡 Astuces et Bonnes Pratiques

### ✅ À FAIRE

1. **Calibrez au début de chaque session** (touche C)
2. **Faites des pauses toutes les 15-20 minutes** (touche P)
3. **Recalibrez après chaque pause** pour retrouver le confort
4. **Testez les 3 modes** pour trouver celui qui vous convient
5. **Ajustez la sensibilité** progressivement (+/- par petites touches)
6. **Gardez un bon éclairage** sur votre visage
7. **Restez à 50-80cm** de la caméra
8. **Commencez par le mode Simplifié** si c'est votre première fois

### ❌ À ÉVITER

1. ❌ Jouer dans le noir complet
2. ❌ Se positionner trop près (< 30cm) ou trop loin (> 1m)
3. ❌ Oublier de recalibrer après avoir bougé
4. ❌ Faire des sessions trop longues au début (fatigue)
5. ❌ Modifier trop de paramètres d'un coup
6. ❌ Jouer avec des obstacles devant le visage
7. ❌ Négliger les signaux de fatigue

---

## 📞 Besoin d'Aide ?

### Tests Diagnostiques

```bash
# Vérifier que tout est installé correctement
python test_setup.py

# Tester juste la caméra
python camera_handler.py
```

### Fichiers Utiles

- **Configuration** : Ouvrez `config.json`
- **Logs** : Consultez `driving_sessions.csv`
- **Documentation développeur** : Lisez `CLAUDE.md`

---

## 🏆 Récapitulatif Ultra-Rapide

1. **Installer** → `installer.bat` ou `pip install -r requirements.txt`
2. **Lancer** → `lancer.bat` ou `python accessible_face_drive.py`
3. **Calibrer** → Restez immobile 3 secondes
4. **Jouer** → Bougez la tête, le jeu réagit !
5. **Ajuster** → Touches +/- pour la sensibilité, M pour le mode

**Problème ?** Appuyez sur **C** pour recalibrer !

---

**Fait avec ❤️ pour rendre le gaming accessible à tous**

🎮 **Bon jeu !** 🏎️💨
