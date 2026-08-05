"""Persistent RSP session daemon.
Commands: drop JSON files into cmds/ dir as NNN.json:
  {"op":"read","addr":...,"len":...,"out":"file.bin"}
  {"op":"regs"}
  {"op":"cont"}            -- resume, returns immediately
  {"op":"halt"}
  {"op":"stopreason"}
  {"op":"watch","kind":2|3|4,"addr":...,"len":...}   (2=write,3=read,4=access)
  {"op":"unwatch","kind":...,"addr":...,"len":...}
  {"op":"waitstop","timeout":30}   -- wait for async stop packet (watchpoint hit)
  {"op":"step"}
  {"op":"quit"}
Results appear as NNN.result.json. State file daemon_state.txt: running|halted.
"""
import sys, os, json, time, glob, binascii
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gdbrsp import RSP

SCRATCH = os.path.dirname(os.path.abspath(__file__))
CMDS = os.path.join(SCRATCH, "cmds")
os.makedirs(CMDS, exist_ok=True)
for f in glob.glob(os.path.join(CMDS, "*")):
    os.remove(f)

r = RSP()
r.flush_packets()
stop = r.cmd("?", timeout=8.0)
running = False
print("connected, stop:", stop, flush=True)

def set_state():
    with open(os.path.join(SCRATCH, "daemon_state.txt"), "w") as f:
        f.write("running" if running else "halted")
set_state()

def handle(cmd):
    global running
    op = cmd["op"]
    if op == "read":
        data = r.read_mem(cmd["addr"], cmd["len"])
        out = cmd.get("out")
        if out:
            with open(os.path.join(SCRATCH, out), "wb") as f: f.write(data)
            return {"ok": True, "len": len(data), "file": out}
        return {"ok": True, "hex": data.hex()}
    if op == "regs":
        g = r.regs()
        return {"ok": True, "regs": [f"{x:08x}" for x in g]}
    if op == "cont":
        r.cont_nowait(); running = True
        return {"ok": True}
    if op == "step":
        p = r.cmd("s", timeout=5.0)
        return {"ok": True, "stop": p.decode() if p else None}
    if op == "halt":
        r.halt(); running = False
        return {"ok": True}
    if op == "stopreason":
        p = r.cmd("?", timeout=5.0)
        return {"ok": True, "stop": p.decode() if p else None}
    if op == "watch":
        p = r.set_watch(cmd["kind"], cmd["addr"], cmd["len"])
        return {"ok": True, "resp": p.decode() if p else None}
    if op == "unwatch":
        p = r.del_watch(cmd["kind"], cmd["addr"], cmd["len"])
        return {"ok": True, "resp": p.decode() if p else None}
    if op == "waitstop":
        t0 = time.time(); tmo = cmd.get("timeout", 30)
        p = r.recv_packet(timeout=tmo)
        if p is None:
            return {"ok": False, "timeout": True}
        running = False
        return {"ok": True, "stop": p.decode(errors="replace")}
    if op == "quit":
        return {"ok": True, "quit": True}
    return {"ok": False, "err": "unknown op"}

print("daemon ready", flush=True)
quit_flag = False
while not quit_flag:
    files = sorted(glob.glob(os.path.join(CMDS, "*.json")))
    files = [f for f in files if not f.endswith(".result.json")]
    if not files:
        time.sleep(0.2)
        continue
    for fp in files:
        try:
            cmd = json.load(open(fp))
        except Exception:
            time.sleep(0.1)
            try: cmd = json.load(open(fp))
            except Exception as e:
                os.remove(fp); continue
        try:
            res = handle(cmd)
        except Exception as e:
            res = {"ok": False, "err": repr(e)}
        set_state()
        with open(fp[:-5] + ".result.json", "w") as f:
            json.dump(res, f)
        os.remove(fp)
        print("did", cmd.get("op"), "->", str(res)[:120], flush=True)
        if res.get("quit"): quit_flag = True

r.detach()
print("daemon exit", flush=True)
