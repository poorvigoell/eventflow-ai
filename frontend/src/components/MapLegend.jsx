import React from 'react';

const LegendItem = ({ icon, label, description }) => (
  <div className="flex items-center gap-3 rounded-xl bg-white/5 p-3 border border-white/10">
    <div className="shrink-0">{icon}</div>
    <div>
      <p className="text-xs uppercase tracking-[0.24em] text-gray-400 mb-1">{label}</p>
      <p className="text-sm text-white leading-snug">{description}</p>
    </div>
  </div>
);

const dot = (color) => (
  <span className="inline-flex items-center justify-center w-8 h-8 rounded-full border border-white/10" style={{ background: color }} />
);

const line = (color, dashed = false) => (
  <span className="inline-block h-2 w-14 rounded-full border border-white/10" style={{ background: color, borderStyle: dashed ? 'dashed' : 'solid' }} />
);

const circle = (borderColor, fillColor = 'transparent', dashed = false) => (
  <span
    className="inline-flex items-center justify-center w-8 h-8 rounded-full border border-white/10"
    style={{
      borderColor,
      background: fillColor,
      borderStyle: dashed ? 'dashed' : 'solid'
    }}
  />
);

export default function MapLegend({ items }) {
  return (
    <div className="bg-[#0d1320] border border-white/10 rounded-xl p-4">
      <h3 className="text-sm font-semibold uppercase tracking-[0.24em] text-gray-400 mb-4">Map Legend</h3>
      <div className="grid gap-3 sm:grid-cols-2">
        {items.map((item) => (
          <LegendItem key={item.label} icon={item.icon} label={item.label} description={item.description} />
        ))}
      </div>
    </div>
  );
}
