import { ShieldAlert, Map as MapIcon } from 'lucide-react';
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
        <MetricBox title="Police Personnel" value={data.tactical.manpower.traffic_police} emoji="👮" infoText="Deployment size is dynamically based on the number of critical traffic bottlenecks and the predicted incident severity." />
        <MetricBox title="Patrol Vehicles" value={data.tactical.manpower.patrol_vehicles} emoji="🚓" infoText="Calculated to ensure enough vehicles are available to monitor the surrounding road networks and potential spillover zones." />
      </div>

      {/* Support & Logistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricBox title="Ambulance" value={data.tactical.manpower.ambulances} emoji="🚑" infoText="We allocate enough medical units to safely cover the predicted emergency demand, ensuring at least one unit is always on standby." />
        <MetricBox title="Tow Trucks" value={data.tactical.manpower.tow_trucks} emoji="🚜" infoText="Dispatched proportionally to the expected volume of vehicle breakdowns or illegal parking." />
        <MetricBox title="Barricades" value={data.tactical.manpower.barricade_teams} emoji="🚧" infoText="One team is assigned to physically close off or redirect traffic at every identified critical bottleneck." />
      </div>

      <div className="grid grid-cols-2 gap-6 mt-8">
        <Card>
          <h3 className="text-lg font-bold text-[var(--color-accent)] mb-4">🚧 Active Barricade Protocol</h3>
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

        <Card>
          <h3 className="text-lg font-bold text-[var(--color-accent)] mb-4">🧭 Routing & Diversion Protocol</h3>
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
