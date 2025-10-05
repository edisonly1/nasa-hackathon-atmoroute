import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MapPin } from "lucide-react";

interface SidebarProps {
  activeView: string;
  setActiveView: (view: string) => void;
  lat: string;
  lon: string;
  setLat: (lat: string) => void;
  setLon: (lon: string) => void;
  isDroppingPin: boolean;
  setIsDroppingPin: (isDropping: boolean) => void;
}

const Sidebar = ({ activeView, setActiveView, lat, lon, setLat, setLon, isDroppingPin, setIsDroppingPin }: SidebarProps) => {
  const [duration, setDuration] = useState("1d");
  const [customDuration, setCustomDuration] = useState("");

  return (
    <aside className="w-full md:w-80 bg-white border-r p-4 flex flex-col space-y-6 overflow-y-auto">
      <Tabs value={activeView} onValueChange={setActiveView} className="flex flex-col flex-grow">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="corridor">Event Corridor</TabsTrigger>
          <TabsTrigger value="poe">Point PoE</TabsTrigger>
        </TabsList>
        <TabsContent value="corridor" className="flex-grow mt-4 space-y-6">
          <div>
            <h3 className="font-semibold mb-2 text-gray-800">Time</h3>
            <div className="space-y-2">
              <div>
                <Label htmlFor="start-time">Start (UTC)</Label>
                <Input id="start-time" type="datetime-local" />
              </div>
              <div>
                <Label htmlFor="duration">Duration</Label>
                <Select value={duration} onValueChange={setDuration}>
                  <SelectTrigger id="duration"><SelectValue placeholder="Select duration" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1d">1 day</SelectItem>
                    <SelectItem value="3d">3 days</SelectItem>
                    <SelectItem value="5d">5 days</SelectItem>
                    <SelectItem value="7d">7 days</SelectItem>
                    <SelectItem value="14d">14 days</SelectItem>
                    <SelectItem value="custom">Custom</SelectItem>
                  </SelectContent>
                </Select>
                {duration === 'custom' && (
                  <div className="mt-2">
                    <Input
                      id="custom-duration"
                      type="number"
                      placeholder="Enter days (1-30)"
                      min="1"
                      max="30"
                      value={customDuration}
                      onChange={(e) => setCustomDuration(e.target.value)}
                    />
                    <p className="text-xs text-muted-foreground mt-1">Max 30 days.</p>
                  </div>
                )}
              </div>
              <div className="text-sm text-muted-foreground pt-2">
                Step: Daily
              </div>
            </div>
          </div>
          <Thresholds />
        </TabsContent>
        <TabsContent value="poe" className="flex-grow mt-4 space-y-6">
          <div>
            <h3 className="font-semibold mb-2 text-gray-800">Point</h3>
            <div className="space-y-2">
              <Button 
                variant={isDroppingPin ? "secondary" : "outline"} 
                size="sm" 
                className="w-full"
                onClick={() => setIsDroppingPin(!isDroppingPin)}
              >
                <MapPin className="mr-2 h-4 w-4" /> 
                {isDroppingPin ? "Click on map to place pin..." : "Drop Pin on Map"}
              </Button>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <Label htmlFor="lat">Latitude</Label>
                  <Input id="lat" placeholder="e.g., 34.05" value={lat} onChange={(e) => setLat(e.target.value)} />
                </div>
                <div>
                  <Label htmlFor="lon">Longitude</Label>
                  <Input id="lon" placeholder="e.g., -118.25" value={lon} onChange={(e) => setLon(e.target.value)} />
                </div>
              </div>
            </div>
          </div>
          <div>
            <h3 className="font-semibold mb-2 text-gray-800">Date Window</h3>
            <div className="space-y-2">
              <div>
                <Label htmlFor="date">Date</Label>
                <Input id="date" type="date" />
              </div>
              <div>
                <Label htmlFor="window">Window (days)</Label>
                <Input id="window" type="number" placeholder="e.g., 14" />
              </div>
            </div>
          </div>
          <Thresholds />
        </TabsContent>
      </Tabs>
    </aside>
  );
};

const Thresholds = () => (
  <div>
    <h3 className="font-semibold mb-2 text-gray-800">Thresholds</h3>
    <div className="space-y-2">
      <div>
        <Label htmlFor="precip">Precip (mm/day)</Label>
        <Input id="precip" placeholder="e.g., 10" />
      </div>
      <div>
        <Label htmlFor="wind">Wind (mph)</Label>
        <Input id="wind" placeholder="e.g., 20" />
      </div>
      <div>
        <Label htmlFor="rh">RH (%)</Label>
        <Input id="rh" placeholder="e.g., 80" />
      </div>
      <div>
        <Label htmlFor="heat-index">Heat Index (°F)</Label>
        <Input id="heat-index" placeholder="e.g., 95" />
      </div>
    </div>
  </div>
);

export default Sidebar;