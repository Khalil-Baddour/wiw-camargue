// src/components/DataArchitecturePage.jsx
// Page "Données & Architecture" : rend visible le travail de pipeline qui
// ne transparaît pas dans la carte (catalogue STAC, sources, architecture).


import { RxOpenInNewWindow } from "react-icons/rx";
import { RxDownload } from "react-icons/rx";


const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

const STAC_LINKS = [
  {
    label: "collection.json",
    href: `${API_BASE}/catalogue/collection.json`,
    desc: "Collection STAC racine",
  },
  {
    label: "wiw-2024 item.json",
    href: `${API_BASE}/catalogue/wiw-2024/wiw-2024.json`,
    desc: "Item STAC 2024",
  },
  {
    label: "wiw-2025 item.json",
    href: `${API_BASE}/catalogue/wiw-2025/wiw-2025.json`,
    desc: "Item STAC 2025",
  },
  {
    label: "wiw-2026 item.json",
    href: `${API_BASE}/catalogue/wiw-2026/wiw-2026.json`,
    desc: "Item STAC 2026",
  },
];

const PIPELINE_STEPS = [
  {
    step: "1",
    title: "Recherche STAC",
    detail:
      "Interrogation du catalogue Earth Search (Element84) via pystac-client. Sélection minimale de tuiles Sentinel-2 L2A couvrant l'AOI, filtrées par nébulosité (<15%).",
    tech: "pystac-client · Earth Search",
  },
  {
    step: "2",
    title: "Lecture COG",
    detail:
      "Lecture des bandes NIR (B08, 10m), SWIR2 (B12, 20m) et SCL directement depuis S3 par fenêtre (HTTP range requests), sans télécharger les scènes entières. Mosaïque si plusieurs tuiles.",
    tech: "rasterio · GDAL · rasterio.merge",
  },
  {
    step: "3",
    title: "Calcul WIW",
    detail:
      "Application de la règle WIW (Lefebvre et al. 2019) : pixel classé eau si NIR ≤ 0.1804 et SWIR2 ≤ 0.1131 (réflectance de surface). Réechantillonnage SWIR2/SCL à 10m avant seuillage.",
    tech: "numpy · rasterio.warp",
  },
  {
    step: "4",
    title: "Export COG + vecteurs",
    detail:
      "Masque exporté en GeoTIFF Cloud-Optimized (tiled, overviews). Vectorisation des polygones eau, exports multi-formats : GeoJSON (web), GeoPackage (SIG desktop), GeoParquet (cloud-natif).",
    tech: "rasterio · geopandas · pyarrow",
  },
  {
    step: "5",
    title: "Catalogue STAC statique",
    detail:
      "Génération d'une Collection STAC + 3 Items avec pystac. Chaque item référence ses 4 assets (COG, GeoJSON, GPKG, Parquet). Architecture agnostique : le pipeline peut basculer vers le Copernicus Data Space Ecosystem (DIAS) en changeant l'endpoint et en ajoutant l'auth OAuth2.",
    tech: "pystac",
  },
  {
    step: "6",
    title: "Diffusion",
    detail:
      "Catalogue statique servi par FastAPI (StaticFiles) + 2 endpoints JSON consommés par ce frontend. Tout est conteneurisé (docker-compose) pour le déploiement.",
    tech: "FastAPI · Docker",
  },
];

