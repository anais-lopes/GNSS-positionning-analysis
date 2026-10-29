# realtime_gps_satellites_inmemory.py

import pynmea2
import serial
import math
import time
from pathlib import Path

# === Paramètres ===
SERIAL_PORT      = 'COM3'                # À adapter pour votre GPS
BAUD_RATE        = 4800
HTML_FILE        = 'gps_satellites_trajectory.html'
EARTH_RADIUS     = 6371000.0             # Rayon terrestre en mètres
SAT_ALT          = 20200000.0            # Altitude simulée des satellites (mètres)
REFRESH_INTERVAL = 2                     # Intervalle d'acquisition en secondes

# Couleurs CSS pour GPS (PRN cycle palette)
COLOR_PALETTE = [
    '#FF0000', '#00FF00', '#0000FF', '#FFA500',
    '#800080', '#00FFFF', '#FFC0CB', '#FFFF00',
    '#008000', '#000080',
]

# Historique en mémoire pour cette session : { prn: [ (lon, lat, alt), ... ] }
sat_history = {}
# Palette index pour chaque nouveau PRN
sat_colors = {}

def geodetic_to_ecef(lat, lon, alt):
    φ, λ = math.radians(lat), math.radians(lon)
    r = EARTH_RADIUS + alt
    return (
        r * math.cos(φ) * math.cos(λ),
        r * math.cos(φ) * math.sin(λ),
        r * math.sin(φ)
    )

def ecef_to_geodetic(x, y, z):
    r = math.sqrt(x*x + y*y + z*z)
    return (
        math.degrees(math.asin(z/r)),
        math.degrees(math.atan2(y, x)),
        r - EARTH_RADIUS
    )

def topocentric_to_ecef(lat0, lon0, alt0, azim, elev):
    x0, y0, z0 = geodetic_to_ecef(lat0, lon0, alt0)
    az, el = math.radians(azim), math.radians(elev)
    e = math.cos(el)*math.sin(az)
    n = math.cos(el)*math.cos(az)
    u = math.sin(el)
    φ0, λ0 = math.radians(lat0), math.radians(lon0)
    x_dir = -math.sin(λ0)*e - math.sin(φ0)*math.cos(λ0)*n + math.cos(φ0)*math.cos(λ0)*u
    y_dir =  math.cos(λ0)*e - math.sin(φ0)*math.sin(λ0)*n + math.cos(φ0)*math.sin(λ0)*u
    z_dir =  math.cos(φ0)*n + math.sin(φ0)*u
    return x0 + x_dir*SAT_ALT, y0 + y_dir*SAT_ALT, z0 + z_dir*SAT_ALT

def parse_nmea(lines):
    """Retourne (observer, gps_positions) depuis liste de lignes NMEA brutes."""
    observer = None
    gps_positions = {}
    for raw in lines:
        line = raw.strip()
        if line.startswith('$GPGGA'):
            try:
                msg = pynmea2.parse(line)
                observer = (msg.latitude, msg.longitude, float(msg.altitude or 0.0))
            except pynmea2.ParseError:
                continue
        elif len(line)>6 and line[3:6]=='GSV' and line[1:3]=='GP':
            parts = line.split('*')[0].split(',')
            for i in range((len(parts)-4)//4):
                prn_s, elev_s, az_s, _ = parts[4+4*i:8+4*i]
                if not prn_s: continue
                try:
                    prn = int(prn_s)
                    az  = float(az_s or 0.0)
                    el  = float(elev_s or 0.0)
                except ValueError:
                    continue
                gps_positions[prn] = (az, el)
    return observer, gps_positions

def assign_color(prn):
    """Donne une couleur à un PRN si pas déjà."""
    if prn not in sat_colors:
        idx = len(sat_colors) % len(COLOR_PALETTE)
        sat_colors[prn] = COLOR_PALETTE[idx]
    return sat_colors[prn]

def insert_history(prn, lon, lat, alt):
    """Ajoute un point à l'historique du satellite."""
    sat_history.setdefault(prn, []).append((lon, lat, alt))

def generate_html(observer):
    """Construit le HTML de la session courante (observateur + trajectoires GPS)."""
    js = []
    # Observateur
    if observer:
        lat0, lon0, alt0 = observer
        js += [
            "var obs = viewer.entities.add({",
            f"  position: Cesium.Cartesian3.fromDegrees({lon0:.6f},{lat0:.6f},{alt0:.1f}),",
            "  point: { pixelSize: 12, color: Cesium.Color.RED }",
            "});", ""
        ]
    # Satellites
    for prn, traj in sat_history.items():
        color = assign_color(prn)
        pts = [f"Cesium.Cartesian3.fromDegrees({lon:.6f},{lat:.6f},{alt:.1f})" for lon,lat,alt in traj]
        # polyline
        js += [
            f"var line_{prn}=viewer.entities.add({{polyline:{{positions:[{','.join(pts)}],width:2,material:Cesium.Color.fromCssColorString('{color}')}}}});",
            ""
        ]
        # dernier point
        lon_l, lat_l, alt_l = traj[-1]
        js += [
            f"var pt_{prn}=viewer.entities.add({{position:Cesium.Cartesian3.fromDegrees({lon_l:.6f},{lat_l:.6f},{alt_l:.1f}),point:{{pixelSize:6,color:Cesium.Color.fromCssColorString('{color}')}}}});",
            ""
        ]

    html = [
        "<!DOCTYPE html>","<html><head><meta charset='UTF-8'><title>GPS Trajectoires</title>",
        "<script src='https://cesium.com/downloads/cesiumjs/releases/1.111/Build/Cesium/Cesium.js'></script>",
        "<link href='https://cesium.com/downloads/cesiumjs/releases/1.111/Build/Cesium/Widgets/widgets.css' rel='stylesheet'/>",
        "<style>html,body,#cesiumContainer{width:100%;height:100%;margin:0;padding:0;}#infoBox{position:absolute;top:10px;left:10px;background:rgba(255,255,255,0.8);padding:10px;border-radius:5px;}</style>",
        "</head><body>",
        "<div id='cesiumContainer'></div>",
        "<div id='infoBox'>GPS Trajectoires<button onclick='location.reload()'>Rafraîchir</button></div>",
        "<script>",
        "Cesium.Ion.defaultAccessToken='';",
        "var viewer=new Cesium.Viewer('cesiumContainer',{imageryProvider:new Cesium.OpenStreetMapImageryProvider(),baseLayerPicker:false,timeline:false,animation:false});",
    ]
    for line in js:
        html.append("  "+line)
    html += [
        "viewer.zoomTo(viewer.entities);",
        "</script></body></html>"
    ]
    Path(HTML_FILE).write_text("\n".join(html), encoding='utf-8')

def main():
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    try:
        while True:
            lines, t0 = [], time.time()
            while time.time()-t0 < REFRESH_INTERVAL:
                raw = ser.readline().decode('utf-8','ignore')
                if raw: lines.append(raw)
            obs, gps_pos = parse_nmea(lines)
            # si observer bon, on enregistre
            if obs and -90<obs[0]<90 and -180<obs[1]<180:
                insert_history(0, obs[1], obs[0], obs[2])
                for prn,(az,el) in gps_pos.items():
                    if 0<=az<360 and 0<=el<=90:
                        # conversion puis insert
                        x,y,z = topocentric_to_ecef(obs[0],obs[1],obs[2],az,el)
                        lat_s,lon_s,alt_s = ecef_to_geodetic(x,y,z)
                        insert_history(prn, lon_s, lat_s, alt_s)
            # génère page avec tout l'historique de session
            generate_html(obs)
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()

if __name__=='__main__':
    main()
