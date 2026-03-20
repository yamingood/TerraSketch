import React from 'react';
import { 
  Square2StackIcon, 
  CubeIcon, 
  TableCellsIcon,
  TagIcon
} from '@heroicons/react/24/outline';

interface PlanControlsProps {
  viewMode: '2d' | '3d';
  setViewMode: (mode: '2d' | '3d') => void;
  showGrid: boolean;
  setShowGrid: (show: boolean) => void;
  showLabels: boolean;
  setShowLabels: (show: boolean) => void;
}

export const PlanControls: React.FC<PlanControlsProps> = ({
  viewMode,
  setViewMode,
  showGrid,
  setShowGrid,
  showLabels,
  setShowLabels
}) => {
  return (
    <div className="border-b border-gray-200 px-4 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {/* View Mode Toggle */}
          <div className="flex items-center space-x-1">
            <span className="text-sm font-medium text-gray-700 mr-2">Vue:</span>
            <button
              onClick={() => setViewMode('2d')}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                viewMode === '2d'
                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              <div className="flex items-center space-x-1">
                <Square2StackIcon className="h-4 w-4" />
                <span>2D</span>
              </div>
            </button>
            <button
              onClick={() => setViewMode('3d')}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                viewMode === '3d'
                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              <div className="flex items-center space-x-1">
                <CubeIcon className="h-4 w-4" />
                <span>3D</span>
              </div>
            </button>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          {/* Display Options */}
          <div className="flex items-center space-x-3">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showGrid}
                onChange={(e) => setShowGrid(e.target.checked)}
                className="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
              />
              <div className="flex items-center space-x-1 text-sm text-gray-700">
                <TableCellsIcon className="h-4 w-4" />
                <span>Grille</span>
              </div>
            </label>

            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showLabels}
                onChange={(e) => setShowLabels(e.target.checked)}
                className="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
              />
              <div className="flex items-center space-x-1 text-sm text-gray-700">
                <TagIcon className="h-4 w-4" />
                <span>Étiquettes</span>
              </div>
            </label>
          </div>
        </div>
      </div>
    </div>
  );
};