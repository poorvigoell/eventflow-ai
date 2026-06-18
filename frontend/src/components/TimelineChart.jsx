import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export const TimelineChart = ({ timelineData }) => {
  if (!timelineData || timelineData.length === 0) return null;

  // Format data for Recharts
  const data = timelineData.map(item => ({
    time: item.time,
    incidents: item.count,
    phase: item.phase
  }));

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-[#111] border border-white/20 p-3 rounded-lg shadow-xl">
          <p className="text-[#00d2ff] font-bold mb-1">{label}</p>
          <p className="text-white">Incidents: <span className="font-bold text-red-400">{data.incidents}</span></p>
          <p className="text-gray-400 text-xs mt-1 uppercase">{data.phase}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="h-[192px] w-full mt-4 flex flex-col">
      <h3 className="text-sm font-bold text-gray-300 mb-2 uppercase tracking-wider">Incident Surge Timeline</h3>
      <div className="flex-1 w-full relative">
        <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
          <AreaChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorIncidents" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#00d2ff" stopOpacity={0.5}/>
                <stop offset="95%" stopColor="#00d2ff" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis dataKey="time" stroke="#666" tick={{fill: '#888', fontSize: 10}} />
            <YAxis stroke="#666" tick={{fill: '#888', fontSize: 10}} />
            <Tooltip content={<CustomTooltip />} cursor={{stroke: 'rgba(255,255,255,0.2)', strokeWidth: 1}} />
            <Area type="monotone" dataKey="incidents" stroke="#00d2ff" strokeWidth={3} fillOpacity={1} fill="url(#colorIncidents)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
