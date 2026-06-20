# Observatoire WIW Camargue
 
Détection et suivi interannuel des surfaces en eau dans les zones humides de Camargue, par application de l'indice **Water In Wetlands (WIW)** sur des images Sentinel-2 L2A issues du programme Copernicus.
 
Les résultats sont publiés sous forme d'un **catalogue STAC statique** (GeoTIFF COG, GeoJSON, GeoPackage, GeoParquet) et visualisables via une **application web cartographique** (React + Leaflet) servie par une API FastAPI.
 
> Référence scientifique : Lefebvre G. et al. (2019), *Introducing WIW for Detecting the Presence of Water in Wetlands with Landsat and Sentinel Satellites*, Remote Sensing, 11(19), 2210. — Indice développé par les chercheurs de l'Institut de recherche de la **Tour du Valat**.
 


---
 
## Objectifs du projet
 
- Mobiliser les standards **STAC** (SpatioTemporal Asset Catalog) de bout en bout : recherche de scènes Sentinel-2 via un catalogue STAC public (Earth Search / Element84) en entrée, et génération d'un catalogue STAC de produits dérivés en sortie
- Travailler avec les formats **cloud-natifs** : lecture de COG par fenêtre (HTTP range requests), export GeoParquet
- Construire un **pipeline Python entièrement automatisé** (recherche → traitement → vectorisation → export → catalogue STAC), déployé via Docker
- Exposer les données via une **API REST** (FastAPI) et une **application web** cartographique (React + Leaflet)
---

--
 
## Pipeline de traitement
 
```
Earth Search (STAC) → Sentinel-2 L2A (COG)
        ↓
  Lecture bandes NIR (B08, 10m) + SWIR2 (B12, 20m) + SCL
  sur l'AOI Camargue (lecture par fenêtre, sans téléchargement complet)
        ↓
  Calcul indice WIW (seuillage NIR ≤ 0.1804 / SWIR2 ≤ 0.1131)
  + masque nuages/ombres/neige (SCL)
        ↓
  Export masque → COG (GeoTIFF Cloud-Optimized)
  Vectorisation → GeoJSON · GeoPackage · GeoParquet
        ↓
  Génération catalogue STAC statique (pystac)
  collection.json + item.json par date + assets téléchargeables
        ↓
  Diffusion : FastAPI (StaticFiles + endpoints JSON)
  Visualisation : React + Leaflet
```
 
---


---
 
## Stack technique
 
| Domaine | Outils |
|---|---|
| Données satellite | Sentinel-2 L2A / Copernicus · Earth Search (Element84) |
| Standards géospatiaux | STAC · COG · OGC WMS · GeoParquet |
| Traitement géospatial | Python · rasterio · GDAL · GeoPandas · Shapely · PDAL |
| Catalogue STAC | pystac · pystac-client |
| Backend | FastAPI · uvicorn |
| Frontend | React · Leaflet · react-leaflet · Recharts |
| Déploiement | Docker · docker-compose |
 
---


## Structure du projet
 
```
wiw-camargue/
├── pipeline/                                 # modules Python réutilisables
│   ├── config.py                            # paramètres centralisés
│   ├── stac_search.py                       # recherche STAC + lecture COG
│   ├── compute_wiw.py                       # calcul indice WIW
│   ├── vectorize.py                         # vectorisation polygones eau
│   ├── export.py                            # export COG + vecteurs multi-formats
│   ├── catalog.py                           # génération catalogue STAC (pystac)
│   └── main.py                              # exécution pipeline complet
    └── recherche_stac_calculSpatial.ipynb                             # pipeline exploratoire (recherche + calcul WIW)
   
├── catalogue/                               # catalogue STAC statique généré
│   ├── collection.json
│   ├── wiw-2024/  (item.json · COG · GeoJSON · GeoPackage · GeoParquet)
│   ├── wiw-2025/
│   └── wiw-2026/
├── backend/                                 # API FastAPI

├── frontend/                                # application React + Leaflet

└── docker-compose.yml
```
 
---
