from .schemas import TenantId

TENANTS = {
    "delhi_pwd": {
        "id": "delhi_pwd",
        "short": "Delhi",
        "name": "PWD Delhi",
        "state": "NCT of Delhi",
        "districts": ["New Delhi", "South Delhi", "East Delhi"],
        "center": [28.6139, 77.209],
        "zoom": 12,
        "sla_hours": 72,
        "languages": ["hi", "en"],
    },
    "rajasthan_pwd": {
        "id": "rajasthan_pwd",
        "short": "Rajasthan",
        "name": "PWD Rajasthan",
        "state": "Rajasthan",
        "districts": ["Jaipur", "Jodhpur", "Barmer"],
        "center": [26.2389, 73.0243],
        "zoom": 7,
        "sla_hours": 96,
        "languages": ["hi", "en", "raj"],
    },
}


def district_for_point(tenant_id: TenantId, lat: float, lng: float) -> str:
    if tenant_id == "rajasthan_pwd":
        if lat < 26.2 and lng < 72:
            return "Barmer"
        if lng < 73.8:
            return "Jodhpur"
        return "Jaipur"
    if lng > 77.26:
        return "East Delhi"
    if lat < 28.56:
        return "South Delhi"
    return "New Delhi"
