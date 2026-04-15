import React, { useRef, useEffect, useState } from 'react';

interface Plant {
  id: string;
  nom: string;
  nom_latin: string;
  position: { x: number; y: number };
  taille_mature: { hauteur: number; largeur: number };
  type: string;
  zone_climatique: string[];
  couleur_floraison?: string;
  periode_floraison?: string[];
}

interface Zone {
  nom: string;
  type: string;
  couleur: string;
  points: Array<{ x: number; y: number }>;
}

interface Plan {
  id: string;
  nom: string;
  terrain: {
    dimensions: { longueur: number; largeur: number };
    exposition: string;
    type_sol: string;
  };
  plantes: Plant[];
  zones: Zone[];
}

interface PlanViewerProps {
  plan: Plan;
  selectedPlant: string | null;
  onPlantSelect: (plantId: string | null) => void;
  viewMode: '2d' | '3d';
  showGrid: boolean;
  showLabels: boolean;
}

export const PlanViewer: React.FC<PlanViewerProps> = ({
  plan,
  selectedPlant,
  onPlantSelect,
  viewMode,
  showGrid,
  showLabels
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [scale, setScale] = useState(20); // pixels per meter
  const [offset, _setOffset] = useState({ x: 50, y: 50 });

  useEffect(() => {
    drawPlan();
  }, [plan, selectedPlant, showGrid, showLabels, scale, offset]);

  const drawPlan = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Set canvas size to match terrain
    const canvasWidth = plan.terrain.dimensions.longueur * scale + offset.x * 2;
    const canvasHeight = plan.terrain.dimensions.largeur * scale + offset.y * 2;
    canvas.width = Math.min(canvasWidth, 800);
    canvas.height = Math.min(canvasHeight, 600);

    // Draw grid
    if (showGrid) {
      drawGrid(ctx);
    }

    // Draw zones
    plan.zones.forEach(zone => {
      drawZone(ctx, zone);
    });

    // Draw terrain boundary
    drawTerrainBoundary(ctx);

    // Draw plants
    plan.plantes.forEach(plant => {
      drawPlant(ctx, plant, plant.id === selectedPlant);
    });

    // Draw labels
    if (showLabels) {
      plan.plantes.forEach(plant => {
        drawPlantLabel(ctx, plant);
      });
    }
  };

  const drawGrid = (ctx: CanvasRenderingContext2D) => {
    ctx.strokeStyle = '#E5E7EB';
    ctx.lineWidth = 1;
    
    // Vertical lines
    for (let x = 0; x <= plan.terrain.dimensions.longueur; x++) {
      const canvasX = offset.x + x * scale;
      ctx.beginPath();
      ctx.moveTo(canvasX, offset.y);
      ctx.lineTo(canvasX, offset.y + plan.terrain.dimensions.largeur * scale);
      ctx.stroke();
    }

    // Horizontal lines
    for (let y = 0; y <= plan.terrain.dimensions.largeur; y++) {
      const canvasY = offset.y + y * scale;
      ctx.beginPath();
      ctx.moveTo(offset.x, canvasY);
      ctx.lineTo(offset.x + plan.terrain.dimensions.longueur * scale, canvasY);
      ctx.stroke();
    }
  };

  const drawZone = (ctx: CanvasRenderingContext2D, zone: Zone) => {
    if (zone.points.length < 3) return;

    ctx.fillStyle = zone.couleur + '80'; // Add transparency
    ctx.strokeStyle = zone.couleur;
    ctx.lineWidth = 2;

    ctx.beginPath();
    const firstPoint = zone.points[0];
    ctx.moveTo(
      offset.x + firstPoint.x * scale,
      offset.y + firstPoint.y * scale
    );

    zone.points.slice(1).forEach(point => {
      ctx.lineTo(
        offset.x + point.x * scale,
        offset.y + point.y * scale
      );
    });

    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    // Draw zone label
    const centerX = zone.points.reduce((sum, p) => sum + p.x, 0) / zone.points.length;
    const centerY = zone.points.reduce((sum, p) => sum + p.y, 0) / zone.points.length;
    
    ctx.fillStyle = '#374151';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(
      zone.nom,
      offset.x + centerX * scale,
      offset.y + centerY * scale
    );
  };

  const drawTerrainBoundary = (ctx: CanvasRenderingContext2D) => {
    ctx.strokeStyle = '#1F2937';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.rect(
      offset.x,
      offset.y,
      plan.terrain.dimensions.longueur * scale,
      plan.terrain.dimensions.largeur * scale
    );
    ctx.stroke();
  };

  const drawPlant = (ctx: CanvasRenderingContext2D, plant: Plant, isSelected: boolean) => {
    const centerX = offset.x + plant.position.x * scale;
    const centerY = offset.y + plant.position.y * scale;
    const radius = (plant.taille_mature.largeur / 2) * scale;

    // Plant shadow/root zone
    ctx.fillStyle = isSelected ? '#059669' : '#6B7280';
    ctx.globalAlpha = 0.3;
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
    ctx.fill();
    ctx.globalAlpha = 1;

    // Plant symbol based on type
    const plantColor = getPlantColor(plant.type);
    ctx.fillStyle = isSelected ? '#10B981' : plantColor;
    
    if (plant.type === 'Arbre') {
      // Tree symbol
      const trunkHeight = 8;
      const crownRadius = Math.max(6, radius * 0.3);
      
      // Trunk
      ctx.fillStyle = '#8B4513';
      ctx.fillRect(centerX - 2, centerY - trunkHeight/2, 4, trunkHeight);
      
      // Crown
      ctx.fillStyle = isSelected ? '#10B981' : '#22C55E';
      ctx.beginPath();
      ctx.arc(centerX, centerY - trunkHeight/2, crownRadius, 0, 2 * Math.PI);
      ctx.fill();
    } else if (plant.type === 'Arbuste') {
      // Shrub symbol
      const shrubRadius = Math.max(4, radius * 0.2);
      ctx.fillStyle = isSelected ? '#10B981' : '#16A34A';
      ctx.beginPath();
      ctx.arc(centerX, centerY, shrubRadius, 0, 2 * Math.PI);
      ctx.fill();
    } else {
      // Generic plant symbol
      ctx.fillStyle = isSelected ? '#10B981' : '#22C55E';
      ctx.beginPath();
      ctx.arc(centerX, centerY, Math.max(3, radius * 0.15), 0, 2 * Math.PI);
      ctx.fill();
    }

    // Selection indicator
    if (isSelected) {
      ctx.strokeStyle = '#059669';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(centerX, centerY, radius + 5, 0, 2 * Math.PI);
      ctx.stroke();
    }
  };

  const drawPlantLabel = (ctx: CanvasRenderingContext2D, plant: Plant) => {
    const centerX = offset.x + plant.position.x * scale;
    const centerY = offset.y + plant.position.y * scale;
    const radius = (plant.taille_mature.largeur / 2) * scale;

    ctx.fillStyle = '#FFFFFF';
    ctx.strokeStyle = '#374151';
    ctx.lineWidth = 1;
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';

    // Label background
    const labelY = centerY + radius + 15;
    const textWidth = ctx.measureText(plant.nom).width + 6;
    
    ctx.fillRect(centerX - textWidth/2, labelY - 8, textWidth, 12);
    ctx.strokeRect(centerX - textWidth/2, labelY - 8, textWidth, 12);

    // Label text
    ctx.fillStyle = '#374151';
    ctx.fillText(plant.nom, centerX, labelY - 1);
  };

  const getPlantColor = (type: string): string => {
    switch (type) {
      case 'Arbre': return '#16A34A';
      case 'Arbuste': return '#22C55E';
      case 'Vivace': return '#4ADE80';
      case 'Graminée': return '#84CC16';
      default: return '#22C55E';
    }
  };

  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = (event.clientX - rect.left - offset.x) / scale;
    const y = (event.clientY - rect.top - offset.y) / scale;

    // Find clicked plant
    const clickedPlant = plan.plantes.find(plant => {
      const dx = x - plant.position.x;
      const dy = y - plant.position.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      return distance <= plant.taille_mature.largeur / 2;
    });

    onPlantSelect(clickedPlant?.id || null);
  };

  const handleZoom = (delta: number) => {
    setScale(prevScale => Math.max(5, Math.min(50, prevScale + delta)));
  };

  return (
    <div className="relative">
      {viewMode === '2d' ? (
        <div className="border border-gray-300 rounded-lg overflow-hidden bg-white">
          <canvas
            ref={canvasRef}
            onClick={handleCanvasClick}
            className="cursor-pointer"
            style={{ maxWidth: '100%', height: 'auto' }}
          />
          
          {/* Zoom controls */}
          <div className="absolute bottom-4 left-4 flex flex-col bg-white rounded-lg shadow-lg border border-gray-300">
            <button
              onClick={() => handleZoom(5)}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-t-lg"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
            </button>
            <button
              onClick={() => handleZoom(-5)}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-b-lg border-t border-gray-300"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
              </svg>
            </button>
          </div>

          {/* Scale indicator */}
          <div className="absolute bottom-4 right-4 bg-white rounded-lg shadow-lg border border-gray-300 px-3 py-2">
            <div className="text-xs text-gray-600">
              1m = {scale}px
            </div>
          </div>
        </div>
      ) : (
        // 3D view placeholder
        <div className="border border-gray-300 rounded-lg bg-gray-100 flex items-center justify-center h-96">
          <div className="text-center text-gray-500">
            <div className="text-4xl mb-2">🌲</div>
            <p>Vue 3D</p>
            <p className="text-sm">À venir dans une prochaine version</p>
          </div>
        </div>
      )}
    </div>
  );
};