# healthcheck.py
import socket, sys

def up(port: int) -> bool:
    s = socket.socket()
    s.settimeout(2)
    try:
        s.connect(("127.0.0.1", port))
        return True
    except Exception:
        return False
    finally:
        s.close()

# Healthy chỉ khi CẢ 2 cổng đều mở
sys.exit(0 if all(up(p) for p in (8501, 8001)) else 1)