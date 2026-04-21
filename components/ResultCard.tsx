import Image from "next/image";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

type ResultCardProps = {
  disease: string;
  confidence: number;
  previewSrc: string;
  uncertain?: boolean;
};

function getStatus(disease: string, confidence: number) {
  const score = Math.round(confidence * 100);

  if (/healthy/i.test(disease)) {
    return { label: "Healthy", className: "bg-green-100 text-green-700 border-green-200" };
  }

  if (score < 75) {
    return {
      label: "Monitor Closely",
      className: "bg-yellow-100 text-yellow-800 border-yellow-200",
    };
  }

  return {
    label: "Disease Detected",
    className: "bg-red-100 text-red-700 border-red-200",
  };
}

export function ResultCard({ disease, confidence, previewSrc, uncertain = false }: ResultCardProps) {
  const confidencePercent = Math.round(confidence * 100);
  const status = getStatus(disease, confidence);

  return (
    <Card className="border-green-100">
      <CardHeader>
        <CardTitle className="text-xl text-gray-900">Scan Result</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="overflow-hidden rounded-xl border border-gray-200">
          {previewSrc ? (
            <Image
              src={previewSrc}
              alt="Captured leaf sample"
              width={640}
              height={360}
              className="h-44 w-full object-cover md:h-56"
              unoptimized
            />
          ) : (
            <div className="flex h-44 items-center justify-center bg-gray-100 text-sm text-gray-500 md:h-56">
              No preview image available
            </div>
          )}
        </div>

        <div className="space-y-2">
          <p className="text-sm text-gray-500">Detected condition</p>
          <h2 className="text-2xl font-semibold text-green-700">{disease}</h2>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline" className={status.className}>
              {status.label}
            </Badge>
            {uncertain && (
              <Badge variant="outline" className="border-yellow-200 bg-yellow-100 text-yellow-800">
                Low Confidence
              </Badge>
            )}
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Confidence score</span>
            <span className="font-medium text-gray-800">{confidencePercent}%</span>
          </div>
          <Progress value={confidencePercent} aria-label="Prediction confidence score" />
        </div>
      </CardContent>
    </Card>
  );
}
