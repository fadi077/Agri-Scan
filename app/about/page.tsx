import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function AboutPage() {
  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-10 sm:px-6">
      <section className="glass-card rounded-3xl p-6 md:p-8">
        <h1 className="section-title">About Agri Scan</h1>
        <p className="mt-3 max-w-3xl text-sm text-gray-700 md:text-base">
          Agri Scan is an AI-powered crop health assistant built to help farmers identify leaf
          diseases faster and make safer decisions in the field. It combines mobile-first camera
          scanning, model confidence checks, and practical treatment guidance to reduce delayed
          diagnosis and unnecessary pesticide use.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <Card className="glass-card rounded-2xl">
          <CardHeader>
            <CardTitle className="text-lg text-green-700">Our Mission</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-gray-700">
            <p>
              Support small and medium farmers with early disease detection using accessible AI.
            </p>
            <p>
              Improve crop outcomes by encouraging targeted action instead of blanket chemical use.
            </p>
          </CardContent>
        </Card>

        <Card className="glass-card rounded-2xl">
          <CardHeader>
            <CardTitle className="text-lg text-green-700">Who It Helps</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-gray-700">
            <p>Farmers and field workers needing quick on-site crop checks.</p>
            <p>Agricultural cooperatives running large-area disease monitoring.</p>
            <p>Students and researchers validating real-world crop health workflows.</p>
          </CardContent>
        </Card>
      </section>

      <Card className="glass-card rounded-2xl">
        <CardHeader>
          <CardTitle className="text-lg text-green-700">How Agri Scan Works</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-gray-700">
          <p>1. Select crop type, capture a leaf image, and submit the scan.</p>
          <p>2. The backend model analyzes the image and returns confidence-scored predictions.</p>
          <p>
            3. The app highlights top likely conditions, flags low-confidence results, and suggests
            next actions.
          </p>
          <p>
            4. Farmers can add field notes/location and download a report for follow-up decisions.
          </p>
        </CardContent>
      </Card>

      <section className="grid gap-4 md:grid-cols-2">
        <Card className="rounded-2xl border-amber-200 bg-amber-50">
          <CardHeader>
            <CardTitle className="text-lg text-amber-900">Model Limitations</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-amber-900">
            <p>Prediction quality depends on image clarity, lighting, and crop fit.</p>
            <p>Non-leaf or poor-quality images may be rejected for safety.</p>
            <p>
              AI confidence can vary in real field environments, so uncertain results require
              re-scan and validation.
            </p>
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-blue-200 bg-blue-50">
          <CardHeader>
            <CardTitle className="text-lg text-blue-900">Responsible Use</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-blue-900">
            <p>Agri Scan provides decision support, not final medical/agronomic diagnosis.</p>
            <p>Always verify treatment plans with local agricultural experts.</p>
            <p>
              Use confidence scores, top predictions, and field observations together before
              applying pesticides.
            </p>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
