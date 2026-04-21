import { AlertTriangle, RefreshCw } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type InvalidScanNoticeProps = {
  reason?: string | null;
  onRetry?: () => void;
};

export function InvalidScanNotice({ reason, onRetry }: InvalidScanNoticeProps) {
  return (
    <Card className="border-amber-200 bg-amber-50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg text-amber-900">
          <AlertTriangle className="h-5 w-5" />
          Scan Not Reliable Yet
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm text-amber-800">
        <p>{reason ?? "No clear leaf detected. Please capture a cleaner leaf image."}</p>
        <ul className="list-disc space-y-1 pl-5">
          <li>Use daylight and avoid shadows on the leaf.</li>
          <li>Fill at least half the frame with one leaf.</li>
          <li>Hold still and keep focus sharp before scanning.</li>
        </ul>
        {onRetry && (
          <Button onClick={onRetry} className="bg-green-600 text-white hover:bg-green-700">
            <RefreshCw className="mr-2 h-4 w-4" />
            Retake Scan
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
