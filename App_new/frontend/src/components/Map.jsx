import { useEffect, useRef } from "react";
import L from "leaflet";
import { getColor } from "../utils/map";

export default function Map({ mapInstanceRef }) {
  const mapRef = useRef(null);

  useEffect(() => {
    if (!mapRef.current) return;

    // Map initialisieren
    const map = L.map(mapRef.current).setView(
      [51.51588878700843, 7.475327389339492],
      7,
    );

    // To make the map globally
    mapInstanceRef.current = map;

    const fsLayer = L.featureGroup().addTo(map);
    const adLayer = L.featureGroup().addTo(map);
    const districtLayer = L.featureGroup().addTo(map);
    const cityLayer = L.featureGroup().addTo(map);

    mapInstanceRef.current.layers = {
      cityLayer,
      districtLayer,
      adLayer,
      fsLayer,
    };

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
    const overlayMaps = {
      Cities: cityLayer,
      Districts: districtLayer,
      "Administrative Districts": adLayer,
      "Federal States": fsLayer,
    };

    L.control.layers(baseMaps, overlayMaps).addTo(map);

    // Fixed z-index for layers
    map.createPane("F");
    map.getPane("F").style.zIndex = 400;

    map.createPane("A");
    map.getPane("A").style.zIndex = 410;

    map.createPane("D");
    map.getPane("D").style.zIndex = 420;

    map.createPane("C");
    map.getPane("C").style.zIndex = 430;

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
          .map(
            (c) =>
              '<i class="bi bi-circle-fill" style="color:' +
              getColor(c) +
              '" ></i> ' +
              (c ? c : "+"),
          )
          .join("<br>");

      div.style.backgroundColor = "rgba(255,255,255,0.7)";
      return div;
    };

    legend.addTo(map);

    // Cleanup beim Unmount (WICHTIG!)
    return () => {
      map.remove();
    };
  }, [mapInstanceRef]);

  return <div ref={mapRef} style={{ height: "470px", width: "100%" }} />;
}
