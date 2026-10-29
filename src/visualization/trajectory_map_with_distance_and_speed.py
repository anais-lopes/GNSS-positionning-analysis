import folium
import pynmea2
import serial
import serial.tools.list_ports
import time
import webbrowser
import os
import math

# === Paramètres ===
SERIAL_PORT = 'COM3'          # Mets ici ton port réel
BAUD_RATE = 4800
MAP_FILE = 'map.html'
TXT_FILE = 'trames.txt'
REFRESH_DELAY = 0.1  # secondes

# === Initialisation série ===
ser = serial.Serial(SERIAL_PORT, baudrate=BAUD_RATE, timeout=1)

# === Initialisation ===
positions = []
total_distance = 0.0
last_time = None

# === Fonction Haversine ===
def haversine(lat1, lon1, lat2, lon2):
    R = 6371e3  # Terre en mètres
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = math.sin(d_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# === Boucle principale ===
print("Lecture des trames GPS et mise à jour de la carte...")

with open(TXT_FILE, 'a') as txt_file:
    while True:
        try:
            line = ser.readline().decode('utf-8', errors='ignore').strip()

            # Enregistre dans le fichier texte
            if line:
                txt_file.write(line + '\n')
                txt_file.flush()

            if line.startswith('$GPGGA'):
                gga = pynmea2.parse(line)
                lat = gga.latitude
                lon = gga.longitude
                current_time = time.time()
                print(f"Position : {lat:.6f}, {lon:.6f}")
                positions.append((lat, lon))

                # Calcul distance
                if len(positions) >= 2:
                    d = haversine(positions[-2][0], positions[-2][1], lat, lon)
                    total_distance += d

                # Calcul vitesse
                if last_time is not None:
                    elapsed_time = current_time - last_time
                    speed = (d / elapsed_time) * 3.6  # m/s en km/h
                else:
                    speed = 0.0
                last_time = current_time

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

                # Ajout des infos dans HTML
                html_info = f"""
                <div style='position: fixed; top: 10px; left: 10px; background: white; padding: 10px; z-index: 1000; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.3);'>
                    <strong>Distance totale :</strong> {total_distance/1000:.2f} km<br>
                    <strong>Vitesse :</strong> {speed:.2f} km/h
                </div>
                """
                m.get_root().html.add_child(folium.Element(html_info))

                # Sauvegarde de la carte
                m.save(MAP_FILE)

                # Ouvrir une fois dans le navigateur
                if not os.path.exists('.map_opened'):
                    webbrowser.open('file://' + os.path.realpath(MAP_FILE))
                    open('.map_opened', 'w').close()

                time.sleep(REFRESH_DELAY)

        except KeyboardInterrupt:
            print("Arrêt manuel.")
            break
        except Exception as e:
            print("Erreur : ", e)
