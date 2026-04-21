import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import type { TopPrediction } from "@/lib/api";
import { normalizeDiseaseName } from "@/lib/treatments";

type TopPredictionsProps = {
  predictions: TopPrediction[];
};

export function TopPredictions({ predictions }: TopPredictionsProps) {
  if (!predictions.length) return null;

  return (
    <Card className="border-green-100">
      <CardHeader>
        <CardTitle className="text-lg text-green-700">Most Likely Conditions</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {predictions.slice(0, 3).map((item, index) => {
          const label = normalizeDiseaseName(item.disease);
          const percent = Math.round(item.confidence * 100);
          return (
            <div key={`${item.class_id}-${index}`} className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <p className="font-medium text-gray-700">
                  {index + 1}. {label}
                </p>
                <p className="text-gray-600">{percent}%</p>
              </div>
              <Progress value={percent} />
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
