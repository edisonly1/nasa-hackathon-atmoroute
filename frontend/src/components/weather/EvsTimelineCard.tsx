import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const EvsTimelineCard = () => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">EVS Timeline</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-24 flex items-center justify-center bg-gray-100 rounded-md">
          <p className="text-xs text-muted-foreground">Timeline chart will be here.</p>
        </div>
      </CardContent>
    </Card>
  );
};

export default EvsTimelineCard;