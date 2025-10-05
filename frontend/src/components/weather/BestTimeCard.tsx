import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const BestTimeCard = () => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Best Time</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-24 flex items-center justify-center bg-gray-100 rounded-md">
          <p className="text-xs text-muted-foreground">Best time info will be here.</p>
        </div>
      </CardContent>
    </Card>
  );
};

export default BestTimeCard;