import LeafletMap from "./LeafletMap";
import EvsTimelineCard from "./EvsTimelineCard";
import CoverageCard from "./CoverageCard";
import BestTimeCard from "./BestTimeCard";

const EventCorridorView = () => {
  return (
    <div className="flex flex-col h-full space-y-4">
      <div className="flex-grow relative min-h-[300px] md:min-h-[400px]">
        <LeafletMap drawingEnabled={true} />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <EvsTimelineCard />
        <CoverageCard />
        <BestTimeCard />
      </div>
    </div>
  );
};

export default EventCorridorView;