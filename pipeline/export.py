"""Export des résultats WIW : raster Cloud-Optimized GeoTIFF (COG) et
vecteurs multi-formats (GeoJSON, GeoPackage, GeoParquet).
"""

import os

import rasterio


def export_mask_to_cog(water_mask, transform, crs, output_path):
    """Exporte le masque WIW en GeoTIFF Cloud-Optimized (tiled + overviews)."""
    profile = {
        "driver": "GTiff",
        "height": water_mask.shape[0],
        "width": water_mask.shape[1],
        "count": 1,
        "dtype": "uint8",
        "crs": crs,
        "transform": transform,
        "nodata": 255,
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
        "compress": "deflate",
    }
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(water_mask, 1)
        dst.build_overviews([2, 4, 8, 16], rasterio.enums.Resampling.nearest)
    return output_path


def write_vector_formats(gdf, output_basepath):
    """Écrit le GeoDataFrame en GeoJSON (WGS84), GeoPackage et GeoParquet (CRS natif)."""
    geojson_path = f"{output_basepath}.geojson"
    gpkg_path = f"{output_basepath}.gpkg"
    parquet_path = f"{output_basepath}.parquet"

    gdf.to_crs("EPSG:4326").to_file(geojson_path, driver="GeoJSON")
    gdf.to_file(gpkg_path, driver="GPKG")
    gdf.to_parquet(parquet_path)

    return {"geojson": geojson_path, "gpkg": gpkg_path, "parquet": parquet_path}


def export_all(results, vector_results, output_dir):
    """Exporte chaque date traitée : raster COG + vecteurs GeoJSON/GPKG/Parquet.

    Crée un sous-dossier `<output_dir>/wiw-<année>/` par date.

    Retourne {date_range: {"cog": chemin, "geojson": chemin, "gpkg": chemin,
    "parquet": chemin}}, nécessaire à catalog.py pour construire les assets
    STAC référençant ces fichiers.
    """
    exported_paths = {}

    for date_range, r in results.items():
        year = r["date"].year
        out_dir = os.path.join(output_dir, f"wiw-{year}")
        os.makedirs(out_dir, exist_ok=True)

        cog_path = export_mask_to_cog(
            r["mask"], r["transform"], r["crs"],
            os.path.join(out_dir, f"wiw-{year}.tif"),
        )

        gdf = vector_results[date_range]
        vector_paths = write_vector_formats(gdf, os.path.join(out_dir, f"wiw-{year}"))

        exported_paths[date_range] = {"cog": cog_path, **vector_paths}

        print(f"{year} : {len(gdf)} polygones, {gdf['area_ha'].sum():.1f} ha -> {out_dir}/")

    return exported_paths
