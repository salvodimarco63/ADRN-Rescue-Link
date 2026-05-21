from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)

positions = {}
history = {}

@app.route("/")
def home():
    return """
    <h1>ADRN Centrale Operativa</h1>
    <p>Server attivo.</p>
    <p><a href="/centrale">Apri Centrale ADRN</a></p>
    """

@app.route("/centrale")
def centrale():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>ADRN Centrale</title>
    <meta charset="utf-8" />
    <style>
        body { margin:0; font-family: Arial; }
        #map { height:100vh; width:100%; }
        #panel {
            position:absolute; top:10px; right:10px;
            background:white; padding:12px; z-index:999;
            border-radius:10px; width:340px;
            box-shadow:0 0 10px #555;
        }
        .small { font-size:13px; color:#333; }
        .sos { color:red; font-weight:bold; font-size:16px; }
    </style>
    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
</head>
<body>

<div id="panel">
    <h3>ADRN Centrale SAR</h3>
    <p><b>Stato:</b> operativa</p>
    <p><b>Modalità:</b> tracking realtime</p>
    <div id="lista" class="small">In attesa coordinate...</div>
</div>

<div id="map"></div>

<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
<script>
var map = L.map('map').setView([45.6983, 9.6773], 13);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19
}).addTo(map);

var markers = {};
var trails = {};
var autoFollow = true;

L.marker([45.6983, 9.6773]).addTo(map)
.bindPopup('Centrale ADRN - Bergamo')
.openPopup();

function creaIcona(sos) {
    return L.icon({
        iconUrl: sos
            ? 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png'
            : 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });
}

function aggiornaMappa() {
    fetch('/api/positions')
    .then(response => response.json())
    .then(data => {
        let testo = "";

        Object.keys(data).forEach(id => {
            let p = data[id];

            let lat = p.lat;
            let lon = p.lon;
            let tipo = p.tipo || "target";
            let accuracy = p.accuracy || "n.d.";
            let speed = p.speed || "n.d.";
            let heading = p.heading || "n.d.";
            let battery = p.battery || "n.d.";
            let sos = p.sos || false;
            let timestamp = p.timestamp || "n.d.";

            let popup = "<b>" + id + "</b><br>" +
                        "Tipo: " + tipo + "<br>" +
                        "Lat: " + lat + "<br>" +
                        "Lon: " + lon + "<br>" +
                        "Precisione: " + accuracy + " m<br>" +
                        "Velocità: " + speed + "<br>" +
                        "Direzione: " + heading + "<br>" +
                        "Batteria: " + battery + "%<br>" +
                        "Ultimo update: " + timestamp + "<br>" +
                        (sos ? "<b style='color:red'>SOS ATTIVO</b>" : "");

            if (markers[id]) {
                markers[id].setLatLng([lat, lon]);
                markers[id].setIcon(creaIcona(sos));
                markers[id].bindPopup(popup);
            } else {
                markers[id] = L.marker([lat, lon], {
                    icon: creaIcona(sos)
                }).addTo(map).bindPopup(popup);
            }

            if (autoFollow) {
                map.setView([lat, lon], 16);
            }

            if (sos) {
                markers[id].openPopup();
            }

            testo += "<b>" + id + "</b> - " + tipo + "<br>" +
                     "Lat: " + lat + "<br>" +
                     "Lon: " + lon + "<br>" +
                     "Precisione: " + accuracy + " m<br>" +
                     "Batteria: " + battery + "%<br>" +
                     "Ultimo update: " + timestamp + "<br>" +
                     (sos ? "<span class='sos'>SOS ATTIVO</span><br>" : "") +
                     "<br>";
        });

        document.getElementById("lista").innerHTML =
            testo || "In attesa coordinate...";
    });

    fetch('/api/history')
    .then(r => r.json())
    .then(storico => {
        Object.keys(storico).forEach(id => {
            if (trails[id]) {
                map.removeLayer(trails[id]);
            }

            trails[id] = L.polyline(storico[id], {
                color: 'red',
                weight: 4
            }).addTo(map);
        });
    });
}

setInterval(aggiornaMappa, 2000);
aggiornaMappa();
</script>

</body>
</html>
"""

@app.route("/localizza/<target_id>")
def localizza(target_id):
    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>ADRN Localizzazione</title>
</head>

<body style="font-family:Arial; text-align:center; padding:30px;">

<h2>ADRN Rescue Link</h2>

<p>Premi il pulsante e consenti l’uso del GPS.</p>

<button onclick="avviaTracking()" style="
padding:20px;
font-size:22px;
border:none;
border-radius:12px;
background:#d62828;
color:white;
">
AVVIA TRACKING GPS
</button>

<br><br>

<button onclick="inviaSOS()" style="
padding:16px;
font-size:20px;
border:none;
border-radius:12px;
background:#ffb703;
color:black;
">
SOS
</button>

<p id="stato">In attesa...</p>

<script>
let watchId = null;
let batteria = "n.d.";

if (navigator.getBattery) {{
    navigator.getBattery().then(function(battery) {{
        batteria = Math.round(battery.level * 100);
    }});
}}

function inviaPosizione(pos, sos=false) {{

    fetch('/api/position', {{
        method:'POST',
        headers:{{
            'Content-Type':'application/json'
        }},
        body: JSON.stringify({{
            id: '{target_id}',
            tipo: 'disperso',
            lat: pos.coords.latitude,
            lon: pos.coords.longitude,
            accuracy: pos.coords.accuracy,
            speed: pos.coords.speed,
            heading: pos.coords.heading,
            battery: batteria,
            sos: sos
        }})
    }})
    .then(r => r.json())
    .then(data => {{
        document.getElementById("stato").innerHTML =
        "TRACKING ATTIVO<br>" +
        "Lat: " + pos.coords.latitude + "<br>" +
        "Lon: " + pos.coords.longitude + "<br>" +
        "Precisione: " + Math.round(pos.coords.accuracy) + " m<br>" +
        "Batteria: " + batteria + "%";
    }});
}}

function avviaTracking() {{
    if (!navigator.geolocation) {{
        document.getElementById("stato").innerHTML = "GPS non supportato";
        return;
    }}

    watchId = navigator.geolocation.watchPosition(
        function(pos) {{
            inviaPosizione(pos, false);
        }},
        function(err) {{
            document.getElementById("stato").innerHTML =
            "GPS non autorizzato o non disponibile";
        }},
        {{
            enableHighAccuracy: true,
            maximumAge: 0,
            timeout: 10000
        }}
    );
}}

function inviaSOS() {{
    navigator.geolocation.getCurrentPosition(function(pos) {{
        inviaPosizione(pos, true);
        document.getElementById("stato").innerHTML = "SOS INVIATO";
    }});
}}
</script>

</body>
</html>
"""

@app.route("/api/position", methods=["POST"])
def save_position():
    data = request.json
    target_id = data.get("id", "target-1")

    posizione = {
        "lat": data.get("lat"),
        "lon": data.get("lon"),
        "tipo": data.get("tipo", "disperso"),
        "accuracy": data.get("accuracy"),
        "speed": data.get("speed"),
        "heading": data.get("heading"),
        "battery": data.get("battery"),
        "sos": data.get("sos", False),
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }

    positions[target_id] = posizione

    if target_id not in history:
        history[target_id] = []

    history[target_id].append([
        posizione["lat"],
        posizione["lon"]
    ])

    return jsonify({
        "status": "ok",
        "id": target_id,
        "data": posizione
    })

@app.route("/api/history")
def get_history():
    return jsonify(history)

@app.route("/api/positions")
def get_positions():
    return jsonify(positions)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
