"""Calcul de l'indice WIW (Water In Wetlands), d'après Lefebvre et al., 2019.

Applique la règle WIW sur les bandes NIR et SWIR2, combinée au masque de
qualité dérivé de la bande SCL (nuages, ombres, neige, no data).
"""

import numpy as np
from rasterio.warp import Resampling, reproject


def resample_to_reference(src_array, src_transform, src_crs,
                           ref_array, ref_transform, ref_crs,
                           resampling=Resampling.bilinear):
    """Réechantillonne src_array sur la grille (forme + transform) de ref_array."""
    dst = np.empty(ref_array.shape, dtype=src_array.dtype)
    reproject(
        source=src_array,
        destination=dst,
        src_transform=src_transform,
        src_crs=src_crs,
        dst_transform=ref_transform,
        dst_crs=ref_crs,
        resampling=resampling,
    )
    return dst


def compute_wiw(nir, nir_transform, nir_crs,
                swir2, swir2_transform, swir2_crs,
                scl, scl_transform, scl_crs,
                nir_threshold, swir2_threshold, scl_invalid_classes,
                reflectance_scale):
    """Calcule le masque WIW sur la grille NIR (10 m).

    Retourne (water_mask, transform) où water_mask vaut 1=eau, 0=non-eau,
    255=invalide (nuage, ombre, neige, no data...).
    """
    swir2_10m = resample_to_reference(
        swir2, swir2_transform, swir2_crs,
        nir, nir_transform, nir_crs,
        resampling=Resampling.bilinear,
    )
    scl_10m = resample_to_reference(
        scl, scl_transform, scl_crs,
        nir, nir_transform, nir_crs,
        resampling=Resampling.nearest,
    )

    nir_refl = nir.astype("float32") / reflectance_scale
    swir2_refl = swir2_10m.astype("float32") / reflectance_scale

    valid_mask = ~np.isin(scl_10m, list(scl_invalid_classes))
    is_water = (nir_refl <= nir_threshold) & (swir2_refl <= swir2_threshold)

    water_mask = np.where(valid_mask, is_water.astype("uint8"), 255).astype("uint8")
    return water_mask, nir_transform


def water_area_ha(water_mask, transform):
    """Surface en eau (ha) à partir du masque WIW et de la résolution du transform."""
    pixel_area_m2 = abs(transform.a * transform.e)
    n_water_pixels = int(np.sum(water_mask == 1))
    return n_water_pixels * pixel_area_m2 / 10_000


def compute_results(bands_by_date, selected_items, nir_threshold, swir2_threshold,
                     scl_invalid_classes, reflectance_scale):
    """Calcule le masque WIW et la surface en eau pour chaque date sélectionnée.

    Retourne {date_range: {"mask", "transform", "crs", "area_ha", "items",
    "date", "tile_ids"}}.
    """
    results = {}

    for date_range, items in selected_items.items():
        b = bands_by_date[date_range]

        water_mask, mask_transform = compute_wiw(
            b["nir"], b["nir_transform"], b["nir_crs"],
            b["swir2"], b["swir2_transform"], b["swir2_crs"],
            b["scl"], b["scl_transform"], b["scl_crs"],
            nir_threshold=nir_threshold,
            swir2_threshold=swir2_threshold,
            scl_invalid_classes=scl_invalid_classes,
            reflectance_scale=reflectance_scale,
        )

        area_ha = water_area_ha(water_mask, mask_transform)
        # Toutes les tuiles d'un même groupe partagent la même date d'acquisition
        # (c'est le critère de regroupement utilisé lors de la sélection STAC).
        acq_date = items[0].datetime.date()
        tile_ids = [item.id for item in items]

        results[date_range] = {
            "mask": water_mask,
            "transform": mask_transform,
            "crs": b["nir_crs"],
            "area_ha": area_ha,
            "items": items,
            "date": acq_date,
            "tile_ids": tile_ids,
        }
        print(f"{acq_date} : surface en eau estimée = {area_ha:.1f} ha ({len(items)} tuile(s))")

    return results
