// src/components/MapView.jsx

import { useState, useCallback } from "react";
import { MapContainer, TileLayer, GeoJSON, LayersControl } from "react-leaflet";
import { RxUpdate } from "react-icons/rx";
import { fetchItemGeoJSON } from "../api";

const CAMARGUE_CENTER = [43.52, 4.57];
const CAMARGUE_ZOOM = 10;

const WATER_STYLE = {
  color: "#1a6eb5",
  weight: 0.8,
  fillColor: "#4a90d9",
  fillOpacity: 0.55,
};

export default function MapView({ selectedItem }) {
  const [geoJsonData, setGeoJsonData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadedItemId, setLoadedItemId] = useState(null);

  // Appelé par react-leaflet dès que la couche GeoJSON est montée dans le DOM.
  // C'est le bon moment pour déclencher le premier chargement - la ref est
  // garantie d'exister ici, contrairement à un useEffect classique.
  const onGeoJsonReady = useCallback(() => {
    if (!selectedItem || loadedItemId === selectedItem.id) return;
    loadGeoJSON(selectedItem);
  });

  // Rechargement à chaque changement de date sélectionnée
  const loadGeoJSON = (item) => {
    if (!item) return;
    setLoading(true);
    fetchItemGeoJSON(item)
      .then((data) => {
        setGeoJsonData(data);
        setLoadedItemId(item.id);
      })
      .catch((err) => console.error("Erreur chargement GeoJSON :", err))
      .finally(() => setLoading(false));
  };

  // Quand selectedItem change (clic sur un bouton de date), on recharge
  if (selectedItem && selectedItem.id !== loadedItemId && !loading) {
    loadGeoJSON(selectedItem);
  }

  return (
    <div style={{ position: "relative" }}>

      {/* Indicateur de chargement superposé à la carte */}
      {loading && (
        <div
          style={{
            position: "absolute",
            top: "12px",
            left: "50%",
            transform: "translateX(-50%)",
            zIndex: 1000,
            background: "rgba(26, 110, 181, 0.92)",
            color: "#fff",
            padding: "8px 18px",
            borderRadius: "20px",
            fontSize: "13px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
          }}
        >
          <RxUpdate
            size={15}
            style={{
              animation: "spin 1s linear infinite",
            }}
          />
          Chargement de la carte…
          <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
        </div>
      )}

      <MapContainer
        center={CAMARGUE_CENTER}
        zoom={CAMARGUE_ZOOM}
        style={{ height: "500px", width: "100%", borderRadius: "8px" }}
      >
        <LayersControl position="topright">
          <LayersControl.BaseLayer checked name="OpenStreetMap">
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            />
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer name="Satellite (ESRI)">
            <TileLayer
              url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
              attribution="© Esri, Maxar, Earthstar Geographics"
            />
          </LayersControl.BaseLayer>
        </LayersControl>

        {/* On recrée la couche GeoJSON à chaque changement de données :
            key={selectedItem?.id} force react-leaflet à démonter/remonter
            le composant, ce qui évite les problèmes de mutation de couche */}
        {geoJsonData && (
          <GeoJSON
            key={selectedItem?.id}
            data={geoJsonData}
            style={WATER_STYLE}
            ref={onGeoJsonReady}
            onEachFeature={(feature, layer) => {
              if (feature.properties?.area_ha) {
                layer.bindPopup(
                  `Surface : ${feature.properties.area_ha.toFixed(2)} ha`
                );
              }
            }}
          />
        )}
      </MapContainer>
    </div>
  );
}