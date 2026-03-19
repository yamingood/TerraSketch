# TerraSketch — Intégration IGN (Institut National de l'Information Géographique)

## Contexte

L'intégration IGN permet d'enrichir automatiquement les données cadastrales uploadées dans TerraSketch avec des informations géographiques officielles françaises, notamment :

- **Données altimétriques** précises (MNT RGE)
- **Occupation du sol** (OCS GE)
- **Données administratives** (géocodage inverse)
- **Imagerie aérienne** haute résolution
- **Réseaux de transport** et hydrographie

---

## APIs IGN intégrées

### 1. **Géoplateforme IGN** - API principale
- **Base URL** : `https://wxs.ign.fr/{apikey}/`
- **Services** : WMS, WMTS, WFS pour cartes et données vectorielles
- **Documentation** : https://geoservices.ign.fr/documentation/web/

### 2. **API Géocodage** - Adresses et coordonnées
- **Base URL** : `https://wxs.ign.fr/{apikey}/geoportail/geocodage/`
- **Services** : Géocodage direct/inverse, autocomplétion
- **Formats** : JSON, XML

### 3. **API Altimétrie** - Modèle Numérique de Terrain
- **Base URL** : `https://wxs.ign.fr/{apikey}/alti/`
- **Services** : Altitude ponctuelle, profil altimétrique
- **Précision** : 1 mètre (RGE ALTI)

### 4. **API Données vectorielles** - Occupation du sol
- **Base URL** : `https://wxs.ign.fr/{apikey}/wfs`
- **Couches** : OCS GE, BD TOPO, parcellaire
- **Format** : GeoJSON, GML

---

## Authentification et limites

### Clé API IGN
```bash
# Variable d'environnement requise
IGN_API_KEY=your_ign_api_key_here

# Obtenir une clé gratuite (2M requêtes/mois)
# https://geoservices.ign.fr/services-web-libres
```

### Quotas et limitations
- **Gratuit** : 2 000 000 requêtes/mois
- **Rate limit** : 100 requêtes/seconde
- **Payant** : Au-delà selon grille tarifaire
- **Cache obligatoire** : Données IGN peuvent être mises en cache 24h

---

## Architecture d'intégration TerraSketch

### Service principal : `apps/geography/services/ign_service.py`

```python
class IGNService:
    """Service d'intégration IGN pour enrichissement géographique"""
    
    def __init__(self):
        self.api_key = settings.IGN_API_KEY
        self.base_urls = {
            'geocoding': f'https://wxs.ign.fr/{self.api_key}/geoportail/geocodage/',
            'elevation': f'https://wxs.ign.fr/{self.api_key}/alti/',
            'wfs': f'https://wxs.ign.fr/{self.api_key}/wfs',
            'wmts': f'https://wxs.ign.fr/{self.api_key}/wmts'
        }
    
    async def enrich_parcelle_data(self, geojson_parcelle):
        """Enrichissement complet d'une parcelle cadastrale"""
        
    async def get_elevation_profile(self, coordinates):
        """Profil altimétrique détaillé"""
        
    async def get_land_cover(self, polygon):
        """Occupation du sol OCS GE"""
        
    async def reverse_geocode(self, lat, lon):
        """Géocodage inverse pour adresse normalisée"""
```

### Modèle étendu : `apps/cadastre/models.py`

