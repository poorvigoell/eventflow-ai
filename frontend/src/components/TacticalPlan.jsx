import { ShieldAlert, Map as MapIcon, Info } from 'lucide-react';
import { Card, MetricBox } from './ui/components';

export function TacticalPlan({ data }) {
  if (!data || !data.tactical) return null;

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-20">
      <h2 className="text-2xl font-bold mb-6 flex items-center gap-2 border-b border-white/10 pb-4">
        <ShieldAlert className="text-[#00d2ff]" size={28} /> Tactical Deployment Plan
      </h2>

      {/* Primary Responders */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <MetricBox title="Police Personnel" value={data.tactical.manpower.traffic_police} infoText={<span><strong>Formula:</strong> max(4, 2 + (Junctions × 3) + (Incidents × 0.25))</span>} />
        <MetricBox title="Patrol Vehicles" value={data.tactical.manpower.patrol_vehicles} infoText={<span><strong>Formula:</strong> max(1, 1 + (Junctions × 0.4) + (Incidents × 0.05))</span>} />
      </div>

      {/* Support & Logistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricBox title="Ambulance" value={data.tactical.manpower.ambulances} infoText={<span><strong>Formula:</strong> max(1, round(Incidents × 0.12))</span>} />
        <MetricBox title="Tow Trucks" value={data.tactical.manpower.tow_trucks} infoText={<span><strong>Formula:</strong> max(0, round(Incidents × 0.07))</span>} />
        <MetricBox title="Barricades" value={data.tactical.manpower.barricade_teams} infoText={<span><strong>Formula:</strong> max(1, Critical Junctions)</span>} />
      </div>

      <div className="grid grid-cols-2 gap-6 mt-8">
        <Card className="overflow-visible">
          <div className="flex items-center gap-2 mb-4">
            <h3 className="text-lg font-bold text-[var(--color-accent)] m-0">Active Barricade Protocol</h3>
            <div className="group relative flex items-center ml-2 z-50">
              <div className="flex items-center justify-center transition duration-200 hover:scale-110">
                <Info size={16} className="text-[var(--color-accent)] cursor-help" />
              </div>
              <div className="absolute top-full mt-2 left-0 w-64 p-3.5 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl shadow-xl text-[13px] leading-5 text-[var(--color-text-main)] font-normal z-50 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 pointer-events-none normal-case tracking-normal">
                Barricade assignments are determined by evaluating the Risk Score of each intersection. An intersection is closed if its incident severity threatens secondary network cascades.
              </div>
            </div>
          </div>
          <div className="space-y-3">
            {data.tactical.barricade_roads?.length > 0 ? (
              data.tactical.barricade_roads.map((road, i) => (
                <div key={i} className="bg-[var(--color-surface-hover)] border border-[var(--color-border)] p-3 rounded-lg flex flex-col gap-1">
                  <div className="flex justify-between items-start">
                    <span className="font-semibold text-[var(--color-text-main)]">{road.road}</span>
                    <span className="text-[10px] bg-[var(--color-accent)] text-[var(--color-base)] px-2 py-0.5 rounded uppercase font-bold">{road.timing}</span>
                  </div>
                  <span className="text-xs text-[var(--color-text-muted)]">{road.reason}</span>
                </div>
              ))
            ) : (
              <div className="flex flex-col items-center justify-center p-8 text-[var(--color-text-muted)] bg-[var(--color-surface-hover)] rounded-lg border border-[var(--color-border)] h-full">
                <ShieldAlert className="mb-3 opacity-50 text-[var(--color-accent)]" size={32} />
                <p className="text-sm font-bold text-[var(--color-text-muted)]">No Barricades Needed</p>
                <p className="text-xs text-center mt-1 text-[var(--color-text-muted)]">Incident severity does not require road closures.</p>
              </div>
            )}
          </div>
        </Card>

        <Card className="overflow-visible">
          <div className="flex items-center gap-2 mb-4">
            <h3 className="text-lg font-bold text-[var(--color-accent)] m-0">Routing & Diversion Protocol</h3>
            <div className="group relative flex items-center ml-2 z-50">
              <div className="flex items-center justify-center transition duration-200 hover:scale-110">
                <Info size={16} className="text-[var(--color-accent)] cursor-help" />
              </div>
              <div className="absolute top-full mt-2 right-0 w-64 p-3.5 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl shadow-xl text-[13px] leading-5 text-[var(--color-text-main)] font-normal z-50 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 pointer-events-none normal-case tracking-normal">
                Diversions calculate the fastest alternative path bypassing barricades, using Dijkstra's algorithm on the real-time road network weights.
              </div>
            </div>
          </div>
          <div className="space-y-3">
            {data.tactical.diversion_plan?.length > 0 ? (
              data.tactical.diversion_plan.map((div, i) => (
                <div key={i} className="bg-[var(--color-surface-hover)] border border-[var(--color-border)] p-3 rounded-lg">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-bold text-[var(--color-text-muted)]">Alternate Route</span>
                    <span className="text-xs text-[var(--color-accent)] font-mono">{div.added_time} delay</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="line-through text-[var(--color-text-muted)] opacity-70">{div.from}</span>
                    <span className="text-[var(--color-text-muted)]">→</span>
                    <span className="text-[var(--color-accent)] font-bold">via {div.via}</span>
                    <span className="text-[var(--color-text-muted)]">→</span>
                    <span className="text-[var(--color-text-main)]">{div.to}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="flex flex-col items-center justify-center p-8 text-[var(--color-text-muted)] bg-[var(--color-surface-hover)] rounded-lg border border-[var(--color-border)] h-full">
                <MapIcon className="mb-3 opacity-50 text-[var(--color-accent)]" size={32} />
                <p className="text-sm font-bold text-[var(--color-text-muted)]">No Diversions Needed</p>
                <p className="text-xs text-center mt-1 text-[var(--color-text-muted)]">Traffic flow remains within capacity parameters.</p>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
