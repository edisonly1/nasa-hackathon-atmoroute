import LeafletMap from "./LeafletMap";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LatLng } from "leaflet";

interface PointPoeViewProps {
  lat: string;
  lon: string;
  setLat: (lat: string) => void;
  setLon: (lon: string) => void;
  isDroppingPin: boolean;
  setIsDroppingPin: (isDropping: boolean) => void;
}

const PointPoeView = ({ lat, lon, setLat, setLon, isDroppingPin, setIsDroppingPin }: PointPoeViewProps) => {
  const markerLat = parseFloat(lat);
  const markerLon = parseFloat(lon);
  const markerPosition: [number, number] | null = 
    !isNaN(markerLat) && !isNaN(markerLon) ? [markerLat, markerLon] : null;

  const handleMapClick = (latlng: LatLng) => {
    setLat(latlng.lat.toFixed(4));
    setLon(latlng.lng.toFixed(4));
    setIsDroppingPin(false);
  };

  return (
    <div className="flex flex-col h-full space-y-4">
      <div className="flex-grow relative min-h-[300px] md:min-h-[400px]">
        <LeafletMap 
          markerPosition={markerPosition}
          onMapClick={handleMapClick}
          isDroppingPin={isDroppingPin}
        />
      </div>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Point Probability of Exceedance (PoE)</CardTitle>
          <Button variant="outline">Download PoE</Button>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center bg-gray-100 rounded-md">
            <p className="text-muted-foreground">PoE curves, histograms, and stats table will be displayed here.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PointPoeView;