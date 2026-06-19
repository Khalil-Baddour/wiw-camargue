// src/App.jsx
// Composant racine : charge les items depuis le backend au montage,
// orchestre la navigation entre la carte (MapView + DateSelector +
// WaterAreaChart) et la page "Données & Architecture".

import { useState, useEffect } from "react";
import { fetchItems } from "./api";
import MapView from "./components/MapView";
import DateSelector from "./components/DateSelector";
import WaterAreaChart from "./components/WaterAreaChart";
import DataArchitecturePage from "./components/DataArchitecturePage";


export default function App() {
  const [items, setItems] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [page, setPage] = useState("map"); // "map" | "data"
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchItems()
      .then((data) => {
        setItems(data);
        setSelectedItem(data[0] ?? null); // sélectionne la première date par défaut
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", minHeight: "100vh", background: "#f9fafb" }}>

      {/* Barre de navigation */}
      <header
        style={{
          background: "#1a6eb5",
          color: "#fff",
          padding: "0 24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          height: "56px",
          boxShadow: "0 2px 6px rgba(0,0,0,0.15)",
        }}
      >
        <div>
          <span style={{ fontWeight: "bold", fontSize: "16px" }}>
            Observatoire WIW
          </span>
          <span style={{ marginLeft: "8px", fontSize: "13px", opacity: 0.85 }}>
            Surfaces en eau · Camargue
          </span>
        </div>
        <nav style={{ display: "flex", gap: "4px" }}>
          {[
            { id: "map", label: "Carte" },
            { id: "data", label: "Données & Architecture" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setPage(tab.id)}
              style={{
                padding: "6px 16px",
                borderRadius: "4px",
                border: "none",
                background: page === tab.id ? "rgba(255,255,255,0.25)" : "transparent",
                color: "#fff",
                fontWeight: page === tab.id ? "bold" : "normal",
                cursor: "pointer",
                fontSize: "14px",
              }}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </header>

      {/* Contenu principal */}
      <main style={{ padding: "24px", maxWidth: "960px", margin: "0 auto" }}>

        {loading && (
          <p style={{ textAlign: "center", color: "#888", marginTop: "80px" }}>
            Chargement du catalogue…
          </p>
        )}

        {error && (
          <div
            style={{
              background: "#fff3f3",
              border: "1px solid #f5c2c2",
              borderRadius: "8px",
              padding: "16px",
              color: "#c0392b",
              marginTop: "24px",
            }}
          >
            <strong>Erreur de connexion au backend :</strong> {error}
            <br />
            <small>Vérifiez que le backend FastAPI tourne sur http://localhost:8000</small>
          </div>
        )}

        {!loading && !error && page === "map" && (
          <>
            <div
              style={{
                display: "flex",
                alignItems: "flex-start",
                justifyContent: "space-between",
                flexWrap: "wrap",
                gap: "12px",
                marginBottom: "16px",
              }}
            >
              <div>
                <h1 style={{ margin: 0, fontSize: "20px", color: "#1a3a5c" }}>
                  Détection des surfaces en eau par indice WIW
                </h1>
                <p style={{ margin: "4px 0 0", fontSize: "13px", color: "#666" }}>
                  Water In Wetlands Index · Lefebvre et al. (2019) · Données Sentinel-2 L2A / Copernicus
                </p>
              </div>
              {selectedItem && (
                <div
                  style={{
                    background: "#eaf2fb",
                    borderRadius: "8px",
                    padding: "10px 16px",
                    fontSize: "13px",
                    color: "#1a3a5c",
                    textAlign: "right",
                  }}
                >
                  <strong>
                    {Math.round(selectedItem.area_ha).toLocaleString("fr-FR")} ha
                  </strong>
                  <br />
                  <span style={{ color: "#666" }}>surface en eau détectée</span>
                </div>
              )}
            </div>

            {/* Sélecteur de date */}
            <div style={{ marginBottom: "16px" }}>
              <DateSelector
                items={items}
                selectedId={selectedItem?.id}
                onSelect={setSelectedItem}
              />
            </div>

            {/* Carte */}
            <MapView selectedItem={selectedItem} />

            {/* Graphique */}
            <div
              style={{
                background: "#fff",
                borderRadius: "8px",
                padding: "20px",
                marginTop: "20px",
                border: "1px solid #e0e8f0",
              }}
            >
              <WaterAreaChart items={items} selectedItem={selectedItem} />
            </div>

            {/* Source */}
            <p style={{ fontSize: "11px", color: "#aaa", marginTop: "12px", textAlign: "right" }}>
              Source : Sentinel-2 L2A / Copernicus · Earth Search (Element84) ·
              Lefebvre G. et al. (2019), Remote Sensing, 11(19), 2210
            </p>
          </>
        )}

        {!loading && !error && page === "data" && (
          <DataArchitecturePage items={items} />
        )}
      </main>
    </div>
  );
}
