import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
        <p className="mt-2 text-gray-600">
          Track your progress with detailed competency maps
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Competency Map</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex h-64 items-center justify-center text-gray-400">
              Radar Chart Placeholder
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Progress Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex h-64 items-center justify-center text-gray-400">
              Line Chart Placeholder
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Weak Concepts Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span>Reported Speech</span>
              <span className="text-sm text-red-600">45% mastery</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Conditionals</span>
              <span className="text-sm text-orange-600">55% mastery</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Word Formation</span>
              <span className="text-sm text-yellow-600">65% mastery</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
