// src/components/DateSelector.jsx
// Affiche les 3 dates disponibles sous forme de boutons.
// Le bouton actif est mis en évidence ; un clic notifie le parent via onSelect.

export default function DateSelector({ items, selectedId, onSelect }) {
  return (
    <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
      {items.map((item) => {
        const date = new Date(item.date).toLocaleDateString("fr-FR", {
          day: "2-digit",
          month: "long",
          year: "numeric",
        });
        const isActive = item.id === selectedId;

        return (
          <button
            key={item.id}
            onClick={() => onSelect(item)}
            style={{
              padding: "8px 16px",
              borderRadius: "6px",
              border: isActive ? "2px solid #1a6eb5" : "2px solid #ccc",
              background: isActive ? "#1a6eb5" : "#fff",
              color: isActive ? "#fff" : "#333",
              fontWeight: isActive ? "bold" : "normal",
              cursor: "pointer",
              transition: "all 0.15s",
            }}
          >
            {date}
          </button>
        );
      })}
    </div>
  );
}
