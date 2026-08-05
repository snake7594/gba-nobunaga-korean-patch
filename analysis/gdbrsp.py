import socket, time, sys, binascii

class RSP:
    def __init__(self, host="127.0.0.1", port=2345, timeout=5.0):
        self.s = socket.create_connection((host, port), timeout=10)
        self.s.settimeout(timeout)
        self.buf = b""

    def _cks(self, d): return sum(d) & 0xFF

    def send(self, payload: bytes):
        pkt = b"$" + payload + b"#" + f"{self._cks(payload):02x}".encode()
        self.s.sendall(pkt)

    def recv_packet(self, timeout=None):
        if timeout is not None:
            self.s.settimeout(timeout)
        # returns payload bytes of next $...# packet; handles acks
        while True:
            i = self.buf.find(b"$")
            if i >= 0:
                j = self.buf.find(b"#", i)
                if j >= 0 and len(self.buf) >= j+3:
                    payload = self.buf[i+1:j]
                    self.buf = self.buf[j+3:]
                    self.s.sendall(b"+")
                    return payload
            try:
                d = self.s.recv(65536)
            except socket.timeout:
                return None
            if not d:
                raise ConnectionError("closed")
            self.buf += d

    def flush_packets(self):
        """consume and discard any pending packets (e.g. async stop replies)"""
        while True:
            p = self.recv_packet(timeout=0.3)
            if p is None:
                return

    def cmd(self, payload: str, timeout=None):
        self.send(payload.encode())
        while True:
            p = self.recv_packet(timeout)
            if p is None: return None
            if p == b"": continue      # ack noise
            return p

    def halt(self):
        self.interrupt()
        import time as _t; _t.sleep(0.3)
        self.drain()
        self.flush_packets()

    def drain(self):
        try:
            self.s.settimeout(0.2)
            while True:
                d = self.s.recv(65536)
                if not d: break
                self.buf += d
        except socket.timeout:
            pass

    def read_mem(self, addr, length, chunk=512):
        out = bytearray()
        a = addr
        remaining = length
        while remaining > 0:
            n = min(chunk, remaining)
            r = self.cmd(f"m{a:x},{n:x}")
            if r is None or r.startswith(b"E"):
                raise IOError(f"mem read fail @{a:#x}: {r}")
            b = binascii.unhexlify(r)
            out += b
            a += len(b); remaining -= len(b)
        return bytes(out)

    def cont_nowait(self):
        self.send(b"c")

    def interrupt(self):
        self.s.sendall(b"\x03")

    def stop_reason(self):
        return self.cmd("?")

    def regs(self):
        r = self.cmd("g")
        b = binascii.unhexlify(r)
        gpr = [int.from_bytes(b[i*4:(i+1)*4], "little") for i in range(16)]
        return gpr

    def detach(self):
        try:
            self.send(b"D")
            self.recv_packet(timeout=1.0)
        except Exception:
            pass
        try:
            self.s.close()
        except Exception:
            pass

    def set_watch(self, kind, addr, length):
        # kind: 2=write,3=read,4=access
        return self.cmd(f"Z{kind},{addr:x},{length:x}")

    def del_watch(self, kind, addr, length):
        return self.cmd(f"z{kind},{addr:x},{length:x}")
