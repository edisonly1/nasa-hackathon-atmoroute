import { useState } from "react";
import Header from "@/components/weather/Header";
import Sidebar from "@/components/weather/Sidebar";
import EventCorridorView from "@/components/weather/EventCorridorView";
import PointPoeView from "@/components/weather/PointPoeView";

const Index = () => {
  const [activeView, setActiveView] = useState("corridor");
  const [lat, setLat] = useState("34.05");
  const [lon, setLon] = useState("-118.25");
  const [isDroppingPin, setIsDroppingPin] = useState(false);

  return (
    <div className="flex flex-col md:flex-row h-screen bg-gray-50 font-sans text-sm text-gray-900">
      <Sidebar
        activeView={activeView}
        setActiveView={setActiveView}
        lat={lat}
        lon={lon}
        setLat={setLat}
        setLon={setLon}
        isDroppingPin={isDroppingPin}
        setIsDroppingPin={setIsDroppingPin}
      />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          {activeView === "corridor" ? (
            <EventCorridorView />
          ) : (
            <PointPoeView
              lat={lat}
              lon={lon}
              setLat={setLat}
              setLon={setLon}
              isDroppingPin={isDroppingPin}
              setIsDroppingPin={setIsDroppingPin}
            />
          )}
        </main>
      </div>
    </div>
  );
};

export default Index;