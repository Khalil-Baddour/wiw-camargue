"""Backend FastAPI - Observatoire WIW Camargue.

Rôle de ce backend, est assez simple puisque le catalogue STAC est
statique :

1. Servir les fichiers du catalogue (collection.json, item.json, COG,
   GeoJSON/GPKG/Parquet) en fichiers statiques, accessibles par URL.
2. Exposer un petit endpoint JSON pratique pour le frontend, qui agrège
   le contenu de collection.json + des 3 item.json en une seule réponse
   (évite au frontend de faire 4 requêtes et de parser du STAC brut).

Lancer en local :
    uvicorn app.main:app --reload --port 8000

Documentation interactive générée automatiquement par FastAPI :
    http://localhost:8000/docs
"""

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Dossier racine du catalogue STAC statique généré par pipeline/catalog.py
# (cf. config.OUTPUT_DIR côté pipeline). Structure attendue :
#   wiw-camargue/
#   ├── backend/app/main.py   (ce fichier)
#   └── catalogue/
CATALOG_DIR = Path(__file__).resolve().parent.parent.parent / "catalogue"

app = FastAPI(
    title="Observatoire WIW Camargue - API",
    description=(
        "API servant le catalogue STAC statique des surfaces en eau "
        "détectées par l'indice WIW sur des scènes Sentinel-2 (Camargue)."
    ),
    version="1.0.0",
)

# Autorise le frontend React (servi sur un autre port/domaine en dev) à
# interroger cette API. À restreindre à votre domaine réel en production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Sert tout le contenu de catalogue/ tel quel : collection.json, item.json,
# et surtout les assets (COG, GeoJSON, GPKG, Parquet) en téléchargement
# direct par URL, ex. /catalogue/wiw-2024/wiw-2024.tif
app.mount("/catalogue", StaticFiles(directory=CATALOG_DIR), name="catalogue")


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Fichier introuvable : {path.name}")
    with open(path) as f:
        return json.load(f)


@app.get("/")
def root():
    return {
        "message": "API Observatoire WIW Camargue",
        "endpoints": ["/items", "/items/{item_id}", "/catalogue/collection.json"],
        "docs": "/docs",
    }


@app.get("/items")
def list_items():
    """Liste les items du catalogue avec leurs métadonnées et liens d'assets,
    dans un format prêt à consommer par le frontend (évite de reparser du
    STAC brut côté React)."""
    collection = _load_json(CATALOG_DIR / "collection.json")

    items_summary = []
    for link in collection.get("links", []):
        if link.get("rel") != "item":
            continue
        item_path = (CATALOG_DIR / link["href"]).resolve()
        item = _load_json(item_path)

        items_summary.append({
            "id": item["id"],
            "date": item["properties"]["datetime"],
            "title": item["properties"].get("title"),
            "area_ha": item["properties"].get("wiw:area_ha"),
            "bbox": item["bbox"],
            "assets": {
                key: f"/catalogue/{item['id']}/{Path(asset['href']).name}"
                for key, asset in item["assets"].items()
            },
        })

    items_summary.sort(key=lambda i: i["date"])
    return {"collection": collection["id"], "items": items_summary}


@app.get("/items/{item_id}")
def get_item(item_id: str):
    """Retourne l'item STAC brut (utile pour un client STAC externe, ou
    pour débugger/démontrer la conformité STAC en entretien)."""
    item_path = CATALOG_DIR / item_id / f"{item_id}.json"
    return _load_json(item_path)
