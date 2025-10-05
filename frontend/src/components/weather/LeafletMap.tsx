import { MapContainer, TileLayer, Marker, useMap, useMapEvents, FeatureGroup } from 'react-leaflet';
import { EditControl } from 'react-leaflet-draw';
import L from 'leaflet';
import 'leaflet-draw';
import { useEffect } from 'react';

// Fix for leaflet-draw initialization error
L.drawLocal.draw.toolbar.buttons.polyline = 'Draw a route';
L.drawLocal.draw.toolbar.buttons.polygon = 'Draw an area';
L.drawLocal.draw.handlers.polyline.tooltip.start = 'Click to start drawing route.';
L.drawLocal.draw.handlers.polyline.tooltip.cont = 'Click to continue drawing route.';
L.drawLocal.draw.handlers.polyline.tooltip.end = 'Click last point to finish route.';
L.drawLocal.draw.handlers.polygon.tooltip.start = 'Click to start drawing area.';
L.drawLocal.draw.handlers.polygon.tooltip.cont = 'Click to continue drawing area.';
L.drawLocal.draw.handlers.polygon.tooltip.end = 'Click first point to close this area.';
L.drawLocal.edit.toolbar.actions.save.title = 'Save changes.';
L.drawLocal.edit.toolbar.actions.save.text = 'Save';
L.drawLocal.edit.toolbar.actions.cancel.title = 'Cancel editing, discards all changes.';
L.drawLocal.edit.toolbar.actions.cancel.text = 'Cancel';
L.drawLocal.edit.toolbar.buttons.edit = 'Edit layers.';
L.drawLocal.edit.toolbar.buttons.editDisabled = 'No layers to edit.';
L.drawLocal.edit.toolbar.buttons.remove = 'Delete layers.';
L.drawLocal.edit.toolbar.buttons.removeDisabled = 'No layers to delete.';
L.drawLocal.edit.handlers.edit.tooltip.text = 'Drag handles, or marker to edit feature.';
L.drawLocal.edit.handlers.edit.tooltip.subtext = 'Click cancel to undo changes.';
L.drawLocal.edit.handlers.remove.tooltip.text = 'Click on a feature to remove';

// Fix for default icon issue with bundlers like Vite
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

interface MapControllerProps {
  markerPosition: [number, number] | null;
}

const MapController = ({ markerPosition }: MapControllerProps) => {
  const map = useMap();
  useEffect(() => {
    if (markerPosition) {
      map.setView(markerPosition, map.getZoom());
    }
  }, [markerPosition, map]);
  return null;
};

interface MapEventsProps {
    onMapClick: (latlng: L.LatLng) => void;
    isDroppingPin: boolean;
}

const MapEvents = ({ onMapClick, isDroppingPin }: MapEventsProps) => {
    useMapEvents({
        click(e) {
            if (isDroppingPin) {
                onMapClick(e.latlng);
            }
        },
    });
    return null;
};

interface LeafletMapProps {
    markerPosition?: [number, number] | null;
    onMapClick?: (latlng: L.LatLng) => void;
    isDroppingPin?: boolean;
    drawingEnabled?: boolean;
}

const LeafletMap = ({ markerPosition, onMapClick, isDroppingPin, drawingEnabled = false }: LeafletMapProps) => {
  const initialCenter: [number, number] = [34.05, -118.25];

  return (
    <div className={`h-full w-full rounded-lg overflow-hidden border ${isDroppingPin ? 'cursor-crosshair' : ''}`}>
      <MapContainer center={initialCenter} zoom={10} scrollWheelZoom={true} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {drawingEnabled && (
          <FeatureGroup>
            <EditControl
              position="topright"
              draw={{
                rectangle: false,
                polygon: true,
                polyline: true,
                circle: false,
                circlemarker: false,
                marker: false,
              }}
            />
          </FeatureGroup>
        )}

        {markerPosition && <Marker position={markerPosition} />}
        {onMapClick && isDroppingPin !== undefined && <MapEvents onMapClick={onMapClick} isDroppingPin={isDroppingPin} />}
        <MapController markerPosition={markerPosition} />
        <div className="leaflet-bottom leaflet-right">
          <div className="leaflet-control leaflet-bar bg-white p-2 rounded-md shadow-lg">
            <h4 className="font-bold text-xs mb-1">EVS Legend</h4>
            <div className="flex items-center space-x-2">
              <span className="text-xs" style={{color: '#D14343'}}>0</span>
              <div className="w-24 h-2 rounded-full" style={{background: 'linear-gradient(to right, #D14343, #10B981)'}}></div>
              <span className="text-xs" style={{color: '#10B981'}}>100</span>
            </div>
          </div>
        </div>
      </MapContainer>
    </div>
  );
};

export default LeafletMap;