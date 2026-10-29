# realtime_satellites_globe_trajectory.py

import pynmea2
import serial
import math
import time
from pathlib import Path

# === Paramètres ===
SERIAL_PORT      = 'COM3'                # À adapter pour ton GPS
BAUD_RATE        = 4800
HTML_FILE        = 'realtime_satellites_globe.html'
EARTH_RADIUS     = 6371000.0             # Rayon terrestre (m)
SAT_ALT          = 20200000.0            # Altitude simulée des satellites (m)
REFRESH_INTERVAL = 2                     # Intervalle d'acquisition (s)

# Couleurs par constellation (Cesium.Color)
CONST_COLORS = {
    'GP': 'Cesium.Color.BLUE',    # GPS
    'GL': 'Cesium.Color.RED',     # GLONASS
    'GA': 'Cesium.Color.GREEN',   # Galileo
    'GB': 'Cesium.Color.ORANGE',  # BeiDou
    'GI': 'Cesium.Color.PURPLE',  # IRNSS
    'GN': 'Cesium.Color.WHITE',   # Mixte/Autres
}

# Historique des positions :
# clé = (talker, prn), valeur = liste de tuples (lon, lat, alt)
sat_history = {}

def parse_nmea_lines(lines):
    """
    Analyse une liste de lignes NMEA :
      - observer = (lat, lon, alt) depuis la dernière trame $GPGGA
      - current_positions = {(talker, prn): (azim, elev), ...} depuis toutes les trames $?GSV
    """
    observer = None
    current_positions = {}

    for raw_line in lines:
        line = raw_line.strip()
        # === Observer (GPGGA) ===
        if line.startswith('$GPGGA'):
            try:
                msg = pynmea2.parse(line)
                lat0 = msg.latitude
                lon0 = msg.longitude
                alt0 = float(msg.altitude) if msg.altitude not in ('', None) else 0.0
                observer = (lat0, lon0, alt0)
            except pynmea2.ParseError:
                continue

        # === Satellites (GPGSV, etc.) ===
        elif len(line) > 6 and line[3:6] == 'GSV':
            talker = line[1:3]  # ex. "GP", "GL", "GA", "GB", etc.
            sentence = line.split('*')[0]
            parts = sentence.split(',')
            fields = parts[4:]
            nb_sat = len(fields) // 4
            for i in range(nb_sat):
                prn_str  = fields[4*i + 0]
                elev_str = fields[4*i + 1]
                azim_str = fields[4*i + 2]
                if not prn_str:
                    continue
                try:
                    prn = int(prn_str)
                    elev = float(elev_str) if elev_str else 0.0
                    azim = float(azim_str) if azim_str else 0.0
                except ValueError:
                    continue
                key = (talker, prn)
                current_positions[key] = (azim, elev)

    return observer, current_positions

def geodetic_to_ecef(lat, lon, alt):
    """
    Convertit (lat [°], lon [°], alt [m]) -> (X, Y, Z) ECEF (m), modèle sphérique.
    """
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    r = EARTH_RADIUS + alt
    x = r * math.cos(lat_rad) * math.cos(lon_rad)
    y = r * math.cos(lat_rad) * math.sin(lon_rad)
    z = r * math.sin(lat_rad)
    return x, y, z

def ecef_to_geodetic(x, y, z):
    """
    Convertit (X, Y, Z) ECEF -> (lat [°], lon [°], alt [m]), modèle sphérique.
    """
    r = math.sqrt(x*x + y*y + z*z)
    lat = math.degrees(math.asin(z / r))
    lon = math.degrees(math.atan2(y, x))
    alt = r - EARTH_RADIUS
    return lat, lon, alt

def topocentric_to_ecef(lat0, lon0, alt0, azim, elev):
    """
    Convertit un vecteur topocentrique (azim [°], elev [°]) -> ECEF (X, Y, Z),
    en positionnant le satellite à distance fixe SAT_ALT depuis l'observateur (lat0, lon0, alt0).
    """
    # 1) Position de l'observateur en ECEF
    x0, y0, z0 = geodetic_to_ecef(lat0, lon0, alt0)

    # 2) Calcul ENU unitaire
    az_rad = math.radians(azim)
    el_rad = math.radians(elev)
    e = math.cos(el_rad) * math.sin(az_rad)   # East
    n = math.cos(el_rad) * math.cos(az_rad)   # North
    u = math.sin(el_rad)                      # Up

    # 3) Rotation ENU -> ECEF
    lat0_rad = math.radians(lat0)
    lon0_rad = math.radians(lon0)
    x_dir = (
        - math.sin(lon0_rad) * e
        - math.sin(lat0_rad) * math.cos(lon0_rad) * n
        + math.cos(lat0_rad) * math.cos(lon0_rad) * u
    )
    y_dir = (
        + math.cos(lon0_rad) * e
        - math.sin(lat0_rad) * math.sin(lon0_rad) * n
        + math.cos(lat0_rad) * math.sin(lon0_rad) * u
    )
    z_dir = (
        + math.cos(lat0_rad) * n
        + math.sin(lat0_rad) * u
    )

    # 4) Position du satellite en coordonnées ECEF
    x_sat = x0 + x_dir * SAT_ALT
    y_sat = y0 + y_dir * SAT_ALT
    z_sat = z0 + z_dir * SAT_ALT
    return x_sat, y_sat, z_sat

