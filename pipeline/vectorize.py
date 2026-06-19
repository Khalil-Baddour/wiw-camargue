"""Vectorisation des masques WIW en polygones "eau"."""

import geopandas as gpd
import numpy as np
from rasterio.features import shapes
from shapely.geometry import shape


def vectorize_water_mask(water_mask, transform, crs, item_id=None, item_date=None):
    """Vectorise les pixels "eau" (valeur 1) en polygones. Ignore nuages/non-eau."""
    water_only = np.where(water_mask == 1, 1, 0).astype("uint8")

    polygons = [
        shape(geom)
        for geom, value in shapes(water_only, mask=water_only == 1, transform=transform)
        if value == 1
    ]

    if not polygons:
        return gpd.GeoDataFrame({"area_ha": [], "item_id": [], "date": []}, geometry=[], crs=crs)

    gdf = gpd.GeoDataFrame(geometry=polygons, crs=crs)
    gdf["area_ha"] = gdf.geometry.area / 10_000
    gdf["item_id"] = item_id
    gdf["date"] = item_date
    return gdf


def vectorize_results(results):
    """Vectorise chaque masque WIW de `results`.

    Retourne {date_range: GeoDataFrame} avec les polygones "eau" et leurs
    attributs (surface, tuiles d'origine, date).
    """
    vector_results = {}
    for date_range, r in results.items():
        gdf = vectorize_water_mask(
            r["mask"], r["transform"], r["crs"],
            item_id=", ".join(r["tile_ids"]),
            item_date=r["date"].isoformat(),
        )
        vector_results[date_range] = gdf
    return vector_results
