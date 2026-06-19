"""Génération du catalogue STAC statique (collection + items) à partir des
résultats du pipeline WIW, avec la librairie pystac.

Le catalogue est "statique" : pas de serveur STAC API, juste des fichiers
JSON conformes à la spécification STAC (Collection + Items), à déployer
tels quels sur le serveur avec les assets (COG, GeoJSON, GPKG, Parquet).
Suffisant et recommandé pour un petit nombre de produits dérivés.

Structure générée dans `output_dir` :

    catalogue/
    ├── collection.json
    ├── wiw-2024/
    │   ├── wiw-2024.json      (item STAC)
    │   ├── wiw-2024.tif       (déjà présent, écrit par export.py)
    │   ├── wiw-2024.geojson
    │   ├── wiw-2024.gpkg
    │   └── wiw-2024.parquet
    ├── wiw-2025/
    │   └── ...
    └── wiw-2026/
        └── ...
"""

import os
from datetime import datetime, timezone

import pystac
from pystac import Asset, Collection, Extent, Item, MediaType, SpatialExtent, TemporalExtent
from shapely.geometry import box, mapping

# Media types non couverts nativement par pystac.MediaType
MEDIA_TYPE_GEOPACKAGE = "application/geopackage+sqlite3"
MEDIA_TYPE_GEOPARQUET = "application/vnd.apache.parquet"

COLLECTION_ID = "wiw-camargue"
COLLECTION_TITLE = "Water In Wetlands - Camargue"
COLLECTION_DESCRIPTION = (
    "Surfaces en eau detectees dans les zones humides de Camargue par "
    "l'indice Water In Wetlands (WIW, Lefebvre et al. 2019) applique a "
    "des scenes Sentinel-2 L2A, une date par annee."
)


def _item_bbox_and_geometry(gdf):
    """Calcule la bbox et la geometrie (en WGS84) de l'emprise d'un GeoDataFrame.

    Utilise l'enveloppe convexe des polygones plutot que l'union exacte :
    plus simple, et suffisant pour decrire l'emprise spatiale d'un item STAC.
    """
    gdf_wgs84 = gdf.to_crs("EPSG:4326")
    minx, miny, maxx, maxy = gdf_wgs84.total_bounds
    bbox = [minx, miny, maxx, maxy]
    geometry = mapping(box(*bbox))
    return bbox, geometry


def build_item(date_range, result, gdf, asset_paths, item_href_prefix):
    """Construit un pystac.Item pour une date traitée.

    Parametres :
        date_range     : cle de date_range utilisee dans le pipeline (ex. "2024-04-01/2024-05-31")
        result          : entree de `results` (compute_wiw.compute_results) pour cette date
        gdf             : GeoDataFrame vectorise correspondant (vectorize.vectorize_results)
        asset_paths     : dict des chemins de fichiers exportes, ex.
                          {"cog": ".../wiw-2024.tif", "geojson": ..., "gpkg": ..., "parquet": ...}
        item_href_prefix: prefixe d'URL ou de chemin relatif sous lequel les
                          assets seront accessibles une fois deployes (ex.
                          "https://mon-domaine.fr/catalogue/wiw-2024/" ou "./")
    """
    bbox, geometry = _item_bbox_and_geometry(gdf)
    acq_date = result["date"]
    item_id = f"wiw-{acq_date.year}"

    item = Item(
        id=item_id,
        geometry=geometry,
        bbox=bbox,
        datetime=datetime(acq_date.year, acq_date.month, acq_date.day, tzinfo=timezone.utc),
        properties={
            "title": f"Surfaces en eau - Camargue - {acq_date.isoformat()}",
            "wiw:area_ha": round(float(gdf["area_ha"].sum()), 2),
            "wiw:source_tiles": result["tile_ids"],
            "wiw:nir_threshold": 0.1804,
            "wiw:swir2_threshold": 0.1131,
        },
    )

    item.add_asset(
        "data",
        Asset(
            href=f"{item_href_prefix}{os.path.basename(asset_paths['cog'])}",
            media_type=MediaType.COG,
            title="Masque WIW (raster, Cloud-Optimized GeoTIFF)",
            roles=["data"],
        ),
    )
    item.add_asset(
        "geojson",
        Asset(
            href=f"{item_href_prefix}{os.path.basename(asset_paths['geojson'])}",
            media_type=MediaType.GEOJSON,
            title="Polygones eau (GeoJSON, WGS84)",
            roles=["data"],
        ),
    )
    item.add_asset(
        "gpkg",
        Asset(
            href=f"{item_href_prefix}{os.path.basename(asset_paths['gpkg'])}",
            media_type=MEDIA_TYPE_GEOPACKAGE,
            title="Polygones eau (GeoPackage)",
            roles=["data"],
        ),
    )
    item.add_asset(
        "parquet",
        Asset(
            href=f"{item_href_prefix}{os.path.basename(asset_paths['parquet'])}",
            media_type=MEDIA_TYPE_GEOPARQUET,
            title="Polygones eau (GeoParquet)",
            roles=["data"],
        ),
    )

    return item