export default function DataArchitecturePage({ items }) {
  return (
    <div style={{ maxWidth: "820px", margin: "0 auto", padding: "24px 16px" }}>
      <h2 style={{ marginBottom: "4px" }}>Données & Architecture</h2>
      <p style={{ color: "#666", marginBottom: "32px", fontSize: "14px" }}>
        Cette page met en lumière le pipeline de traitement qui produit les données
        affichées sur la carte. Les fichiers du catalogue STAC sont accessibles
        et téléchargeables directement via les liens ci-dessous.
      </p>

      {/* Catalogue STAC */}
      <section style={{ marginBottom: "36px" }}>
        <h3 style={{ borderBottom: "2px solid #1a6eb5", paddingBottom: "6px" }}>
          Catalogue STAC
        </h3>
        <p style={{ fontSize: "14px", color: "#555", marginBottom: "12px" }}>
          Catalogue statique conforme à la spécification STAC, généré par{" "}
          <code>pystac</code>. Interrogeable par n'importe quel client STAC
          (ex. <code>pystac-client</code>) ou visualiseur STAC externe.
        </p>
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          {STAC_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "10px 14px",
                background: "#f4f7fb",
                borderRadius: "6px",
                textDecoration: "none",
                color: "#1a6eb5",
                fontSize: "14px",
                border: "1px solid #dce6f0",
              }}
            >
              <span>
                <strong>{link.label}</strong>
                <span style={{ color: "#888", marginLeft: "10px" }}>
                  {link.desc}
                </span>
              </span>
              <RxOpenInNewWindow size={16} />
            </a>
          ))}
        </div>
      </section>

      {/* Assets téléchargeables */}
      {items.length > 0 && (
        <section style={{ marginBottom: "36px" }}>
          <h3 style={{ borderBottom: "2px solid #1a6eb5", paddingBottom: "6px" }}>
            Produits WIW Camargue (téléchargement)
          </h3>
          <p style={{ fontSize: "14px", color: "#555", marginBottom: "12px" }}>
            Chaque item STAC expose 4 assets : masque raster (COG), polygones
            eau en GeoJSON (web/Leaflet), GeoPackage (QGIS/ArcGIS) et GeoParquet
            (cloud-natif).
          </p>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
            <thead>
              <tr style={{ background: "#f4f7fb" }}>
                <th style={{ textAlign: "left", padding: "8px 10px", border: "1px solid #dce6f0" }}>Date</th>
                <th style={{ padding: "8px 10px", border: "1px solid #dce6f0" }}>COG</th>
                <th style={{ padding: "8px 10px", border: "1px solid #dce6f0" }}>GeoJSON</th>
                <th style={{ padding: "8px 10px", border: "1px solid #dce6f0" }}>GeoPackage</th>
                <th style={{ padding: "8px 10px", border: "1px solid #dce6f0" }}>GeoParquet</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => {
                const date = new Date(item.date).toLocaleDateString("fr-FR", {
                  day: "2-digit", month: "long", year: "numeric",
                });
                return (
                  <tr key={item.id}>
                    <td style={{ padding: "8px 10px", border: "1px solid #dce6f0", fontWeight: "bold" }}>
                      {date}
                    </td>
                    {["data", "geojson", "gpkg", "parquet"].map((assetKey) => (
                      <td key={assetKey} style={{ textAlign: "center", padding: "8px 10px", border: "1px solid #dce6f0" }}>
                        <a
                          href={`${API_BASE}${item.assets[assetKey]}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ color: "#1a6eb5", textDecoration: "none" }}
                        >
                          <RxDownload size={16} />
                        </a>
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </section>
      )}

      {/* Pipeline */}
      <section>
        <h3 style={{ borderBottom: "2px solid #1a6eb5", paddingBottom: "6px" }}>
          Pipeline de traitement
        </h3>
<p style={{ fontSize: "14px", color: "#555", marginBottom: "16px" }}>
  Pipeline Python entièrement automatisé, de la recherche STAC à la
  génération du catalogue, déployé via Docker.
  <br />

  Code source :{" "}
    <a
    href="https://github.com/Khalil-Baddour/wiw-camargue/pipeline/"
    target="_blank"
    rel="noopener noreferrer"
    style={{ color: "#1a6eb5", display: "inline-flex", alignItems: "center", gap: "4px" }}
  >
    github.com/Khalil-Baddour/wiw-camargue <RxOpenInNewWindow size={14} />
  </a>
</p>
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {PIPELINE_STEPS.map((s) => (
            <div
              key={s.step}
              style={{
                display: "flex",
                gap: "14px",
                padding: "14px",
                background: "#f4f7fb",
                borderRadius: "8px",
                border: "1px solid #dce6f0",
              }}
            >
              <div
                style={{
                  minWidth: "32px",
                  height: "32px",
                  borderRadius: "50%",
                  background: "#1a6eb5",
                  color: "#fff",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontWeight: "bold",
                  fontSize: "14px",
                }}
              >
                {s.step}
              </div>
              <div>
                <strong style={{ fontSize: "14px" }}>{s.title}</strong>
                <p style={{ margin: "4px 0 6px", fontSize: "13px", color: "#555" }}>
                  {s.detail}
                </p>
                <code style={{ fontSize: "11px", color: "#888" }}>{s.tech}</code>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
