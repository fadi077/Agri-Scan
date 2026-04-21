import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type FarmerActionPlanProps = {
  confidence: number;
  uncertain?: boolean;
  rejected?: boolean;
};

export function FarmerActionPlan({
  confidence,
  uncertain = false,
  rejected = false,
}: FarmerActionPlanProps) {
  const score = Math.round(confidence * 100);
  const lowConfidence = rejected || uncertain || score < 75;

  const actions = lowConfidence
    ? [
        "Retake photo in daylight with one leaf filling most of the frame.",
        "Avoid spraying immediately; verify symptoms on 2-3 additional leaves.",
        "Consult local agriculture extension support before treatment.",
      ]
    : [
        "Isolate visibly affected plants and monitor nearby leaves daily.",
        "Apply disease-specific treatment according to local guidelines.",
        "Re-scan after 48-72 hours to confirm progression or recovery.",
      ];

  return (
    <Card className="border-green-100 bg-white">
      <CardHeader>
        <CardTitle className="text-lg text-green-700">What To Do Next</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="list-disc space-y-2 pl-5 text-sm text-gray-700">
          {actions.map((action) => (
            <li key={action}>{action}</li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