def build_collection(items, collection_href_prefix):
    """Construit la Collection STAC regroupant tous les items, avec son
    extent spatial/temporel calcule a partir des items fournis."""
    bboxes = [item.bbox for item in items]
    minx = min(b[0] for b in bboxes)
    miny = min(b[1] for b in bboxes)
    maxx = max(b[2] for b in bboxes)
    maxy = max(b[3] for b in bboxes)

    dates = sorted(item.datetime for item in items)

    collection = Collection(
        id=COLLECTION_ID,
        title=COLLECTION_TITLE,
        description=COLLECTION_DESCRIPTION,
        extent=Extent(
            spatial=SpatialExtent([[minx, miny, maxx, maxy]]),
            temporal=TemporalExtent([[dates[0], dates[-1]]]),
        ),
        license="proprietary",
        keywords=["sentinel-2", "wiw", "wetlands", "camargue", "earth-observation"],
    )

    for item in items:
        collection.add_item(item)
        # Lien relatif simple : l'item.json vivra dans son propre sous-dossier
        item.set_self_href(f"{collection_href_prefix}{item.id}/{item.id}.json")

    collection.set_self_href(f"{collection_href_prefix}collection.json")

    return collection


def generate_stac_catalog(results, vector_results, exported_paths, output_dir,
                           href_prefix="./"):
    """Genere le catalogue STAC statique complet (collection.json + un
    item.json par date) et l'ecrit sur disque dans `output_dir`.

    Parametres :
        results         : sortie de compute_wiw.compute_results
        vector_results  : sortie de vectorize.vectorize_results
        exported_paths  : dict {date_range: {"cog":..., "geojson":..., "gpkg":..., "parquet":...}}
                          (chemins de fichiers retournes par export.export_all,
                          a adapter si export_all ne les retourne pas encore -
                          voir note d'integration ci-dessous)
        output_dir      : dossier racine du catalogue (ex. config.OUTPUT_DIR)
        href_prefix     : prefixe d'URL pour les hrefs des items/assets une
                          fois en ligne (ex. "https://mon-domaine.fr/catalogue/")
    """
    items = []

    for date_range, result in results.items():
        gdf = vector_results[date_range]
        asset_paths = exported_paths[date_range]

        # Les assets d'un item vivent dans son propre sous-dossier
        # (wiw-<annee>/), donc les hrefs d'assets restent relatifs ("./").
        item = build_item(date_range, result, gdf, asset_paths, item_href_prefix="./")
        items.append(item)

    collection = build_collection(items, collection_href_prefix=href_prefix)

    collection.normalize_hrefs(output_dir)
    collection.save(catalog_type=pystac.CatalogType.SELF_CONTAINED)

    print(f"Catalogue STAC genere dans {output_dir} ({len(items)} item(s)).")
    return collection
