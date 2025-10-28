# Simple Head Drive pour Forza Horizon

Ce projet propose une passerelle entre les mouvements de tete et les commandes clavier afin de rendre Forza Horizon plus accessible. Il s'appuie sur la detection de repere faciaux via MediaPipe, la capture video OpenCV et l'automatisation PyAutoGUI. L'application fournit une interface Tkinter simple pour choisir la camera, lancer la calibration et surveiller les evenements en direct.

## Objectif

Offrir une experience de conduite alternative pour les personnes qui ne peuvent pas utiliser une manette classique. Le systeme convertit simplement la posture de la tete et l'ouverture de la bouche en appuis clavier utilisables par le jeu.

## Fonctionnalites clefs

- Calibration automatique de la position neutre du visage avant chaque session.
- Acceleration proportionnelle a l'ouverture de la bouche, frein et marche arriere declenches par les mouvements verticaux de la tete.
- Direction par rotations de la tete avec modulation pulsee pour imiter un stick analogique.
- Interface Tkinter pour demarrer/arreter, choisir la camera et lire le journal d'evenements.
- Gestion des claviers AZERTY par defaut (`z`, `s`, `q`, `d`) modifiable dans le code.

## Materiel requis

- PC Windows avec Python 3.9 ou plus recent.
- Webcam ou camera compatible OpenCV (USB ou integree).
- Acces au jeu PC (Forza Horizon ou tout titre acceptant des commandes clavier).
- Bonne luminosite pour faciliter la detection du visage.

## Installation rapide

```bash
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Lancer l'application graphique

```bash
python app.py
```

1. Choisissez la camera si plusieurs options apparaissent.
2. Appuyez sur **Start** pour demarrer la calibration.
3. Suivez les consignes affichees (neutre, bouche fermee, visage bien centre).
4. Une fois la calibration terminee, la fenetre de camera s'ouvre et vous pouvez piloter le jeu.

Vous pouvez arreter a tout moment avec le bouton **Stop** ou en fermant la fenetre Tkinter.

## Controle pas a pas

- **Accelerer** : ouvrez la bouche. Plus l'ouverture est grande, plus `pyautogui` maintient la touche d'acceleration (`z` par defaut).
- **Freiner** : relevez le menton (tete en arriere). Le systeme envoie la touche de frein (`s`).
- **Marche arriere** : baissez nettement la tete. La meme touche `s` est envoyee de facon continue.
- **Tourner** : regardez a gauche ou a droite. Un signal pulse reproduit un volant analogique, proportionnel au detournement de la tete.
- **Maintien automatique** : une logique de "cruise control" gere la repetition des touches pour eviter les a-coups.

Gardez la camera a hauteur des yeux, face a vous, et evitez le contre-jour pour de meilleurs resultats.

## Architecture du projet

```
camera -> CameraHandler -> SimpleHeadControlledDrive -> pyautogui -> jeu
                               |
                               v
                             DriveUI (Tkinter)
```

- `camera_handler.py` : detecte les cameras disponibles, configure la resolution et fournit les images.
- `simple_head_drive.py` : coeur du controle. Exploite MediaPipe pour extraire des points du visage, calcule des seuils, pilote les touches clavier.
- `app.py` : interface graphique, gestion de thread, affichage des evenements et pilotage du cycle de vie.
- `requirements.txt` : dependances Python a installer.

## Personnalisation rapide

- **Touches** : changez les attributs `forward_key`, `backward_key`, `left_key`, `right_key` lors de la creation de `SimpleHeadControlledDrive` (ligne de demarrage dans `app.py` ou bloc `__main__` dans `simple_head_drive.py`).
- **Camera** : passez `camera_override=<index>` a `SimpleHeadControlledDrive` ou fixez `camera_index` dans `CameraHandler`.
- **Calibration** : ajustez `calibration_seconds`, `reverse_threshold`, `steer_dead_zone` si besoin de plus de tolerance.
- **Mode de cruise** : la propriete `cruise_mode` accepte `continuous` ou `pulsed` pour modifier la facon d'envoyer la touche d'acceleration.

## Conseils et bonnes pratiques

- Laissez quelques secondes entre chaque mouvement pour que les seuils se stabilisent.
- Evitez les mouvements parasites (parler, rire) pendant la phase de calibration.
- Desactiver les raccourcis systeme conflictuels si une touche reste appuyee.
- Testez d'abord hors du jeu pour verifier que les touches envoyees correspondent a vos attentes.

## Aller plus loin

- Ajouter un profil clavier pour differents jeux ou layouts (QWERTY, manette virtuelle).
- Enregistrer les parametres de calibration pour eviter de recommencer a chaque session.
- Integrer des retours sonores pour confirmer les changements de mode (frein, reverse, cruise).

Bon pilotage et bon jeu !
