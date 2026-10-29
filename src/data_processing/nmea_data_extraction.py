import numpy as np
import matplotlib.pyplot as plt

def conversion_coord(coord, direction):
    # Convertit une coord NMEA en format décimal
    deg = int(float(coord) / 100)
    min = float(coord) - deg * 100
    decimal = deg + min / 60
    if direction in ['S', 'W']:
        decimal = -decimal
    return decimal

def data_extraction(file_name):
    positions = []

    with open(file_name, 'r') as file:
        for line in file:
            if line.startswith('$GPGGA'):
                champs = line.strip().split(',')
                if len(champs) > 5 and champs[2] and champs[4]:
                    lat = conversion_coord(champs[2], champs[3])
                    lon = conversion_coord(champs[4], champs[5])
                    positions.append((lat, lon))

    return positions

# Exemple d'utilisation
fichier_nmea = 'GPGGA.txt'  # remplace par ton vrai fichier
coordonnees = data_extraction(fichier_nmea)

# Affichage des positions
for lat, lon in coordonnees:
    print(f"Latitude: {lat:.6f}, Longitude: {lon:.6f}")


