import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix pour les icônes par défaut de Leaflet avec Webpack/Vite
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface ParcelleData {
  geometry?: {
    type: string;
    coordinates: number[][][];
  };
  properties?: {
    surface_m2?: number;
    id_parcelle?: string;
    commune?: string;
    section?: string;
    numero?: string;
  };
  bounds?: {
    minX: number;
    maxX: number;
    minY: number;
    maxY: number;
  };
}

interface ParcelleMapPreviewProps {
  parcelle: ParcelleData;
  className?: string;
}

const ParcelleMapPreview: React.FC<ParcelleMapPreviewProps> = ({ 
  parcelle, 
  className = '' 
}) => {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const parcelleLayerRef = useRef<L.Layer | null>(null);

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    // Initialisation de la carte
    const map = L.map(mapRef.current, {
      center: [46.603354, 1.888334], // Centre de la France par défaut
      zoom: 6,
      zoomControl: true,
    });

    // Couches de fond (utilisation d'OpenStreetMap en fallback)
    const ignLayers = {
      plan: L.tileLayer(
        'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
        {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
          maxZoom: 18,
        }
      ),
      satellite: L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        {
          attribution: '&copy; <a href="https://www.esri.com/">Esri</a>',
          maxZoom: 18,
        }
      ),
      cadastre: L.tileLayer(
        'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
        {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
          maxZoom: 18,
        }
      )
    };

    // Ajouter la couche de base (plan IGN)
    ignLayers.plan.addTo(map);

    // Contrôleur de couches
    const layerControl = L.control.layers(
      {
        'Plan': ignLayers.plan,
        'Satellite': ignLayers.satellite,
        'Cadastre': ignLayers.cadastre
      },
      {},
      { position: 'topright' }
    );
    layerControl.addTo(map);

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  useEffect(() => {
    console.log('ParcelleMapPreview useEffect - parcelle reçue:', parcelle);
    if (!mapInstanceRef.current || !parcelle.geometry) {
      console.log('Conditions non remplies - map:', !!mapInstanceRef.current, 'geometry:', !!parcelle.geometry);
      return;
    }

    const map = mapInstanceRef.current;

    // Supprimer l'ancienne couche de parcelle
    if (parcelleLayerRef.current) {
      map.removeLayer(parcelleLayerRef.current);
    }

    try {
      // Validation et normalisation des coordonnées
      let coords: any = parcelle.geometry.coordinates;
      if (!coords || !Array.isArray(coords)) {
        throw new Error('Coordonnées invalides ou manquantes');
      }

      // Normaliser le format des coordonnées
      // Si les coordonnées sont un simple array de points [lng,lat], les encapsuler
      if (coords.length > 0 && Array.isArray(coords[0]) && typeof coords[0][0] === 'number') {
        // Format: [[lng,lat], [lng,lat], ...] -> [[[lng,lat], [lng,lat], ...]]
        coords = [coords];
      }

      // Vérifier le format final
      if (!coords[0] || !Array.isArray(coords[0])) {
        throw new Error('Format de coordonnées invalide');
      }

      // Vérifier que chaque coordonnée est valide
      const validCoords = coords[0].every(coord => 
        Array.isArray(coord) && 
        coord.length === 2 && 
        typeof coord[0] === 'number' && 
        typeof coord[1] === 'number' &&
        !isNaN(coord[0]) && !isNaN(coord[1]) &&
        coord[0] >= -180 && coord[0] <= 180 &&
        coord[1] >= -90 && coord[1] <= 90
      );

      if (!validCoords) {
        throw new Error('Coordonnées invalides ou hors limites');
      }

      console.log('Coordonnées validées:', coords);

      // Création du GeoJSON pour la parcelle avec coordonnées normalisées
      const geojsonFeature = {
        type: 'Feature' as const,
        geometry: {
          type: 'Polygon',
          coordinates: coords
        },
        properties: parcelle.properties || {}
      };

      // Créer la couche GeoJSON
      const parcelleLayer = L.geoJSON(geojsonFeature, {
        style: {
          fillColor: '#3B82F6',
          weight: 3,
          opacity: 1,
          color: '#1E40AF',
          dashArray: '3',
          fillOpacity: 0.3
        },
        onEachFeature: (feature, layer) => {
          // Popup avec informations de la parcelle
          const props = feature.properties;
          const popupContent = `
            <div class="p-2">
              <h3 class="font-semibold text-lg mb-2">Parcelle ${props.id_parcelle || 'N/A'}</h3>
              <div class="space-y-1 text-sm">
                <div><span class="font-medium">Surface:</span> ${props.surface_m2 ? Math.round(props.surface_m2) : 'N/A'} m²</div>
                ${props.commune ? `<div><span class="font-medium">Commune:</span> ${props.commune}</div>` : ''}
                ${props.section ? `<div><span class="font-medium">Section:</span> ${props.section}</div>` : ''}
                ${props.numero ? `<div><span class="font-medium">Numéro:</span> ${props.numero}</div>` : ''}
              </div>
            </div>
          `;
          layer.bindPopup(popupContent);
        }
      });

      // Ajouter à la carte
      parcelleLayer.addTo(map);
      parcelleLayerRef.current = parcelleLayer;

      // Centrer la carte sur la parcelle
      const bounds = parcelleLayer.getBounds();
      if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [20, 20] });
        
        // Zoom minimum pour voir les détails
        if (map.getZoom() > 16) {
          map.setZoom(16);
        }
      }

    } catch (error) {
      console.error('Erreur lors du rendu de la parcelle sur la carte:', error);
    }
  }, [parcelle]);

  // Affichage de fallback si pas de géométrie
  if (!parcelle.geometry) {
    return (
      <div className={`bg-gray-100 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center ${className}`}>
        <div className="text-center text-gray-500">
          <div className="text-lg mb-2">🗺️</div>
          <div>Aucune géométrie disponible</div>
          <div className="text-sm">La parcelle ne peut pas être affichée</div>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative rounded-lg overflow-hidden border border-gray-300 ${className}`}>
      {/* Carte Leaflet */}
      <div ref={mapRef} className="w-full h-full min-h-[400px]" />
      
      {/* Informations de la parcelle en overlay */}
      <div className="absolute top-4 left-4 bg-white bg-opacity-90 backdrop-blur-sm rounded-lg p-3 shadow-lg z-[1000]">
        <h3 className="font-semibold text-sm mb-2">📍 Parcelle</h3>
        <div className="space-y-1 text-xs">
          {parcelle.properties?.id_parcelle && (
            <div><span className="font-medium">ID:</span> {parcelle.properties.id_parcelle}</div>
          )}
          {parcelle.properties?.surface_m2 && (
            <div><span className="font-medium">Surface:</span> {Math.round(parcelle.properties.surface_m2)} m²</div>
          )}
          {parcelle.properties?.commune && (
            <div><span className="font-medium">Commune:</span> {parcelle.properties.commune}</div>
          )}
        </div>
      </div>
      
      {/* Légende des couches */}
      <div className="absolute bottom-4 left-4 bg-white bg-opacity-90 backdrop-blur-sm rounded-lg p-2 shadow-lg z-[1000]">
        <div className="text-xs text-gray-600">
          💡 Utilisez le contrôleur en haut à droite pour changer de fond de carte
        </div>
      </div>
    </div>
  );
};

export default ParcelleMapPreview;