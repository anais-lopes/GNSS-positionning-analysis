import folium
import pynmea2
import serial
import serial.tools.list_ports
import time
import webbrowser
import os

# === Paramètres ===
SERIAL_PORT = 'COM3'          # Mets ici ton port réel
BAUD_RATE = 4800
MAP_FILE = 'map.html'
REFRESH_DELAY = 0.1  # secondes

# === Initialisation série ===
ser = serial.Serial(SERIAL_PORT, baudrate=BAUD_RATE, timeout=1)

# === Liste des positions ===
positions = []

# === Boucle principale ===
print("Lecture des trames GPS et mise à jour de la carte...")

while True:
    try:
        line = ser.readline().decode('utf-8', errors='ignore').strip()

        if line.startswith('$GPGGA'):
            gga = pynmea2.parse(line)
            lat = gga.latitude
            lon = gga.longitude
            print(f"Position : {lat:.6f}, {lon:.6f}")
            positions.append((lat, lon))

            # Création de la carte
            map_center = [lat, lon]
            m = folium.Map(location=map_center, zoom_start=18)

            # Trace des points
            for i, (lt, ln) in enumerate(positions):
                folium.CircleMarker(
                    location=(lt, ln),
                    radius=3,
                    color='blue',
                    fill=True,
                    fill_color='blue',
                    popup=f"Point {i+1}"
                ).add_to(m)

            # Tracé de la trajectoire
            if len(positions) >= 2:
                folium.PolyLine(
                    locations=positions,
                    color='red',
                    weight=3,
                    opacity=0.8,
                    popup="Trajectoire"
                ).add_to(m)

            # Sauvegarde de la carte
            m.save(MAP_FILE)

            # Ouvrir une fois dans le navigateur
            if not os.path.exists('.map_opened'):
                webbrowser.open('file://' + os.path.realpath(MAP_FILE))
                open('.map_opened', 'w').close()

            # Pause
            time.sleep(REFRESH_DELAY)

    except KeyboardInterrupt:
        print("Arrêt manuel.")
        break
    except Exception as e:
        print("Erreur : ", e)

