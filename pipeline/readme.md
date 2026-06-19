pipeline/
├── config.py        # tous les chemins et paramètres
├── stac_search.py   # AOI + recherche STAC + sélection minimale de tuiles + lecture des bandes
├── compute_wiw.py   # calcul de l'indice WIW + surface en eau
├── vectorize.py      # vectorisation des masques en polygones
├── export.py         # export COG + GeoJSON/GPKG/Parquet
├── main.py           # importe tout et exécute le pipeline complet
└── requirements.txt



## Exécution
cd pipeline/
python main.py
