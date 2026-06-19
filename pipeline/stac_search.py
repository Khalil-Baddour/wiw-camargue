"""Recherche STAC (Earth Search) et lecture des bandes Sentinel-2 sur l'AOI.

Ce module regroupe :
- le chargement de l'AOI et sa reprojection en WGS84 (attendue par STAC) ;
- la recherche des scènes Sentinel-2 L2A par fenêtre temporelle, avec une
  sélection du nombre MINIMAL de tuiles nécessaires pour couvrir l'AOI
  (1, 2 ou 3 tuiles selon le cas, jamais plus) ;
- la lecture/découpage des bandes (avec mosaïque si plusieurs tuiles).
"""

import geopandas as gpd
import pystac_client
import rasterio
import shapely.geometry
import shapely.ops
from rasterio.io import MemoryFile
from rasterio.mask import mask
from rasterio.merge import merge


def load_aoi(aoi_path):
    """Charge l'AOI et la reprojette en WGS84 (CRS attendu par la bbox STAC).

    Retourne (aoi, aoi_wgs84, bbox) :
    - aoi : GeoDataFrame dans son CRS d'origine
    - aoi_wgs84 : GeoDataFrame reprojeté en EPSG:4326
    - bbox : [minx, miny, maxx, maxy] en WGS84
    """
    aoi = gpd.read_file(aoi_path)
    aoi_wgs84 = aoi.to_crs("EPSG:4326") if aoi.crs != "EPSG:4326" else aoi
    bbox = aoi_wgs84.total_bounds.tolist()
    return aoi, aoi_wgs84, bbox


def _select_minimal_tiles(items, aoi_geom_wgs84, aoi_area, target_coverage):
    """Sélectionne le nombre minimal de tuiles nécessaires pour couvrir
    l'AOI à hauteur de `target_coverage`.

    Trie les tuiles candidates par nébulosité croissante puis les ajoute
    une à une, en ne gardant que celles qui apportent une vraie plus-value
    de couverture, et s'arrête dès que la cible est atteinte.
    """
    candidates = [(item, shapely.geometry.shape(item.geometry)) for item in items]
    # On ne garde que les tuiles qui touchent réellement l'AOI
    candidates = [(i, g) for i, g in candidates if g.intersects(aoi_geom_wgs84)]
    candidates.sort(key=lambda c: c[0].properties["eo:cloud_cover"])

    selected = []
    covered = None
    current_coverage = 0.0

    for item, geom in candidates:
        if current_coverage >= target_coverage:
            break
        new_covered = geom if covered is None else shapely.ops.unary_union([covered, geom])
        new_coverage = new_covered.intersection(aoi_geom_wgs84).area / aoi_area
        if new_coverage > current_coverage:  # la tuile apporte une vraie plus-value
            selected.append(item)
            covered = new_covered
            current_coverage = new_coverage

    return selected, current_coverage


