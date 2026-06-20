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
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] p-3 rounded-lg shadow-2xl">
          <p className="text-[var(--color-text-main)] font-bold mb-1">{label}</p>
          <p className="text-sm font-bold text-[var(--color-accent)]">+{payload[0].value} incidents</p>
          <p className="text-[var(--color-text-muted)] text-xs mt-1 uppercase">{data.phase}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full h-full min-h-[200px] flex flex-col">
      <h3 className="text-xs uppercase tracking-widest text-[var(--color-accent)] mb-2 font-bold">Predicted Traffic Build-up Timeline</h3>
      <p className="text-xs text-[var(--color-text-muted)] opacity-80 mb-4 pr-4 leading-relaxed">
        Timeline is generated as inflow, steady, and exodus phases using predicted incidents, event time, and duration.
      </p>
      <div className="flex-1 min-h-[160px] w-full">
        <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
          <AreaChart data={data} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorIncidents" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--color-accent)" stopOpacity={0.5}/>
                <stop offset="95%" stopColor="var(--color-accent)" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
            <XAxis dataKey="time" stroke="var(--color-text-muted)" tick={{fill: 'var(--color-text-muted)', fontSize: 10}} />
            <YAxis stroke="var(--color-text-muted)" tick={{fill: 'var(--color-text-muted)', fontSize: 10}} />
            <Tooltip content={<CustomTooltip />} />
            <Area type="monotone" dataKey="incidents" stroke="var(--color-accent)" strokeWidth={3} fillOpacity={1} fill="url(#colorIncidents)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
