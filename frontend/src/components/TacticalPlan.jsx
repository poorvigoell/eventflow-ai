import { ShieldAlert, Map as MapIcon } from 'lucide-react';
import { Card, MetricBox } from './ui/components';

export function TacticalPlan({ data }) {
  if (!data || !data.tactical) return null;

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-20">
      <h2 className="text-2xl font-black mb-6 flex items-center gap-2 border-b border-white/10 pb-4">
        <ShieldAlert className="text-[#00d2ff]" size={28} /> Tactical Deployment Plan
      </h2>

      {/* Primary Responders */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <MetricBox title="Police Personnel" value={data.tactical.manpower.traffic_police} colorClass="text-[#00d2ff] bg-blue-500/10" emoji="👮" infoText="Deployment size is dynamically based on the number of critical traffic bottlenecks and the predicted incident severity." />
        <MetricBox title="Patrol Vehicles" value={data.tactical.manpower.patrol_vehicles} colorClass="text-[#3a7bd5] bg-blue-600/10" emoji="🚓" infoText="Calculated to ensure enough vehicles are available to monitor the surrounding road networks and potential spillover zones." />
      </div>

      {/* Support & Logistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricBox title="Ambulance" value={data.tactical.manpower.ambulances} colorClass="text-[#00e676] bg-green-500/10" emoji="🚑" infoText="We allocate enough medical units to safely cover the predicted emergency demand, ensuring at least one unit is always on standby." />
        <MetricBox title="Tow Trucks" value={data.tactical.manpower.tow_trucks} colorClass="text-[#ffbb00] bg-yellow-500/10" emoji="🚜" infoText="Dispatched proportionally to the expected volume of vehicle breakdowns or illegal parking." />
        <MetricBox title="Barricades" value={data.tactical.manpower.barricade_teams} colorClass="text-[#ff4b2b] bg-red-500/10" emoji="🚧" infoText="One team is assigned to physically close off or redirect traffic at every identified critical bottleneck." />
      </div>

      <div className="grid grid-cols-2 gap-6 mt-8">
        <Card>
          <h3 className="text-lg font-bold text-[#ff4b2b] mb-4">🚧 Active Barricade Protocol</h3>
          <div className="space-y-3">
            {data.tactical.barricade_roads?.length > 0 ? (
              data.tactical.barricade_roads.map((road, i) => (
                <div key={i} className="bg-red-500/5 border border-red-500/20 p-3 rounded-lg flex flex-col gap-1">
                  <div className="flex justify-between items-start">
                    <span className="font-semibold text-white">{road.road}</span>
                    <span className="text-[10px] bg-red-500 text-white px-2 py-0.5 rounded uppercase font-bold">{road.timing}</span>
                  </div>
                  <span className="text-xs text-gray-400">{road.reason}</span>
                </div>
              ))
            ) : (
              <div className="flex flex-col items-center justify-center p-8 text-gray-500 bg-red-500/5 rounded-lg border border-red-500/10 h-full">
                <ShieldAlert className="mb-3 opacity-50 text-[#ff4b2b]" size={32} />
                <p className="text-sm font-bold text-gray-400">No Barricades Needed</p>
                <p className="text-xs text-center mt-1 text-gray-500">Incident severity does not require road closures.</p>
              </div>
            )}
          </div>
        </Card>

        <Card>
          <h3 className="text-lg font-bold text-[#00d2ff] mb-4">🧭 Routing & Diversion Protocol</h3>
          <div className="space-y-3">
            {data.tactical.diversion_plan?.length > 0 ? (
              data.tactical.diversion_plan.map((div, i) => (
                <div key={i} className="bg-blue-500/5 border border-blue-500/20 p-3 rounded-lg">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-bold text-gray-300">Alternate Route</span>
                    <span className="text-xs text-[#00d2ff] font-mono">{div.added_time} delay</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="line-through text-red-400">{div.from}</span>
                    <span className="text-gray-500">→</span>
                    <span className="text-[#00e676] font-bold">via {div.via}</span>
                    <span className="text-gray-500">→</span>
                    <span className="text-white">{div.to}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="flex flex-col items-center justify-center p-8 text-gray-500 bg-blue-500/5 rounded-lg border border-blue-500/10 h-full">
                <MapIcon className="mb-3 opacity-50 text-[#00d2ff]" size={32} />
                <p className="text-sm font-bold text-gray-400">No Diversions Needed</p>
                <p className="text-xs text-center mt-1 text-gray-500">Traffic flow remains within capacity parameters.</p>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