def generate_html(observer, sat_current):
    """
    Construit le fichier HTML (CesiumJS) :
      - Si pas d'observateur, affiche simplement un message + bouton Rafraîchir
      - Sinon, trace l'observateur en rouge, puis pour chaque satellite :
        • une polyligne de sa trajectoire passée
        • un point à sa position la plus récente
      - Bouton Rafraîchir pour recharger manuellement
    """
    # Si pas d'observateur, on génère du HTML minimaliste
    if observer is None:
        html_min = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "  <meta charset='UTF-8' />",
            "  <title>Globe 3D - Pas de position</title>",
            "</head>",
            "<body>",
            "  <h3>Aucune position GPGGA reçue.</h3>",
            "  <button onclick='location.reload()'>Rafraîchir</button>",
            "</body>",
            "</html>"
        ]
        Path(HTML_FILE).write_text("\n".join(html_min), encoding='utf-8')
        return

    lat0, lon0, alt0 = observer

    # 1) JS pour placer l'observateur (rouge)
    observer_js_lines = [
        "var observer = viewer.entities.add({",
        f"    position: Cesium.Cartesian3.fromDegrees({lon0:.6f}, {lat0:.6f}, {alt0:.1f}),",
        "    point: { pixelSize: 12, color: Cesium.Color.RED }",
        "});",
        ""
    ]
    observer_js = "\n".join(observer_js_lines)

    # 2) Mise à jour de l'historique des trajectoires
    for key, (azim, elev) in sat_current.items():
        x_sat, y_sat, z_sat = topocentric_to_ecef(lat0, lon0, alt0, azim, elev)
        lat_sat, lon_sat, alt_sat = ecef_to_geodetic(x_sat, y_sat, z_sat)
        sat_history.setdefault(key, []).append((lon_sat, lat_sat, alt_sat))

    # 3) JS pour chaque satellite : polyline (traj) + point (dernier)
    sats_js_lines = []
    for (talker, prn), traj in sat_history.items():
        color = CONST_COLORS.get(talker, 'Cesium.Color.WHITE')
        # a) Positions pour la polyline
        coords_js = []
        for (lon_sat, lat_sat, alt_sat) in traj:
            coords_js.append(f"Cesium.Cartesian3.fromDegrees({lon_sat:.6f}, {lat_sat:.6f}, {alt_sat:.1f})")
        # b) JS polyline
        polyline_js = [
            f"var line_{talker}{prn} = viewer.entities.add({{",
            "    polyline: {",
            "        positions: [",
            "            " + ",\n            ".join(coords_js),
            "        ],",
            "        width: 2,",
            f"        material: {color}",
            "    }",
            "});",
            ""
        ]
        sats_js_lines.extend(polyline_js)
        # c) JS point pour la position la plus récente
        lon_last, lat_last, alt_last = traj[-1]
        point_js = [
            f"var sat_{talker}{prn}_pt = viewer.entities.add({{",
            f"    position: Cesium.Cartesian3.fromDegrees({lon_last:.6f}, {lat_last:.6f}, {alt_last:.1f}),",
            f"    point: {{ pixelSize: 6, color: {color} }}",
            "});",
            ""
        ]
        sats_js_lines.extend(point_js)

    sats_js = "\n".join(sats_js_lines)

    # 4) Construction finale du HTML, ligne par ligne
    html_lines = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "  <meta charset='UTF-8' />",
        "  <title>Globe 3D - Sat Trajectoires</title>",
        "  <script src='https://cesium.com/downloads/cesiumjs/releases/1.111/Build/Cesium/Cesium.js'></script>",
        "  <link href='https://cesium.com/downloads/cesiumjs/releases/1.111/Build/Cesium/Widgets/widgets.css' rel='stylesheet' />",
        "  <style>",
        "    html, body, #cesiumContainer {",
        "      width: 100%; height: 100%; margin: 0; padding: 0; overflow: hidden;",
        "    }",
        "    #infoBox {",
        "      position: absolute; top: 10px; left: 10px; background: rgba(255,255,255,0.9);",
        "      padding: 10px; border-radius: 5px; font-family: sans-serif; z-index: 999;",
        "    }",
        "  </style>",
        "</head>",
        "<body>",
        "  <div id='cesiumContainer'></div>",
        "  <div id='infoBox'>",
        "    Observateur (rouge) – Trajectoires satellites par constellation",
        "    &nbsp;&nbsp;<button onclick='location.reload()'>Rafraîchir</button>",
        "  </div>",
        "  <script>",
        "    Cesium.Ion.defaultAccessToken = '';",
        "    var viewer = new Cesium.Viewer('cesiumContainer', { imageryProvider: new Cesium.OpenStreetMapImageryProvider(), baseLayerPicker: false, timeline: false, animation: false });",
        "    // 1) Observateur",
        f"    {observer_js.strip()}",
        "    // 2) Trajectoires et points satellites",
        f"    {sats_js.strip()}",
        "    // 3) Zoom pour englober tous les points",
        "    viewer.zoomTo(viewer.entities);",
        "  </script>",
        "</body>",
        "</html>"
    ]

    Path(HTML_FILE).write_text("\n".join(html_lines), encoding='utf-8')

def main():
    # Ouverture du port série
    ser = serial.Serial(SERIAL_PORT, baudrate=BAUD_RATE, timeout=1)
    print("Lecture des trames GPS en temps réel... (Ctrl+C pour arrêter)")

    try:
        while True:
            # Collecte les lignes reçues pendant REFRESH_INTERVAL secondes
            start = time.time()
            lines = []
            while time.time() - start < REFRESH_INTERVAL:
                raw = ser.readline().decode('utf-8', errors='ignore')
                if raw:
                    lines.append(raw)

            # Extraction position observateur + positions satellites
            observer, sat_current = parse_nmea_lines(lines)
            # Mise à jour de l'historique et génération du HTML
            generate_html(observer, sat_current)

            # Le navigateur n'actualise que sur clic
    except KeyboardInterrupt:
        print("Arrêt manuel.")
    finally:
        ser.close()

if __name__ == '__main__':
    main()
