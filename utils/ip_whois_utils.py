# utils/ip_whois_utils.py

from ipwhois import IPWhois
from ipwhois.exceptions import IPDefinedError

def lookup_ip_info(ip: str) -> dict:
    """
    Perform WHOIS lookup for given IP address.
    Returns a dictionary with summary info.
    """
    try:
        obj = IPWhois(ip)
        res = obj.lookup_rdap(depth=1)
        
        return {
            "IP": ip,
            "ASN": res.get("asn"),
            "ASN Org": res.get("asn_description"),
            "Country": res.get("network", {}).get("country"),
            "CIDR": res.get("network", {}).get("cidr"),
            "Name": res.get("network", {}).get("name"),
            "Registry": res.get("network", {}).get("rir"),
            "Created": res.get("network", {}).get("events", [{}])[0].get("event_date", "-")
        }

    except IPDefinedError:
        return {"error": f"{ip} is a reserved IP (private/local)"}
    except Exception as e:
        return {"error": str(e)}
