"""Send a command to the daemon and wait for its result."""
import sys, os, json, time, random

SCRATCH = os.path.dirname(os.path.abspath(__file__))
CMDS = os.path.join(SCRATCH, "cmds")

def do(cmd, timeout=60):
    n = f"{int(time.time()*1000)%100000000:08d}{random.randint(0,999):03d}"
    fp = os.path.join(CMDS, n + ".json")
    rp = fp[:-5] + ".result.json"
    tmp = fp + ".tmp"
    with open(tmp, "w") as f: json.dump(cmd, f)
    os.replace(tmp, fp)
    t0 = time.time()
    while time.time() - t0 < timeout:
        if os.path.exists(rp):
            time.sleep(0.05)
            res = json.load(open(rp))
            os.remove(rp)
            return res
        time.sleep(0.1)
    return {"ok": False, "err": "cmd timeout"}

if __name__ == "__main__":
    cmd = json.loads(sys.argv[1])
    tmo = float(sys.argv[2]) if len(sys.argv) > 2 else 60
    print(json.dumps(do(cmd, tmo)))
