import React from 'react';

const LegendItem = ({ icon, label }) => (
  <div className="flex items-center gap-4 py-1">
    <div className="shrink-0 flex items-center justify-center scale-110">{icon}</div>
    <span className="text-xs font-bold uppercase tracking-widest text-[var(--color-text-main)]">{label}</span>
  </div>
);

export default function MapLegend({ items }) {
  return (
    <div className="bg-[var(--color-surface)]/90 backdrop-blur-md border border-[var(--color-border)] rounded-xl p-5 shadow-xl flex-1">
      <h3 className="text-xs font-bold uppercase tracking-[0.24em] text-[var(--color-text-muted)] mb-4">Map Legend</h3>
      <div className="flex flex-col gap-2">
        {items.map((item) => (
          <LegendItem key={item.label} icon={item.icon} label={item.label} />
        ))}
      </div>
    </div>
  );
}
