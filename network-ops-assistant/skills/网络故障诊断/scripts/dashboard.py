#!/usr/bin/env python3
"""校园网 SNMP 仪表盘 v2 - 含实时流量监控"""

import subprocess, json, re, http.server, threading, time

SWITCH_IP = "172.16.20.217"
COMMUNITY = "Monitor123"
POLL_INTERVAL = 15
PORT = 8099

cache = {"data": None, "prev": {}}

def snmp_walk(oid):
    cmd = ["snmpwalk", "-v2c", "-c", COMMUNITY, "-t", "5", "-r", "2", SWITCH_IP, oid]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    return result.stdout.strip().split("\n") if result.stdout else []

def collect():
    ports = {}
    for line in snmp_walk("1.3.6.1.2.1.2.2.1.2"):
        m = re.search(r'(\d+) = STRING: "(.+)"', line)
        if m: ports[m.group(1)] = {"name": m.group(2), "index": m.group(1)}
    for line in snmp_walk("1.3.6.1.2.1.31.1.1.1.18"):
        m = re.search(r'(\d+) = STRING: "(.+)"', line)
        if m and m.group(1) in ports: ports[m.group(1)]["desc"] = m.group(2)
    for line in snmp_walk("1.3.6.1.2.1.2.2.1.8"):
        m = re.search(r'(\d+) = INTEGER: (\d+)', line)
        if m and m.group(1) in ports: ports[m.group(1)]["up"] = (m.group(2) == "1")
    for line in snmp_walk("1.3.6.1.2.1.2.2.1.5"):
        m = re.search(r'(\d+) = Gauge32: (\d+)', line)
        if m and m.group(1) in ports: ports[m.group(1)]["speed"] = int(m.group(2))
    for line in snmp_walk("1.3.6.1.2.1.2.2.1.14"):
        m = re.search(r'(\d+) = Counter32: (\d+)', line)
        if m and m.group(1) in ports: ports[m.group(1)]["errors"] = int(m.group(2))
    for line in snmp_walk("1.3.6.1.2.1.31.1.1.1.6"):
        m = re.search(r'(\d+) = Counter64: (\d+)', line)
        if m and m.group(1) in ports: ports[m.group(1)]["in_bytes"] = int(m.group(2))
    for line in snmp_walk("1.3.6.1.2.1.31.1.1.1.10"):
        m = re.search(r'(\d+) = Counter64: (\d+)', line)
        if m and m.group(1) in ports: ports[m.group(1)]["out_bytes"] = int(m.group(2))
    return ports

def poll():
    global cache
    while True:
        try:
            now = time.time()
            ports = collect()
            sys_name = subprocess.run(
                ["snmpget", "-v2c", "-c", COMMUNITY, SWITCH_IP, "1.3.6.1.2.1.1.5.0"],
                capture_output=True, text=True, timeout=5
            ).stdout.strip().split(": ")[-1].strip('"')

            # Calculate traffic rates
            prev = cache.get("prev", {})
            for p in ports.values():
                idx = p["index"]
                if idx in prev and "in_bytes" in p:
                    dt = now - prev[idx]["ts"]
                    if dt > 0:
                        p["in_rate"] = int((p["in_bytes"] - prev[idx].get("in_bytes", 0)) / dt)
                        p["out_rate"] = int((p["out_bytes"] - prev[idx].get("out_bytes", 0)) / dt)
                    else:
                        p["in_rate"] = p["out_rate"] = 0
                else:
                    p["in_rate"] = p["out_rate"] = 0

            # Save snapshot for next calc
            cache["prev"] = {p["index"]: {"in_bytes": p.get("in_bytes", 0), "out_bytes": p.get("out_bytes", 0), "ts": now} for p in ports}

            cache["data"] = {
                "hostname": sys_name, "ip": SWITCH_IP,
                "ports": list(ports.values()),
                "time": time.strftime("%H:%M:%S")
            }
        except Exception as e:
            cache["data"] = {"hostname": "Error", "ip": SWITCH_IP, "ports": [], "time": time.strftime("%H:%M:%S"), "error": str(e)}
        time.sleep(POLL_INTERVAL)

