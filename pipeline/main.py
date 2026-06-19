"""Pipeline complet WIW Camargue.

Étapes : recherche STAC -> lecture des bandes -> calcul de l'indice WIW ->
vectorisation -> export (COG + GeoJSON/GPKG/Parquet).

Usage :
    python main.py

Tous les chemins et paramètres sont centralisés dans config.py.
"""

import os

# Permet à GDAL/rasterio de lire les COG publics sur S3 sans credentials AWS,
# et évite un listing de répertoire coûteux à chaque ouverture. Doit être
# fait avant toute ouverture de fichier raster distant.
os.environ["AWS_NO_SIGN_REQUEST"] = "YES"
os.environ["GDAL_DISABLE_READDIR_ON_OPEN"] = "EMPTY_DIR"

import config
import stac_search
import compute_wiw
import vectorize
import export
import catalog


def main():
    print("=== 1. Chargement de l'AOI ===")
    aoi, aoi_wgs84, bbox = stac_search.load_aoi(config.AOI_PATH)
    print(f"CRS d'origine : {aoi.crs} | Entités : {len(aoi)} | Bbox WGS84 : {bbox}")

    print("\n=== 2. Recherche STAC et sélection des tuiles ===")
    selected_items = stac_search.search_and_select_tiles(
        catalog_url=config.CATALOG_URL,
        collection=config.COLLECTION,
        date_ranges=config.DATE_RANGES,
        bbox=bbox,
        aoi_wgs84=aoi_wgs84,
        max_cloud_cover=config.MAX_CLOUD_COVER,
        min_aoi_coverage=config.MIN_AOI_COVERAGE,
    )

    print("\n=== 3. Lecture et découpage des bandes ===")
    bands_by_date = stac_search.read_bands_for_selection(
        selected_items, aoi_wgs84, config.BANDS
    )

    print("\n=== 4. Calcul de l'indice WIW ===")
    results = compute_wiw.compute_results(
        bands_by_date, selected_items,
        nir_threshold=config.NIR_THRESHOLD_S2,
        swir2_threshold=config.SWIR2_THRESHOLD_S2,
        scl_invalid_classes=config.SCL_INVALID_CLASSES,
        reflectance_scale=config.S2_REFLECTANCE_SCALE,
    )

    print("\n=== 5. Vectorisation ===")
    vector_results = vectorize.vectorize_results(results)

    print("\n=== 6. Export (COG + GeoJSON/GPKG/Parquet) ===")
    exported_paths = export.export_all(results, vector_results, config.OUTPUT_DIR)

    print("\n=== 7. Génération du catalogue STAC ===")
    catalog.generate_stac_catalog(
        results, vector_results, exported_paths,
        output_dir=config.OUTPUT_DIR,
        href_prefix=config.STAC_HREF_PREFIX,
    )

    print("\nPipeline terminé.")
    return results, vector_results


if __name__ == "__main__":
    main()
