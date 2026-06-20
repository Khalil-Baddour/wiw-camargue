// src/api.js
// Centralise tous les appels vers le backend FastAPI.
// L'URL de base est en variable d'environnement pour faciliter le déploiement
// (en local : http://localhost:8000, en prod : l'URL du serveur VPS).

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

/**
 * Récupère la liste des items WIW depuis le backend.
 * Retourne un tableau d'items triés par date croissante, chacun avec :
 *   { id, date, title, area_ha, bbox, assets }
 */
export async function fetchItems() {
  const res = await fetch(`${API_BASE}/items`);
  if (!res.ok) throw new Error(`Erreur API /items : ${res.status}`);
  const data = await res.json();
  return data.items;
}

/**
 * Récupère le GeoJSON d'un item (polygones "eau") pour affichage Leaflet.
 * Utilise l'asset "geojson" exposé en fichier statique par le backend.
 */
export async function fetchItemGeoJSON(item) {
  const res = await fetch(`${API_BASE}${item.assets.geojson}`);
  if (!res.ok) throw new Error(`Erreur chargement GeoJSON ${item.id} : ${res.status}`);
  return res.json();
}
