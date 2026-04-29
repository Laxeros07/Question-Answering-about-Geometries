import { useEffect, useRef } from "react";
import L from "leaflet";

export default function Map() {
  const mapRef = useRef(null);

  useEffect(() => {
    if (!mapRef.current) return;

    // Map initialisieren
    const map = L.map(mapRef.current).setView(
      [51.51588878700843, 7.475327389339492],
      7,
    );

    // Base Layer
    const osm = L.tileLayer(
      "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 18,
      },
    ).addTo(map);

    // Layer Control
    const baseMaps = { OpenStreetMap: osm };
    L.control.layers(baseMaps).addTo(map);

    // Feature Groups
    const fsLayer = L.featureGroup().addTo(map);
    const adLayer = L.featureGroup().addTo(map);
    const districtLayer = L.featureGroup().addTo(map);
    const cityLayer = L.featureGroup().addTo(map);

    // Legend
    const legend = L.control({ position: "bottomleft" });

    legend.onAdd = function () {
      const div = L.DomUtil.create("div", "info legend");

      const categories = [
        "City",
        "District",
        "Administrative district",
        "Federal state",
      ];

      div.innerHTML =
        "<strong>Federal Levels</strong><br>" +
        categories
          .map((c) => `<i style="color:${getColor(c)}">●</i> ${c}`)
          .join("<br>");

      div.style.backgroundColor = "rgba(255,255,255,0.7)";
      return div;
    };

    legend.addTo(map);

    function getColor(d) {
      return d === "City"
        ? "#3A27D0"
        : d === "District"
          ? "#f04b23"
          : d === "Administrative district"
            ? "#ffcc00"
            : d === "Federal state"
              ? "#469F4E"
              : "#ff7f00";
    }

    // Cleanup beim Unmount (WICHTIG!)
    return () => {
      map.remove();
    };
  }, []);

  return <div ref={mapRef} style={{ height: "470px", width: "100%" }} />;
}
