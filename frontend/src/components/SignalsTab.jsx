import React from 'react';
import { Card } from './ui/components';
import { Radio } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer } from 'recharts';

export const SignalsTab = ({ signals }) => {
  if (!signals || signals.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-gray-500">
        <Radio size={48} className="mb-4 opacity-50" />
        <h2 className="text-xl font-bold text-gray-300">No Signal Data</h2>
        <p>Run analysis to generate adaptive signal timings.</p>
      </div>
    );
  }

  // Format data for Recharts
  const chartData = signals.map(s => ({
    name: s.junction_name.substring(0, 15) + (s.junction_name.length > 15 ? '...' : ''),
    greenMain: s.phase_a_green_sec,
    greenCross: s.phase_b_green_sec,
  }));

  return (
    <div className="flex-1 max-w-5xl mx-auto space-y-6 w-full">
      <h2 className="text-2xl font-black mb-6 flex items-center gap-2 border-b border-white/10 pb-4">
        <Radio className="text-[#00d2ff]" size={28}/> Adaptive Signal Control
      </h2>
      
      <div className="bg-blue-500/10 border-l-4 border-[#00d2ff] p-4 rounded-lg mb-6">
        <h5 className="text-[#00d2ff] font-bold uppercase tracking-wider text-xs mb-1">How this works</h5>
        <p className="text-sm text-gray-300">This module dynamically alters the green-light timing at critical junctions surrounding the venue to actively flush traffic based on the current event phase.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          {signals.map((rec, i) => {
            const green_pct = rec.phase_a_green_sec / rec.cycle_length_sec;
            return (
              <Card key={i} className="hover:border-white/20 transition-all">
                <div className="flex justify-between items-center mb-3">
                  <strong className="text-white font-bold">{rec.junction_name}</strong>
                  <span className="text-[#00d2ff] text-sm font-mono bg-blue-500/10 px-2 py-1 rounded">Cycle: {rec.cycle_length_sec}s</span>
                </div>
                
                {/* Progress bar */}
                <div className="flex h-3 rounded overflow-hidden mb-2 shadow-inner">
                  <div style={{ width: `${green_pct * 100}%` }} className="bg-[#00d2ff] shadow-[0_0_8px_#00d2ff]"></div>
                  <div style={{ width: `${(1 - green_pct) * 100}%` }} className="bg-[#c77dff] shadow-[0_0_8px_#c77dff]"></div>
                </div>
                
                <div className="flex justify-between text-xs text-gray-400 mb-3 font-mono">
                  <span>Main: {rec.phase_a_green_sec}s</span>
                  <span>Cross: {rec.phase_b_green_sec}s</span>
                </div>
                
                <div className="text-sm text-[#00d2ff] bg-blue-500/5 p-2 rounded border border-blue-500/10">
                  {rec.recommendation}
                </div>
              </Card>
            );
          })}
        </div>

        <div className="relative">
          <div className="sticky top-6">
            <Card className="h-[500px] flex flex-col">
              <h3 className="text-sm font-bold text-gray-300 mb-4 uppercase tracking-wider">Green Split Optimization</h3>
              <div className="flex-1 w-full relative">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
                    <XAxis type="number" stroke="#666" tick={{fill: '#888', fontSize: 10}} />
                    <YAxis dataKey="name" type="category" stroke="#666" tick={{fill: '#888', fontSize: 10}} width={100} />
                    <RechartsTooltip 
                      contentStyle={{ backgroundColor: '#111', borderColor: 'rgba(255,255,255,0.1)' }}
                      itemStyle={{ color: '#fff' }}
                    />
                    <Legend wrapperStyle={{ fontSize: '12px' }}/>
                    <Bar dataKey="greenMain" name="Main Route Green (s)" stackId="a" fill="#00d2ff" radius={[0, 0, 0, 4]} />
                    <Bar dataKey="greenCross" name="Cross Route Green (s)" stackId="a" fill="#c77dff" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};
