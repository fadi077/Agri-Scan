import { Loader2 } from "lucide-react";

type LoadingOverlayProps = {
  label?: string;
};

export function LoadingOverlay({ label = "Analyzing leaf..." }: LoadingOverlayProps) {
  return (
    <div className="absolute inset-0 z-20 flex flex-col items-center justify-center rounded-2xl bg-black/45">
      <Loader2 className="h-10 w-10 animate-spin text-white" aria-hidden="true" />
      <p className="mt-3 text-sm font-medium text-white">{label}</p>
    </div>
  );
}
