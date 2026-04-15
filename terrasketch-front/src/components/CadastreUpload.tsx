import React, { useState, useRef } from 'react';
import { Upload, FileText, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import ParcelleMapPreview from './ParcelleMapPreview';

interface CadastreUploadProps {
  onParcellConfirmed?: (parcelle: any) => void;
  onError?: (error: string) => void;
  maxSizeMb?: number;
}

interface UploadState {
  status: 'idle' | 'uploading' | 'preview' | 'error';
  progress: number;
  error?: string;
  parcelle?: any;
}

const CadastreUpload: React.FC<CadastreUploadProps> = ({
  onParcellConfirmed,
  onError,
  maxSizeMb = 50
}) => {
  const [state, setState] = useState<UploadState>({
    status: 'idle',
    progress: 0
  });
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const acceptedFormats = [
    { name: 'GeoJSON', extensions: '.json, .geojson', description: 'Format standard web' },
    { name: 'Shapefile', extensions: '.zip', description: 'Archive complète (.shp+.dbf+.shx)' },
    { name: 'DXF', extensions: '.dxf', description: 'Fichier CAO cadastral' },
    { name: 'EDIGÉO', extensions: '.thf, .tar.bz2', description: 'Format officiel DGFiP' }
  ];

  const validateFile = (file: File): string | null => {
    // Vérification taille
    const sizeMb = file.size / (1024 * 1024);
    if (sizeMb > maxSizeMb) {
      return `Fichier trop volumineux: ${sizeMb.toFixed(1)} MB. Limite: ${maxSizeMb} MB`;
    }

    // Vérification extension
    const allowedExtensions = ['.json', '.geojson', '.zip', '.dxf', '.thf', '.tar.bz2', '.tar.gz'];
    const fileName = file.name.toLowerCase();
    const hasValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext));
    
    if (!hasValidExtension) {
      return `Format non supporté. Extensions acceptées: ${allowedExtensions.join(', ')}`;
    }

    return null;
  };

  const uploadFile = async (file: File) => {
    setState({ status: 'uploading', progress: 0 });

    try {
      const formData = new FormData();
      formData.append('cadastre_file', file);

      const response = await fetch('http://localhost:8001/api/cadastre/upload/', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("Service d'upload temporairement indisponible");
        }
        throw new Error(`Erreur serveur: ${response.status}`);
      }

      const result = await response.json();

      setState({ 
        status: 'preview', 
        progress: 100, 
        parcelle: result 
      });

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Erreur inconnue';
      setState({ 
        status: 'error', 
        progress: 0, 
        error: errorMessage 
      });
      onError?.(errorMessage);
    }
  };

  const handleFileSelect = async (file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      setState({ 
        status: 'error', 
        progress: 0, 
        error: validationError 
      });
      return;
    }

    await uploadFile(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const confirmParcelle = () => {
    if (state.parcelle && onParcellConfirmed) {
      onParcellConfirmed(state.parcelle);
    }
  };

  const resetUpload = () => {
    setState({ status: 'idle', progress: 0 });
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // État Idle - Zone de drop
  if (state.status === 'idle') {
    return (
      <div className="w-full max-w-2xl mx-auto">
        {/* Zone de drop */}
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            isDragOver 
              ? 'border-green-400 bg-green-50' 
              : 'border-gray-300 hover:border-gray-400'
          }`}
          onDrop={handleDrop}
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragOver(true);
          }}
          onDragLeave={() => setIsDragOver(false)}
        >
          <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Déposez votre fichier cadastral ici
          </h3>
          <p className="text-gray-500 mb-4">
            ou cliquez pour parcourir vos fichiers
          </p>
          
          <button
            onClick={() => fileInputRef.current?.click()}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            <FileText className="h-4 w-4 mr-2" />
            Parcourir
          </button>
          
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            onChange={handleFileInput}
            accept=".json,.geojson,.zip,.dxf,.thf,.tar.bz2,.tar.gz"
          />
        </div>

        {/* Formats acceptés */}
        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Formats supportés :</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {acceptedFormats.map((format) => (
              <div key={format.name} className="flex items-center p-3 border rounded-lg">
                <FileText className="h-5 w-5 text-green-600 mr-3" />
                <div>
                  <div className="font-medium text-sm">{format.name}</div>
                  <div className="text-xs text-gray-500">{format.extensions}</div>
                  <div className="text-xs text-gray-400">{format.description}</div>
                </div>
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-500 mt-3">
            Taille maximum : {maxSizeMb} MB
          </p>
        </div>
      </div>
    );
  }

  // État Uploading - Progress bar
  if (state.status === 'uploading') {
    return (
      <div className="w-full max-w-md mx-auto">
        <div className="text-center mb-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto mb-3"></div>
          <h3 className="text-lg font-medium text-gray-900">
            Analyse du fichier cadastral...
          </h3>
          <p className="text-gray-500">
            Extraction de la géométrie et validation
          </p>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-green-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${state.progress}%` }}
          />
        </div>
      </div>
    );
  }

  // État Preview - Carte et informations
  if (state.status === 'preview' && state.parcelle) {
    const { parcelle } = state;
    
    // Transformer les données de l'API en format attendu par ParcellePreview
    const coordinates = parcelle.geojson?.geometry?.coordinates || [];
    
    // Calculer les bounds depuis les coordonnées
    let bounds = { minX: 0, maxX: 1, minY: 0, maxY: 1 };
    if (coordinates.length > 0 && coordinates[0] && Array.isArray(coordinates[0])) {
      const allCoords = coordinates[0]; // Premier ring du polygone
      if (allCoords.length > 0) {
        bounds = {
          minX: Math.min(...allCoords.map((coord: number[]) => coord[0])),
          maxX: Math.max(...allCoords.map((coord: number[]) => coord[0])),
          minY: Math.min(...allCoords.map((coord: number[]) => coord[1])),
          maxY: Math.max(...allCoords.map((coord: number[]) => coord[1]))
        };
      }
    }
    
    const parcelleData = {
      geometry: {
        type: 'Polygon',
        coordinates: coordinates
      },
      properties: {
        id_parcelle: parcelle.id_parcelle,
        commune: parcelle.commune,
        section: parcelle.section,
        numero: parcelle.numero,
        surface_m2: parcelle.surface_m2
      },
      bounds: bounds
    };
    
    return (
      <div className="w-full max-w-4xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Aperçu de la parcelle */}
          <div className="lg:col-span-2">
            <ParcelleMapPreview parcelle={parcelleData} />
          </div>

          {/* Informations */}
          <div className="space-y-4">
            <div className="bg-white p-4 border rounded-lg">
              <h3 className="font-medium text-gray-900 mb-3">Informations parcelle</h3>
              
              <div className="space-y-2 text-sm">
                {parcelle.id_parcelle && (
                  <div>
                    <span className="text-gray-500">ID Parcelle:</span>
                    <span className="ml-2 font-mono">{parcelle.id_parcelle}</span>
                  </div>
                )}
                
                <div>
                  <span className="text-gray-500">Surface:</span>
                  <span className="ml-2">{parcelle.surface_m2?.toFixed(0)} m²</span>
                  {parcelle.surface_ha && (
                    <span className="text-gray-400"> ({parcelle.surface_ha} ha)</span>
                  )}
                </div>
                
                {parcelle.commune && (
                  <div>
                    <span className="text-gray-500">Commune:</span>
                    <span className="ml-2">{parcelle.commune}</span>
                  </div>
                )}
                
                <div>
                  <span className="text-gray-500">Source:</span>
                  <span className="ml-2 uppercase text-xs bg-gray-100 px-1 rounded">
                    {parcelle.source}
                  </span>
                </div>
              </div>
              
              {/* Topographie */}
              {parcelle.topographie && (
                <div className="mt-4 pt-4 border-t">
                  <h4 className="font-medium text-gray-700 mb-2">Topographie</h4>
                  <div className="space-y-1 text-sm text-gray-600">
                    {parcelle.topographie.denivele_m && (
                      <div>Dénivelé: {parcelle.topographie.denivele_m}m</div>
                    )}
                    {parcelle.topographie.pente_moyenne_pct && (
                      <div>Pente moyenne: {parcelle.topographie.pente_moyenne_pct}%</div>
                    )}
                    {parcelle.topographie.terrassement_complexite && (
                      <div>
                        Terrassement: 
                        <span className={`ml-1 px-1 rounded text-xs ${
                          parcelle.topographie.terrassement_complexite === 'faible' 
                            ? 'bg-green-100 text-green-700'
                            : parcelle.topographie.terrassement_complexite === 'modere'
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-red-100 text-red-700'
                        }`}>
                          {parcelle.topographie.terrassement_complexite}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="space-y-2">
              <button
                onClick={confirmParcelle}
                className="w-full flex items-center justify-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                Confirmer cette parcelle
              </button>
              
              <button
                onClick={resetUpload}
                className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
              >
                Recommencer
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // État Error - Affichage erreur
  if (state.status === 'error') {
    return (
      <div className="w-full max-w-md mx-auto text-center">
        <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Erreur lors du traitement
        </h3>
        
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
          <p className="text-sm text-red-600">{state.error}</p>
        </div>
        
        {state.error?.includes('FORMAT_NOT_SUPPORTED') && (
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-4">
            <AlertCircle className="h-5 w-5 text-blue-500 mx-auto mb-2" />
            <p className="text-sm text-blue-600">
              Pour les fichiers PDF ou TIFF, utilisez la saisie d'adresse pour localiser votre parcelle.
            </p>
          </div>
        )}
        
        <div className="space-y-2">
          <button
            onClick={resetUpload}
            className="w-full flex items-center justify-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
          >
            Essayer un autre fichier
          </button>
          
          <p className="text-xs text-gray-500">
            Besoin d'aide ? Consultez les formats supportés ci-dessus.
          </p>
        </div>
      </div>
    );
  }

  return null;
};

export default CadastreUpload;