```python
class ParcelEnrichment(models.Model):
    """Données d'enrichissement IGN pour une parcelle"""
    
    parcel_id = models.CharField(max_length=50, unique=True)
    
    # Données altimétriques IGN
    elevation_min = models.FloatField(help_text="Altitude min (m) - IGN RGE ALTI")
    elevation_max = models.FloatField(help_text="Altitude max (m) - IGN RGE ALTI") 
    elevation_profile = models.JSONField(help_text="Profil altimétrique détaillé")
    slope_analysis = models.JSONField(help_text="Analyse des pentes")
    
    # Occupation du sol OCS GE
    land_cover_data = models.JSONField(help_text="OCS GE - occupation détaillée")
    vegetation_cover_pct = models.FloatField(help_text="% couverture végétale")
    artificial_cover_pct = models.FloatField(help_text="% surfaces artificialisées")
    water_cover_pct = models.FloatField(help_text="% surfaces en eau")
    
    # Données administratives
    address_normalized = models.CharField(max_length=255, help_text="Adresse IGN normalisée")
    insee_code = models.CharField(max_length=5, help_text="Code INSEE commune")
    department = models.CharField(max_length=3, help_text="Département")
    region = models.CharField(max_length=2, help_text="Région")
    
    # Contexte géographique
    distance_to_water = models.FloatField(help_text="Distance cours d'eau (m)")
    distance_to_road = models.FloatField(help_text="Distance route principale (m)")
    urban_density = models.CharField(max_length=20, help_text="Densité urbaine")
    climate_zone_ign = models.CharField(max_length=50, help_text="Zone climatique IGN")
    
    # Métadonnées
    enriched_at = models.DateTimeField(auto_now_add=True)
    ign_data_version = models.CharField(max_length=20, help_text="Version données IGN")
    cache_expires_at = models.DateTimeField(help_text="Expiration cache IGN (24h)")
```

---

## Flux d'enrichissement automatique

### 1. **Trigger : Upload cadastral**
```python
# apps/cadastre/uploads/handlers.py
async def handle_cadastre_upload(cadastre_file, user_id):
    """Gestionnaire upload avec enrichissement IGN automatique"""
    
    # 1. Parse cadastral standard
    result = parse_cadastre_file(cadastre_file)
    
    # 2. Enrichissement IGN asynchrone
    if settings.IGN_ENRICHMENT_ENABLED:
        enrich_with_ign.delay(result['id_parcelle'], result['geojson'])
    
    return result
```

### 2. **Tâche asynchrone Celery**
```python
# apps/geography/tasks.py
from celery import shared_task

@shared_task(bind=True, max_retries=3)
def enrich_with_ign(self, parcel_id, geojson_data):
    """Enrichissement IGN en arrière-plan"""
    try:
        ign_service = IGNService()
        
        # 1. Profil altimétrique
        elevation_data = await ign_service.get_elevation_profile(
            geojson_data['geometry']['coordinates'][0]
        )
        
        # 2. Occupation du sol
        land_cover = await ign_service.get_land_cover(
            geojson_data['geometry']
        )
        
        # 3. Géocodage inverse
        centroid = calculate_centroid(geojson_data['geometry'])
        address_data = await ign_service.reverse_geocode(
            centroid['lat'], centroid['lon']
        )
        
        # 4. Sauvegarde enrichissement
        ParcelEnrichment.objects.update_or_create(
            parcel_id=parcel_id,
            defaults={
                'elevation_min': elevation_data['min'],
                'elevation_max': elevation_data['max'],
                'elevation_profile': elevation_data['profile'],
                'land_cover_data': land_cover,
                'address_normalized': address_data['address'],
                'insee_code': address_data['insee'],
                # ...
                'cache_expires_at': timezone.now() + timedelta(hours=24)
            }
        )
        
        # 5. Notification temps réel (WebSocket)
        channel_layer = get_channel_layer()
        await channel_layer.group_send(f"parcel_{parcel_id}", {
            'type': 'ign_enrichment_complete',
            'data': {
                'status': 'completed',
                'elevation_data': elevation_data,
                'land_cover': land_cover
            }
        })
        
    except Exception as exc:
        # Retry avec backoff exponentiel
        self.retry(countdown=60 * (2 ** self.request.retries))
```

