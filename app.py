from flask import Flask, jsonify, request

app = Flask(__name__)

positions = {}

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
            border-radius:10px; width:310px;
            box-shadow:0 0 10px #555;
        }
        .small { font-size: 13px; color: #444; }
        .sos { color:red; font-weight:bold; }
    </style>
    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
</head>
<body>

<div id="panel">
    <h3>ADRN Centrale</h3>
    <p><b>Stato:</b> attiva</p>
    <p><b>Target:</b> tracking realtime</p>
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

L.marker([45.6983, 9.6773]).addTo(map)
.bindPopup('Centrale ADRN - Bergamo')
.openPopup();

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
            let sos = p.sos || false;

            let popup = "<b>" + id + "</b><br>" +
                        "Tipo: " + tipo + "<br>" +
                        "Lat: " + lat + "<br>" +
                        "Lon: " + lon + "<br>" +
                        "Precisione: " + accuracy + " m<br>" +
                        "Velocità: " + speed + "<br>" +
                        "Direzione: " + heading + "<br>" +
                        (sos ? "<b style='color:red'>SOS ATTIVO</b>" : "");

            if (markers[id]) {
                markers[id].setLatLng([lat, lon]);
                markers[id].bindPopup(popup);
            } else {
                markers[id] = L.marker([lat, lon]).addTo(map).bindPopup(popup);
            }

            testo += "<b>" + id + "</b> - " + tipo + "<br>" +
                     "Lat: " + lat + "<br>" +
                     "Lon: " + lon + "<br>" +
                     "Precisione: " + accuracy + " m<br>" +
                     (sos ? "<span class='sos'>SOS ATTIVO</span><br>" : "") +
                     "<br>";
        });

        document.getElementById("lista").innerHTML =
            testo || "In attesa coordinate...";
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
            sos: sos
        }})
    }})
    .then(r => r.json())
    .then(data => {{
        document.getElementById("stato").innerHTML =
        "TRACKING ATTIVO<br>" +
        "Lat: " + pos.coords.latitude + "<br>" +
        "Lon: " + pos.coords.longitude + "<br>" +
        "Precisione: " + Math.round(pos.coords.accuracy) + " m";
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

    positions[target_id] = {
        "lat": data.get("lat"),
        "lon": data.get("lon"),
        "tipo": data.get("tipo", "disperso"),
        "accuracy": data.get("accuracy"),
        "speed": data.get("speed"),
        "heading": data.get("heading"),
        "sos": data.get("sos", False)
    }

    return jsonify({
        "status": "ok",
        "id": target_id,
        "data": positions[target_id]
    })

@app.route("/api/positions")
def get_positions():
    return jsonify(positions)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
