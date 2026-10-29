# GNSS Systems: Data Processing & Performance Analysis
**ENSTA — Engineering Project | June 2025**

## English

### Overview
This project explored Global Navigation Satellite Systems (GNSS) through practical experiments, from decoding raw GPS data to evaluating positioning accuracy and visualizing satellite constellations in 3D.

### Key Features
- **NMEA data processing:** Decoded GPGGA and GPGSV messages to extract positioning and satellite information.
- **Real-time GPS tracking:** Developed Python scripts to display trajectories on interactive maps using Folium.
- **Motion analysis:** Computed travelled distance, instantaneous and average speed, and acceleration from GPS measurements.
- **Positioning performance evaluation:** Compared a consumer USB GPS receiver using Single Point Positioning (SPP) with a Real-Time Kinematic (RTK) receiver.
- **3D satellite visualization:** Reconstructed satellite positions from NMEA data and visualized GNSS constellations using CesiumJS.

### Results
- The USB GPS receiver exhibited positioning errors of several metres, with variable accuracy depending on satellite geometry.
- The RTK receiver achieved a mean positioning error below **30 cm** in static measurements.
- HDOP analysis helped explain the relationship between satellite geometry and positioning quality.
- Experiments highlighted the impact of degraded signal reception, particularly near or inside buildings.

### Technologies & Tools
`Python` · `Folium` · `Matplotlib` · `CesiumJS` · `NMEA` · `GNSS` · `GPS` · `RTK`

### Skills Developed
GNSS data processing · Geospatial visualization · Measurement analysis · Error characterization · Experimental validation

---

## Français

### Présentation
Ce projet avait pour objectif d'étudier les systèmes mondiaux de navigation par satellite (GNSS) à travers des expérimentations pratiques, du décodage des données GPS brutes à l'évaluation de la précision du positionnement et à la visualisation 3D des constellations satellitaires.

### Fonctionnalités principales
- **Traitement des données NMEA :** Décodage des trames GPGGA et GPGSV pour extraire les informations de positionnement et sur les satellites.
- **Suivi GPS en temps réel :** Développement de scripts Python pour afficher des trajectoires sur des cartes interactives avec Folium.
- **Analyse du mouvement :** Calcul de la distance parcourue, des vitesses instantanée et moyenne, et de l'accélération à partir des mesures GPS.
- **Évaluation des performances de positionnement :** Comparaison d'un récepteur GPS USB grand public utilisant le positionnement absolu (SPP) avec un récepteur RTK.
- **Visualisation 3D des satellites :** Reconstruction des positions satellitaires à partir des trames NMEA et visualisation des constellations GNSS avec CesiumJS.

### Résultats
- Le récepteur GPS USB présentait des erreurs de positionnement de plusieurs mètres, avec une précision variable selon la géométrie satellitaire.
- Le récepteur RTK a atteint une erreur moyenne inférieure à **30 cm** lors des mesures statiques.
- L'analyse du HDOP a permis d'étudier le lien entre la géométrie des satellites et la qualité du positionnement.
- Les expérimentations ont mis en évidence l'effet d'une réception dégradée du signal, notamment à proximité ou à l'intérieur des bâtiments.

### Technologies et outils
`Python` · `Folium` · `Matplotlib` · `CesiumJS` · `NMEA` · `GNSS` · `GPS` · `RTK`

### Compétences développées
Traitement de données GNSS · Visualisation géospatiale · Analyse métrologique · Caractérisation des erreurs · Validation expérimentale

---

**Project type:** Academic group project  
**Institution:** ENSTA  
**Date:** June 2025
