import socket

def scan_common_ports(ip: str, ports=None, timeout: float = 1.0) -> dict:
    """
    Scans common TCP ports on a given IP address.
    Returns a dict with 'Open' and 'Closed' lists.
    """
    if ports is None:
        ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 3306, 8080]

    result = {
        "IP": ip,
        "Open": [],
        "Closed": []
    }

    for port in ports:
        try:
            print(f"[PORT SCAN] Scanning port {port} on {ip}...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            res = sock.connect_ex((ip, port))
            if res == 0:
                print(f"→ Open")
                result["Open"].append(port)
            else:
                print(f"→ Closed")
                result["Closed"].append(port)
            sock.close()
        except Exception as e:
            print(f"→ Error: {e}")
            result["Closed"].append(port)

    return result
