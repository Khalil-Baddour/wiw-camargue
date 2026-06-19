// src/components/WaterAreaChart.jsx
// Graphique linéaire (Recharts) montrant l'évolution de la surface en eau
// sur les 3 dates disponibles. La date sélectionnée est mise en évidence
// par un point actif de couleur distincte.

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceDot,
  ResponsiveContainer,
} from "recharts";

export default function WaterAreaChart({ items, selectedItem }) {
  const data = items.map((item) => ({
    date: new Date(item.date).toLocaleDateString("fr-FR", {
      month: "short",
      year: "numeric",
    }),
    surface_ha: item.area_ha ? Math.round(item.area_ha) : null,
    id: item.id,
  }));

  // Point actif (date sélectionnée) mis en évidence
  const activePoint = data.find((d) => d.id === selectedItem?.id);

  return (
    <div>
      <h3 style={{ margin: "0 0 12px", fontSize: "15px", color: "#333" }}>
        Évolution de la surface en eau détectée (ha)
      </h3>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} />
          <YAxis
            tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
            tick={{ fontSize: 12 }}
            label={{
              value: "ha",
              angle: -90,
              position: "insideLeft",
              offset: 10,
              style: { fontSize: 11 },
            }}
          />
          <Tooltip
            formatter={(value) => [`${value.toLocaleString("fr-FR")} ha`, "Surface"]}
          />
          <Line
            type="monotone"
            dataKey="surface_ha"
            stroke="#1a6eb5"
            strokeWidth={2}
            dot={{ r: 5, fill: "#1a6eb5" }}
            activeDot={{ r: 7 }}
          />
          {/* Point actif mis en évidence en orange */}
          {activePoint && activePoint.surface_ha && (
            <ReferenceDot
              x={activePoint.date}
              y={activePoint.surface_ha}
              r={8}
              fill="#e07b00"
              stroke="#fff"
              strokeWidth={2}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
