import React from 'react';
import { Card } from './ui/components';
import { Radio } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer } from 'recharts';

export const SignalsTab = ({ signals }) => {
  if (!signals || signals.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-[var(--color-text-muted)]">
        <Radio size={48} className="mb-4 opacity-50 text-[var(--color-accent)]" />
        <h2 className="text-xl font-bold text-[var(--color-text-main)]">No Signal Data</h2>
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
      <h2 className="text-2xl font-bold mb-6 flex items-center gap-2 border-b border-[var(--color-border)] pb-4">
        <Radio className="text-[var(--color-accent)]" size={28}/> Adaptive Signal Control
      </h2>
      
      <div className="bg-[var(--color-surface-hover)] border-l-4 border-[var(--color-accent)] p-4 rounded-lg mb-6 shadow-2xl">
        <h5 className="text-[var(--color-accent)] font-bold uppercase tracking-wider text-xs mb-1">How this works</h5>
        <p className="text-sm text-[var(--color-text-main)]">This module dynamically alters the green-light timing at critical junctions surrounding the venue to actively flush traffic based on the current event phase.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          {signals.map((rec, i) => {
            const green_pct = rec.phase_a_green_sec / rec.cycle_length_sec;
            return (
              <Card key={i} className="hover:border-[var(--color-accent)] transition-all bg-[var(--color-surface)]">
                <div className="flex justify-between items-center mb-3">
                  <strong className="text-[var(--color-text-main)] font-bold">{rec.junction_name}</strong>
                  <span className="text-[var(--color-accent)] text-sm font-mono bg-[var(--color-base)] px-2 py-1 rounded">Cycle: {rec.cycle_length_sec}s</span>
                </div>
                
                {/* Progress bar */}
                <div className="flex h-3 rounded overflow-hidden mb-2 shadow-inner">
                  <div style={{ width: `${green_pct * 100}%`, backgroundColor: 'var(--color-accent)' }} className="shadow-2xl"></div>
                  <div style={{ width: `${(1 - green_pct) * 100}%`, backgroundColor: 'var(--color-surface-hover)' }} className="shadow-inner"></div>
                </div>
                
                <div className="flex justify-between text-xs text-[var(--color-text-muted)] mb-3 font-mono">
                  <span className="text-[var(--color-text-main)]">Main: {rec.phase_a_green_sec}s</span>
                  <span className="text-[var(--color-text-main)] opacity-70">Cross: {rec.phase_b_green_sec}s</span>
                </div>
                
                <div className="text-sm text-[var(--color-text-main)] bg-[var(--color-base)] p-2 rounded border border-[var(--color-border)]">
                  {rec.recommendation}
                </div>
              </Card>
            );
          })}
        </div>

        <div className="relative">
          <div className="sticky top-6">
            <Card className="h-[500px] flex flex-col bg-[var(--color-surface)]">
              <h3 className="text-sm font-bold text-[var(--color-text-muted)] mb-4 uppercase tracking-wider">Green Split Optimization</h3>
              <div className="flex-1 w-full relative">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" horizontal={false} />
                    <XAxis type="number" stroke="var(--color-text-muted)" tick={{fill: 'var(--color-text-muted)', fontSize: 10}} />
                    <YAxis dataKey="name" type="category" stroke="var(--color-text-muted)" tick={{fill: 'var(--color-text-muted)', fontSize: 10}} width={100} />
                    <RechartsTooltip 
                      cursor={false}
                      contentStyle={{ backgroundColor: 'var(--color-surface-hover)', borderColor: 'var(--color-border)' }}
                      itemStyle={{ color: 'var(--color-text-main)' }}
                    />
                    <Legend wrapperStyle={{ fontSize: '12px' }}/>
                    <Bar dataKey="greenMain" name="Main Route Green (s)" stackId="a" fill="var(--color-accent)" radius={[0, 0, 0, 4]} barSize={24} />
                    <Bar dataKey="greenCross" name="Cross Route Green (s)" stackId="a" fill="rgba(255, 255, 255, 0.4)" radius={[0, 4, 4, 0]} barSize={24} />
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
