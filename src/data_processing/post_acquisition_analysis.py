import folium
import matplotlib.pyplot as plt
import math
import pynmea2
from datetime import datetime
import numpy as np

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # rayon terrestre (m)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# === PARSING DU FICHIER ===
fichier = "trames.txt"
positions = []
temps = []

with open(fichier, 'r') as f:
    for line in f:
        try:
            if line.startswith('$GPGGA'):
                msg = pynmea2.parse(line)
                if msg.latitude and msg.longitude and msg.gps_qual > 0:
                    positions.append((msg.latitude, msg.longitude))
                    t = datetime.combine(datetime.today(), msg.timestamp)
                    temps.append(t)
        except Exception:
            continue


if len(positions) < 3:
    print("⛔ Pas assez de données pour tracer la vitesse ou l'accélération.")


# --- Calcul vitesse (m/s) ---
distances = []
vitesses = []
vitesses_km_h = []
temps_sec = []
for i in range(1, len(positions)):
    dt = (temps[i] - temps[i - 1]).total_seconds()
    d = haversine(*positions[i - 1], *positions[i])
    if dt > 0:
        distances.append(d)
        vitesses.append(d / dt)
        vitesses_km_h.append(3.6*d/dt)
        temps_sec.append((temps[i] - temps[0]).total_seconds())

distance_totale = sum(distances)
vitesse_moyenne = np.mean(vitesses)

# --- Calcul accélération (m/s²) ---
accelerations = []
for i in range(1, len(vitesses)):
    dt = temps_sec[i] - temps_sec[i - 1]
    dv = vitesses[i] - vitesses[i - 1]
    if dt > 0:
        accelerations.append(dv / dt)

# --- Tracé de la carte ---
lat_moy = np.mean([p[0] for p in positions])
lon_moy = np.mean([p[1] for p in positions])
carte = folium.Map(location=[lat_moy, lon_moy], zoom_start=17)
folium.PolyLine(positions, color='red', weight=3).add_to(carte)
for lat, lon in positions:
    folium.CircleMarker([lat, lon], radius=3, color='blue', fill=True).add_to(carte)

# Ajouter info distance + vitesse
info_html = f"""
<div style="
    position: fixed; 
    top: 10px; 
    right: 10px; 
    z-index: 1000; 
    background-color: white; 
    padding: 10px; 
    border: 2px solid #333;
    border-radius: 8px;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
    font-family: Arial;
">
    <b>Distance parcourue :</b> {distance_totale:.4f} m<br>
    <b>Vitesse moyenne :</b> {vitesse_moyenne:.4f} m/s
    <b>Vitesse moyenne :</b> {vitesse_moyenne*3.6:.4f} km/h
</div>
"""

carte.get_root().html.add_child(folium.Element(info_html))
carte.save("carte_trajectoire.html")
print("✅ Carte enregistrée sous 'carte_trajectoire.html'")

# --- Tracé des courbes ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), sharex=True)

ax1.plot(temps_sec, vitesses_km_h, label="Vitesse (m/s)", color="blue")
ax1.set_ylabel("Vitesse (km/h)")
ax1.set_title("Vitesse en fonction du temps")
ax1.grid(True)

ax2.plot(temps_sec[1:], accelerations, label="Accélération (m/s²)", color="green")
ax2.set_ylabel("Accélération (m/s²)")
ax2.set_xlabel("Temps (s)")
ax2.set_title("Accélération en fonction du temps")
ax2.grid(True)

plt.tight_layout()
plt.show()
