"""
HCS MiniCDN - Service Archivage Long Terme (port 9016)
======================================================
Stockage et archivage de contenus avec compression maximale HCS
Protocol: HTTP/S3 | HCS preset: archivage (ratio ~15:1)
Fonctionne comme un tier de stockage froid avec restauration en 12h
"""

import os, sys, json, logging, random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from services.service_base import HCSServiceBase

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(BASE_DIR, "config", "services.json")) as f:
    CDN_CONFIG = json.load(f)

service_config = CDN_CONFIG["services"]["archive_storage"]
PORT = int(os.getenv("HCS_SERVICE_PORT", service_config["port"]))

svc = HCSServiceBase(service_config, PORT)
app = svc.app

# Catalogue d'archives simulé
ARCHIVE_CATALOG = [
    {"id": "arch001", "title": "Coupe du Monde 2022 - Tous les matchs", "original_tb": 4.2, "hcs_gb": 280, "created": "2022-12-20", "status": "archived"},
    {"id": "arch002", "title": "JO Paris 2024 - Archives completes",    "original_tb": 8.5, "hcs_gb": 567, "created": "2024-08-15", "status": "archived"},
    {"id": "arch003", "title": "Catalogue Films 4K 2020-2024",          "original_tb": 25,  "hcs_gb": 1667,"created": "2024-01-01", "status": "archived"},
    {"id": "arch004", "title": "Series TV Premium 2023",                "original_tb": 12,  "hcs_gb": 800, "created": "2023-12-31", "status": "archived"},
    {"id": "arch005", "title": "Documentaires Nature 8K",               "original_tb": 3.8, "hcs_gb": 253, "created": "2024-06-01", "status": "restoring"},
    {"id": "arch006", "title": "Actualites TV 2024",                    "original_tb": 15,  "hcs_gb": 1000,"created": "2024-12-31", "status": "archived"},
]


@app.get("/catalog")
async def get_archive_catalog():
    """Catalogue des archives disponibles."""
    total_original_tb = sum(a["original_tb"] for a in ARCHIVE_CATALOG)
    total_hcs_gb = sum(a["hcs_gb"] for a in ARCHIVE_CATALOG)
    savings_pct = (1 - total_hcs_gb / (total_original_tb * 1024)) * 100

    return JSONResponse(content={
        "service": "archive_storage",
        "total_archives": len(ARCHIVE_CATALOG),
        "storage_stats": {
            "total_original_tb": round(total_original_tb, 1),
            "total_hcs_gb": round(total_hcs_gb, 1),
            "total_hcs_tb": round(total_hcs_gb / 1024, 2),
            "savings_pct": round(savings_pct, 1),
            "hcs_compression_ratio": 15,
        },
        "archives": ARCHIVE_CATALOG,
        "retrieval_time_hours": service_config.get("retrieval_time_hours", 12),
        "price_per_gb_usd": service_config.get("price_per_gb"),
    })


@app.post("/archive/store")
async def store_content(request: Request):
    """Enregistre un contenu en archive."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    original_size_gb = float(body.get("size_gb", 10.0))
    title = body.get("title", "Archive sans nom")
    hcs_size_gb = round(original_size_gb / 15, 2)
    cost_usd = round(hcs_size_gb * service_config.get("price_per_gb", 0.002), 4)

    return JSONResponse(content={
        "action": "archive_initiated",
        "title": title,
        "original_size_gb": original_size_gb,
        "hcs_compressed_gb": hcs_size_gb,
        "compression_ratio": 15,
        "savings_gb": round(original_size_gb - hcs_size_gb, 2),
        "savings_pct": round((1 - 1/15) * 100, 1),
        "storage_cost_usd_month": cost_usd,
        "estimated_completion_hours": round(original_size_gb / 10, 1),
        "archive_id": f"arch{random.randint(10000, 99999)}",
        "created_at": datetime.utcnow().isoformat(),
        "retrieval_available_at": (datetime.utcnow() + timedelta(hours=2)).isoformat(),
    })


@app.post("/archive/{archive_id}/restore")
async def restore_content(archive_id: str, request: Request):
    """Lance la restauration d'une archive."""
    archive = next((a for a in ARCHIVE_CATALOG if a["id"] == archive_id), None)
    if not archive:
        raise HTTPException(status_code=404, detail=f"Archive {archive_id} introuvable")

    restore_hours = service_config.get("retrieval_time_hours", 12)
    available_at = datetime.utcnow() + timedelta(hours=restore_hours)

    return JSONResponse(content={
        "archive_id": archive_id,
        "title": archive["title"],
        "action": "restore_initiated",
        "hcs_size_gb": archive["hcs_gb"],
        "original_size_tb": archive["original_tb"],
        "restore_to_resolution": "Original (upscaled via HCS)",
        "estimated_restore_hours": restore_hours,
        "available_at": available_at.isoformat(),
        "delivery_url": f"http://localhost:{PORT}/archive/{archive_id}/download",
        "hcs_upscaling": True,
        "cost_restore_usd": round(archive["hcs_gb"] * 0.01, 2),
    })


@app.get("/cost-calculator")
async def cost_calculator(size_tb: float = 1.0, years: int = 5):
    """Calcule le coût de stockage sur X années."""
    hcs_tb = size_tb / 15
    price_per_gb = service_config.get("price_per_gb", 0.002)

    cost_without = size_tb * 1000 * price_per_gb * 12 * years
    cost_with = hcs_tb * 1000 * price_per_gb * 12 * years
    savings = cost_without - cost_with

    return JSONResponse(content={
        "service": "archive_storage",
        "original_size_tb": size_tb,
        "hcs_size_tb": round(hcs_tb, 3),
        "years": years,
        "cost_without_hcs_usd": round(cost_without, 2),
        "cost_with_hcs_usd": round(cost_with, 2),
        "savings_usd": round(savings, 2),
        "savings_pct": round(savings / cost_without * 100, 1),
        "price_per_gb_usd_month": price_per_gb,
        "hcs_compression_ratio": 15,
    })


if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [ARCHIVE] %(message)s")
    uvicorn.run(app, host="0.0.0.0", port=PORT, access_log=False)
