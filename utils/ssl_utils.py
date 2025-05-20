import socket
import ssl
from datetime import datetime

def check_ssl_certificate(domain: str, port: int = 443, timeout: int = 5) -> dict:
    """
    Connects to domain via SSL and retrieves certificate info.
    Returns a dictionary with CN, SAN, issuer, validity, etc.
    """
    try:
        context = ssl.create_default_context()

        with socket.create_connection((domain, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()

        # Parse expiration
        expires_str = cert.get('notAfter')
        expires_at = datetime.strptime(expires_str, '%b %d %H:%M:%S %Y %Z')
        expired = expires_at < datetime.utcnow()

        # Extract subject CN
        subject = dict(x[0] for x in cert.get('subject', []))
        cn = subject.get('commonName', '-')

        # Extract SANs
        sans = [entry[1] for entry in cert.get('subjectAltName', [])]

        # Extract issuer
        issuer = dict(x[0] for x in cert.get('issuer', []))
        issuer_name = issuer.get('commonName', '-')

        # Serial
        serial = cert.get('serialNumber', '-')

        return {
            "Domain": domain,
            "CN": cn,
            "SubjectAltNames": ", ".join(sans),
            "Issuer": issuer_name,
            "Expires": expires_str,
            "Is Expired": expired,
            "Self-signed": cn == issuer_name,
            "Serial": serial
        }

    except ssl.SSLError as e:
        return {"error": f"SSL Error: {str(e)}"}
    except Exception as e:
        return {"error": f"Connection failed: {str(e)}"}