### 3. **API endpoint enrichi**
```python
# apps/cadastre/views.py
class CadastreUploadView(APIView):
    def post(self, request):
        # Upload standard
        result = handle_cadastre_upload(cadastre_file, user_id)
        
        # Vérifier enrichissement IGN existant
        try:
            enrichment = ParcelEnrichment.objects.get(
                parcel_id=result['id_parcelle'],
                cache_expires_at__gt=timezone.now()
            )
            result['ign_data'] = {
                'status': 'available',
                'elevation': {
                    'min': enrichment.elevation_min,
                    'max': enrichment.elevation_max,
                    'profile': enrichment.elevation_profile
                },
                'land_cover': enrichment.land_cover_data,
                'address': enrichment.address_normalized
            }
        except ParcelEnrichment.DoesNotExist:
            result['ign_data'] = {
                'status': 'processing',
                'estimated_completion': '2-5 minutes'
            }
        
        return Response(result, status=201)
```

---

## Exemple de réponse enrichie IGN

```json
{
  "id_parcelle": "750560000AB0012",
  "surface_m2": 312.5,
  "commune": "Paris",
  "source": "geojson",
  "geojson": {
    "type": "Feature",
    "geometry": {"type": "Polygon", "coordinates": [...]},
    "properties": {"surface_m2": 312.5}
  },
  "ign_data": {
    "status": "available",
    "data_version": "2024.1",
    "elevation": {
      "min": 32.1,
      "max": 35.8,
      "average": 33.9,
      "profile": [
        {"distance": 0, "elevation": 32.1},
        {"distance": 10, "elevation": 33.2},
        {"distance": 20, "elevation": 35.8}
      ],
      "slope_analysis": {
        "max_slope_pct": 12.3,
        "average_slope_pct": 4.2,
        "areas": [
          {"slope_range": "0-5%", "area_pct": 78.5},
          {"slope_range": "5-15%", "area_pct": 21.5}
        ]
      }
    },
    "land_cover": {
      "ocs_ge_version": "2022",
      "categories": [
        {"code": "211", "label": "Zones résidentielles", "area_pct": 45.2},
        {"code": "131", "label": "Espaces verts urbains", "area_pct": 54.8}
      ],
      "vegetation_cover_pct": 54.8,
      "artificial_cover_pct": 45.2,
      "water_cover_pct": 0.0
    },
    "address": {
      "normalized": "12 Rue de la Paix, 75001 Paris",
      "insee_code": "75101",
      "department": "75",
      "region": "11",
      "quality_score": 0.95
    },
    "geographic_context": {
      "distance_to_water_m": 1250,
      "distance_to_major_road_m": 89,
      "urban_density": "dense",
      "climate_zone": "Océanique dégradé (Cfb)"
    }
  },
  "recommendations": {
    "terrain_preparation": "Terrassement léger nécessaire (pente max 12%)",
    "drainage": "Bon drainage naturel - pas d'intervention requise",
    "plant_compatibility": [
      "Végétation urbaine adaptée",
      "Sols anthropisés - amendement organique recommandé"
    ]
  }
}
```

---

## Configuration et déploiement

### Settings Django
```python
# config/settings/base.py

# IGN Integration
IGN_API_KEY = os.getenv('IGN_API_KEY')
IGN_ENRICHMENT_ENABLED = True
IGN_CACHE_DURATION = 24 * 60 * 60  # 24 heures

# Rate limiting IGN
IGN_REQUESTS_PER_SECOND = 10
IGN_DAILY_QUOTA = 100000  # Monitoring quota
```

### Cache Redis pour IGN
```python
# Cache dédié pour données IGN
CACHES = {
    'default': {...},
    'ign_cache': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/2',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'TIMEOUT': 86400,  # 24h cache IGN
    }
}
```

### Monitoring et alertes
```python
# Monitoring quota IGN
class IGNUsageTracker:
    def track_request(self, endpoint, success=True):
        cache.incr(f'ign_usage_daily_{datetime.now().date()}')
        
    def check_quota_remaining(self):
        daily_usage = cache.get(f'ign_usage_daily_{datetime.now().date()}', 0)
        return settings.IGN_DAILY_QUOTA - daily_usage
```

