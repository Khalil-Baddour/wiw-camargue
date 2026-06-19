"""Configuration du pipeline WIW Camargue.

Centralise tous les chemins et paramètres : c'est le seul fichier à modifier
pour adapter le pipeline à un autre poste de travail, une autre AOI, ou
d'autres fenêtres temporelles.
"""

# --- Chemins ---

# Chemin vers le fichier de l'AOI (zone d'intérêt). À adapter selon le poste.
AOI_PATH = "/home/khalil/workspaces/wiw-camargue/pipeline/aoi/limite_camargue.gpkg"

# Dossier racine des exports : un sous-dossier "wiw-<année>/" y sera créé
# pour chaque date traitée (raster COG + vecteurs GeoJSON/GPKG/Parquet).
OUTPUT_DIR = "/home/khalil/workspaces/wiw-camargue/catalogue"

# Préfixe d'URL sous lequel le catalogue STAC sera accessible une fois
# déployé (utilisé dans les hrefs de la collection STAC). En local, "./"
# convient ; à remplacer par l'URL réelle avant déploiement, par ex.
# "https://mon-domaine.fr/catalogue/".
STAC_HREF_PREFIX = "./"


# --- Recherche STAC (Earth Search / Element84) ---

CATALOG_URL = "https://earth-search.aws.element84.com/v1"
COLLECTION = "sentinel-2-l2a"

# Une fenêtre de recherche par an, même saison, pour rendre la comparaison
# interannuelle pertinente.
DATE_RANGES = [
    "2024-04-01/2024-05-31",
    "2025-04-01/2025-05-31",
    "2026-04-01/2026-05-31",
]

MAX_CLOUD_COVER = 15  # % - on ignore les scènes au-delà de ce seuil
MIN_AOI_COVERAGE = 0.98  # part minimale de l'AOI devant être couverte par les tuiles retenues


# --- Bandes nécessaires au calcul du WIW ---

# Clé interne -> nom de l'asset STAC correspondant
BANDS = {"nir": "nir", "swir2": "swir22", "scl": "scl"}


# --- Calcul de l'indice WIW (Lefebvre et al., 2019) ---

# Seuils de réflectance de surface (Sentinel-2), valeurs publiées par les auteurs
NIR_THRESHOLD_S2 = 0.1804
SWIR2_THRESHOLD_S2 = 0.1131

# Classes SCL exclues : no data, saturé/défectueux, ombre de nuage,
# nuage proba moyenne, nuage proba haute, cirrus fin, neige
SCL_INVALID_CLASSES = {0, 1, 3, 8, 9, 10, 11}

# Facteur d'échelle des réflectances Sentinel-2 L2A (DN -> [0, 1])
S2_REFLECTANCE_SCALE = 10000.0
