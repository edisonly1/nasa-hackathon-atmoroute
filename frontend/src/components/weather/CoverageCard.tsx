import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const CoverageCard = () => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Coverage ≥ Threshold</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-24 flex items-center justify-center bg-gray-100 rounded-md">
          <p className="text-xs text-muted-foreground">Coverage data will be here.</p>
        </div>
      </CardContent>
    </Card>
  );
};

export default CoverageCard;