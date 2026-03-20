import React, { useRef, useEffect } from 'react';

interface Coordinates {
  type: string;
  coordinates: number[][][];
}

interface ParcelleGeometry {
  type: string;
  coordinates: number[][][];
}

interface ParcelleData {
  geometry: ParcelleGeometry;
  properties: {
    commune?: string;
    section?: string;
    numero?: string;
    surface?: number;
  };
  bounds: {
    minX: number;
    maxX: number;
    minY: number;
    maxY: number;
  };
}

interface ParcellePreviewProps {
  parcelle: ParcelleData;
  className?: string;
}

const ParcellePreview: React.FC<ParcellePreviewProps> = ({ parcelle, className = '' }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    drawParcelle();
  }, [parcelle]);

  const drawParcelle = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Validation des données de géométrie
    if (!parcelle?.geometry?.coordinates || !Array.isArray(parcelle.geometry.coordinates)) {
      console.warn('Données de géométrie invalides:', parcelle);
      // Afficher un message d'erreur dans le canvas
      ctx.fillStyle = '#6B7280';
      ctx.font = '14px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Données de parcelle invalides', canvas.width / 2, canvas.height / 2);
      return;
    }

    // Calculate scale and offset to fit the parcel in the canvas
    const { bounds } = parcelle;
    const width = bounds.maxX - bounds.minX;
    const height = bounds.maxY - bounds.minY;
    
    const canvasWidth = canvas.width - 40; // 20px margin on each side
    const canvasHeight = canvas.height - 40;
    
    const scaleX = canvasWidth / width;
    const scaleY = canvasHeight / height;
    const scale = Math.min(scaleX, scaleY);
    
    const offsetX = (canvas.width - width * scale) / 2;
    const offsetY = (canvas.height - height * scale) / 2;

    // Convert geographic coordinates to canvas coordinates
    const geoToCanvas = (lon: number, lat: number) => {
      const x = (lon - bounds.minX) * scale + offsetX;
      const y = canvas.height - ((lat - bounds.minY) * scale + offsetY); // Flip Y axis
      return { x, y };
    };

    // Draw the parcel
    if (parcelle.geometry.type === 'Polygon' && parcelle.geometry.coordinates.length > 0) {
      const coordinates = parcelle.geometry.coordinates[0]; // First ring (exterior)
      
      if (coordinates && Array.isArray(coordinates) && coordinates.length > 0) {
        ctx.beginPath();
        
        const start = geoToCanvas(coordinates[0][0], coordinates[0][1]);
        ctx.moveTo(start.x, start.y);
        
        for (let i = 1; i < coordinates.length; i++) {
          const point = geoToCanvas(coordinates[i][0], coordinates[i][1]);
          ctx.lineTo(point.x, point.y);
        }
        
        ctx.closePath();
        
        // Fill
        ctx.fillStyle = '#10B981'; // emerald-500
        ctx.globalAlpha = 0.3;
        ctx.fill();
        
        // Stroke
        ctx.globalAlpha = 1;
        ctx.strokeStyle = '#059669'; // emerald-600
        ctx.lineWidth = 2;
        ctx.stroke();
      }
    }

    // Draw a simple north arrow
    const arrowX = canvas.width - 30;
    const arrowY = 30;
    ctx.fillStyle = '#374151'; // gray-700
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('N', arrowX, arrowY - 5);
    
    // Arrow
    ctx.beginPath();
    ctx.moveTo(arrowX, arrowY);
    ctx.lineTo(arrowX - 5, arrowY + 10);
    ctx.lineTo(arrowX + 5, arrowY + 10);
    ctx.closePath();
    ctx.fillStyle = '#059669';
    ctx.fill();
  };

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-4 ${className}`}>
      <div className="mb-3">
        <h3 className="text-sm font-medium text-gray-900 mb-2">Aperçu de la parcelle</h3>
        <div className="text-xs text-gray-600 space-y-1">
          {parcelle.properties.commune && (
            <div>
              <span className="font-medium">Commune:</span> {parcelle.properties.commune}
            </div>
          )}
          {parcelle.properties.section && (
            <div>
              <span className="font-medium">Section:</span> {parcelle.properties.section}
            </div>
          )}
          {parcelle.properties.numero && (
            <div>
              <span className="font-medium">Numéro:</span> {parcelle.properties.numero}
            </div>
          )}
          {parcelle.properties.surface && (
            <div>
              <span className="font-medium">Surface:</span> {parcelle.properties.surface.toFixed(1)} m²
            </div>
          )}
        </div>
      </div>
      
      <div className="relative">
        <canvas
          ref={canvasRef}
          width={280}
          height={200}
          className="border border-gray-200 rounded"
          style={{ width: '100%', height: 'auto', maxWidth: '280px' }}
        />
      </div>
    </div>
  );
};

export default ParcellePreview;