def search_and_select_tiles(catalog_url, collection, date_ranges, bbox, aoi_wgs84,
                             max_cloud_cover, min_aoi_coverage):
    """Recherche les scènes Sentinel-2 sur chaque fenêtre temporelle et ne
    garde, pour chacune, que les tuiles minimales nécessaires pour couvrir
    l'AOI à hauteur de `min_aoi_coverage`.

    Retourne {date_range: [items]} (1, 2 ou 3 tuiles selon le cas).
    """
    client = pystac_client.Client.open(catalog_url)
    aoi_geom_wgs84 = aoi_wgs84.unary_union
    aoi_area = aoi_geom_wgs84.area

    selected_items = {}

    for date_range in date_ranges:
        search = client.search(
            collections=[collection],
            bbox=bbox,
            datetime=date_range,
            query={"eo:cloud_cover": {"lt": max_cloud_cover}},
        )
        items = list(search.items())

        if not items:
            print(f"{date_range} -> aucune scène trouvée sous {max_cloud_cover}% de nuages")
            continue

        # On regroupe par date d'acquisition exacte : un même jour peut
        # nécessiter plusieurs tuiles adjacentes pour couvrir toute l'AOI.
        by_acq_date = {}
        for item in items:
            by_acq_date.setdefault(item.datetime.date(), []).append(item)

        candidates = []
        for acq_date, day_items in by_acq_date.items():
            chosen_tiles, coverage = _select_minimal_tiles(
                day_items, aoi_geom_wgs84, aoi_area, min_aoi_coverage
            )
            if not chosen_tiles:
                continue
            mean_cloud = sum(i.properties["eo:cloud_cover"] for i in chosen_tiles) / len(chosen_tiles)
            candidates.append((coverage, mean_cloud, acq_date, chosen_tiles))

        if not candidates:
            print(f"{date_range} -> aucune tuile ne touche réellement l'AOI")
            continue

        # On garde la date qui couvre le mieux l'AOI (et en cas d'égalité, la moins nuageuse)
        candidates.sort(key=lambda c: (-c[0], c[1]))
        best_coverage, best_cloud, best_date, best_items = candidates[0]

        selected_items[date_range] = best_items

        tile_ids = ", ".join(i.id for i in best_items)
        print(
            f"{date_range} -> {len(best_items)} tuile(s) le {best_date} "
            f"(couverture AOI: {best_coverage:.1%}, nuages moyens: {best_cloud:.1f}%) - {tile_ids}"
        )
        if best_coverage < min_aoi_coverage:
            print(f"  /!\\ Couverture incomplète de l'AOI pour {date_range} ({best_coverage:.1%})")

    return selected_items


def _read_band_mosaic_clipped(asset_hrefs, aoi_gdf):
    """Lit un ou plusieurs assets COG (une tuile ou plusieurs tuiles pour la
    même date), les mosaïque si besoin, puis découpe le résultat sur l'AOI
    (reprojection automatique vers le CRS du raster)."""
    datasets = [rasterio.open(href) for href in asset_hrefs]
    try:
        src_crs = datasets[0].crs
        aoi_proj = aoi_gdf.to_crs(src_crs)
        # On limite la mosaïque à l'emprise de l'AOI : évite de télécharger
        # l'intégralité de chaque tuile (110x110 km) via le réseau.
        bounds = tuple(aoi_proj.total_bounds)

        mosaic, mosaic_transform = merge(datasets, bounds=bounds)

        profile = datasets[0].profile.copy()
        profile.update(
            height=mosaic.shape[1],
            width=mosaic.shape[2],
            transform=mosaic_transform,
            count=1,
        )

        with MemoryFile() as memfile:
            with memfile.open(**profile) as mem_dataset:
                mem_dataset.write(mosaic)
                out_image, out_transform = mask(mem_dataset, aoi_proj.geometry, crop=True)
                return out_image[0], out_transform, mem_dataset.crs
    finally:
        for ds in datasets:
            ds.close()


def read_bands_for_selection(selected_items, aoi_wgs84, bands):
    """Lit et découpe les bandes nécessaires (NIR, SWIR2, SCL) pour chaque
    date sélectionnée.

    Retourne {date_range: {"nir": ndarray, "nir_transform": ...,
    "nir_crs": ..., "swir2": ..., "scl": ...}}.
    """
    bands_by_date = {}

    for date_range, items in selected_items.items():
        band_data = {}
        crs_used = None
        for band_key, asset_key in bands.items():
            hrefs = [item.assets[asset_key].href for item in items]
            data, transform, crs = _read_band_mosaic_clipped(hrefs, aoi_wgs84)
            band_data[band_key] = data
            band_data[f"{band_key}_transform"] = transform
            band_data[f"{band_key}_crs"] = crs
            crs_used = crs
        bands_by_date[date_range] = band_data

        tile_ids = ", ".join(item.id for item in items)
        print(
            f"{date_range} - CRS: {crs_used} - {len(items)} tuile(s) ({tile_ids}) - "
            f"NIR {band_data['nir'].shape}, SWIR2 {band_data['swir2'].shape}, "
            f"SCL {band_data['scl'].shape}"
        )

    return bands_by_date