HTML = r"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>校园网监控 - """ + SWITCH_IP + r"""</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui,sans-serif;background:#0f1923;color:#e0e0e0;padding:16px}
.header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:8px}
.header h1{font-size:22px;color:#fff}.header .info{font-size:12px;color:#8a9ba8}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:8px}
.card{border-radius:8px;padding:10px 12px;background:#1a2a38;border-left:4px solid #555}
.card.up{border-left-color:#15b371}.card.down{background:#2a1515;border-left-color:#e74c3c}
.card .row1{display:flex;justify-content:space-between;align-items:flex-start}
.card .port{font-size:11px;color:#8a9ba8;font-family:monospace}
.card .status{font-size:10px;padding:2px 6px;border-radius:3px;font-weight:700}
.card .status.up{background:#15b37133;color:#15b371}.card .status.down{background:#e74c3c33;color:#e74c3c}
.card .desc{font-size:13px;color:#fff;margin:3px 0;font-weight:600}
.card .meta{font-size:10px;color:#6b7c8a;display:flex;justify-content:space-between;margin:3px 0}
.card .speed{color:#48aff0}.card .err{color:#e67e22}
.traffic-bar{display:flex;gap:2px;margin-top:4px;height:6px;border-radius:3px;overflow:hidden;background:#0f1923}
.traffic-bar .in{background:#48aff0;transition:width .5s}.traffic-bar .out{background:#15b371;transition:width .5s}
.traffic-text{font-size:10px;color:#5a6b78;margin-top:2px;display:flex;justify-content:space-between}
.summary{display:flex;gap:12px;margin-bottom:12px;flex-wrap:wrap}
.summary .stat{background:#1a2a38;padding:8px 14px;border-radius:8px;text-align:center}
.summary .stat .num{font-size:24px;font-weight:700}
.summary .stat .label{font-size:10px;color:#8a9ba8}
.summary .up .num{color:#15b371}.summary .down .num{color:#e74c3c}
.refresh{font-size:12px;color:#48aff0;cursor:pointer;user-select:none}
.refresh:hover{text-decoration:underline}
@media(max-width:600px){.grid{grid-template-columns:1fr}}
</style></head><body>
<div class="header"><div><h1 id="hostname">Loading...</h1><div class="info" id="updateTime"></div></div>
<div><span class="refresh" onclick="fetchData()">&#x1f504; 刷新</span></div></div>
<div class="summary" id="summary"></div><div class="grid" id="grid"></div>
<script>
function fmt(bps){if(bps>=1e9)return (bps/1e9).toFixed(1)+'G';if(bps>=1e6)return (bps/1e6).toFixed(1)+'M';
if(bps>=1e3)return (bps/1e3).toFixed(0)+'K';return bps+' '}
function fmtB(bps){return fmt(bps*8)+'bps'}
function barPct(rate,max){if(max<=0)return 0;return Math.min(100,rate/max*100)}
async function fetchData(){
try{const r=await fetch('/api/ports');const d=await r.json();render(d)}catch(e){}
}
function render(d){
document.getElementById('hostname').innerHTML='&#x1f5e5; '+d.hostname;
document.getElementById('updateTime').textContent=d.ip+' | '+d.time+' | 每'+""" + str(POLL_INTERVAL) + r"""秒刷新';
const ports=d.ports||[];
const up=ports.filter(p=>p.up).length,down=ports.filter(p=>!p.up).length;
let maxRate=1;ports.forEach(p=>{if(p.in_rate>maxRate)maxRate=p.in_rate;if(p.out_rate>maxRate)maxRate=p.out_rate});
document.getElementById('summary').innerHTML=
'<div class="stat up"><div class="num">'+up+'</div><div class="label">&#x1f7e2; 在线</div></div>'+
'<div class="stat down"><div class="num">'+down+'</div><div class="label">&#x1f534; 离线</div></div>'+
'<div class="stat"><div class="num">'+ports.length+'</div><div class="label">总端口</div></div>'+
'<div class="stat"><div class="num">'+fmt(maxRate)+'</div><div class="label">峰值B/s</div></div>';
document.getElementById('grid').innerHTML=ports.map(p=>{
const cls=p.up?'up':'down',st=p.up?'&#x1f7e2; UP':'&#x1f534; DOWN';
const sp=p.speed?(p.speed>=1e9?(p.speed/1e9).toFixed(0)+'G':(p.speed/1e6).toFixed(0)+'M'):'?';
const e=p.errors>0?' &#x26a0;'+p.errors:'';
const ip=barPct(p.in_rate,maxRate),op=barPct(p.out_rate,maxRate);
return '<div class="card '+cls+'"><div class="row1"><span class="port">'+p.name+
'</span><span class="status '+cls+'">'+st+'</span></div><div class="desc">'+(p.desc||'未标注')+
'</div><div class="meta"><span class="speed">'+sp+e+'</span></div>'+
'<div class="traffic-bar"><div class="in" style="width:'+ip+'%"></div><div class="out" style="width:'+op+'%"></div></div>'+
'<div class="traffic-text"><span>&#x25b2; '+fmtB(p.in_rate)+'</span><span>&#x25bc; '+fmtB(p.out_rate)+'</span></div></div>';
}).join('');
}
fetchData();setInterval(fetchData,15000);
</script></body></html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/ports':
            self.send_response(200)
            self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin','*')
            self.end_headers()
            self.wfile.write(json.dumps(cache.get("data",{}), ensure_ascii=False).encode())
        else:
            self.send_response(200)
            self.send_header('Content-Type','text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML.encode())

if __name__ == '__main__':
    threading.Thread(target=poll, daemon=True).start()
    time.sleep(5)
    print(f"\n仪表盘: http://127.0.0.1:{PORT}\n")
    http.server.HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
