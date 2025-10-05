import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";

const Header = () => {
  return (
    <header className="flex items-center justify-between p-4 bg-white border-b shrink-0">
      <div className="flex items-center">
        <h1 className="text-lg font-semibold" style={{ color: '#0B3D91' }}>
          Will It Rain On My Parade?
        </h1>
      </div>
      <div className="flex items-center space-x-2">
        <Button style={{ backgroundColor: '#0B3D91', color: 'white' }}>Run</Button>
        <Button variant="outline">
          <Download className="mr-2 h-4 w-4" />
          Export
        </Button>
      </div>
    </header>
  );
};

export default Header;