---

## Interface utilisateur

### Indicateur de statut dans CadastreUpload
```typescript
// terrasketch-front/src/components/CadastreUpload.tsx

interface IGNEnrichment {
  status: 'processing' | 'available' | 'error';
  elevation?: ElevationData;
  landCover?: LandCoverData;
  estimatedCompletion?: string;
}

const IGNStatusIndicator: React.FC<{ignData: IGNEnrichment}> = ({ignData}) => {
  if (ignData.status === 'processing') {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded p-3">
        <div className="flex items-center">
          <Loader className="h-4 w-4 text-blue-600 animate-spin mr-2" />
          <span className="text-blue-800 text-sm">
            Enrichissement IGN en cours... ({ignData.estimatedCompletion})
          </span>
        </div>
      </div>
    );
  }
  
  if (ignData.status === 'available') {
    return (
      <div className="bg-green-50 border border-green-200 rounded p-3">
        <h4 className="text-green-800 font-medium mb-2">✅ Données IGN disponibles</h4>
        <div className="text-sm space-y-1">
          <div>🏔️ Altitude: {ignData.elevation?.min}m - {ignData.elevation?.max}m</div>
          <div>🌿 Végétation: {ignData.landCover?.vegetation_cover_pct}%</div>
          <div>📍 Adresse: {ignData.address?.normalized}</div>
        </div>
      </div>
    );
  }
  
  return null;
};
```

---

## Tests et validation

### Tests unitaires
```python
# apps/geography/tests/test_ign_service.py
class IGNServiceTest(TestCase):
    def setUp(self):
        self.ign_service = IGNService()
        self.test_coordinates = [[2.3522, 48.8566], [2.3532, 48.8576]]
    
    @patch('apps.geography.services.ign_service.httpx.AsyncClient')
    async def test_elevation_profile_success(self, mock_client):
        """Test profil altimétrique IGN"""
        
    @patch('apps.geography.services.ign_service.httpx.AsyncClient')  
    async def test_land_cover_extraction(self, mock_client):
        """Test extraction occupation du sol"""
        
    def test_quota_monitoring(self):
        """Test monitoring quota IGN"""
```

### Fichiers de test
```
apps/geography/tests/fixtures/
├── ign_elevation_response.json
├── ign_landcover_response.json
├── ign_geocoding_response.json
└── sample_parcel_75001.geojson
```

---

## Migration et données existantes

### Script de migration
```python
# scripts/migrate_ign_enrichment.py
"""Script pour enrichir les parcelles existantes avec IGN"""

def migrate_existing_parcels():
    """Enrichissement batch des parcelles existantes"""
    parcels = get_parcels_without_ign_data()
    
    for parcel in parcels:
        enrich_with_ign.delay(parcel.id, parcel.geojson_data)
        time.sleep(0.1)  # Rate limiting
```

---

## Roadmap et évolutions

### Phase 1 (MVP) ✅
- [x] Intégration API Altimétrie
- [x] Intégration API Géocodage inverse
- [x] Cache 24h des données IGN
- [x] Enrichissement asynchrone

### Phase 2 (Q2 2024)
- [ ] API Occupation du sol OCS GE complète
- [ ] Intégration imagerie satellite
- [ ] Analyse automatique pentes et exposition
- [ ] Recommandations plantes selon microclimat

### Phase 3 (Q3 2024)
- [ ] Intégration réseaux (eau, électricité)
- [ ] Analyse pollution et nuisances sonores
- [ ] Données météo historiques Météo-France
- [ ] Prédictions climatiques locales

---

## Contact et support

**Équipe TerraSketch** - Intégration IGN
- 📧 Contact : dev@terrasketch.fr
- 📚 Documentation IGN : https://geoservices.ign.fr/
- 🔑 Clé API IGN : https://geoservices.ign.fr/services-web-libres
- 💬 Support IGN : assistance-geoportail@ign.fr