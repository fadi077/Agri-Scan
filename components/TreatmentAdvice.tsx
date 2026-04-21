import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { treatmentAdvice } from "@/lib/treatments";

type TreatmentAdviceProps = {
  disease: string;
};

export function TreatmentAdvice({ disease }: TreatmentAdviceProps) {
  const tips = treatmentAdvice[disease] ?? [
    "Consult your local agriculture extension officer for a field-specific treatment plan.",
    "Monitor neighboring plants and isolate visibly affected leaves quickly.",
  ];

  return (
    <Card className="border-green-100">
      <CardHeader>
        <CardTitle className="text-lg text-green-700">Treatment Recommendations</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="list-disc space-y-2 pl-5 text-sm text-gray-700">
          {tips.map((tip) => (
            <li key={tip}>{tip}</li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
