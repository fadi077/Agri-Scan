import { AlertTriangle } from "lucide-react";

type SafetyDisclaimerProps = {
  compact?: boolean;
};

export function SafetyDisclaimer({ compact = false }: SafetyDisclaimerProps) {
  return (
    <div
      className={`rounded-xl border border-amber-200 bg-amber-50 text-amber-900 ${
        compact ? "p-3 text-xs" : "p-4 text-sm"
      }`}
      role="note"
      aria-label="Safety disclaimer"
    >
      <p className="flex items-start gap-2 font-medium">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
        AI guidance only, not a substitute for agronomist advice.
      </p>
      <p className="mt-2">
        Always verify treatment decisions locally before applying pesticides. Low-confidence
        results should be re-scanned in better lighting or checked by an expert.
      </p>
    </div>
  );
}
