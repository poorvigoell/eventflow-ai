import React, { useEffect, useState } from 'react';

const markerSample = (color) => (
  <span
    className="inline-flex items-center justify-center w-8 h-8 rounded-full border border-white/15"
    style={{ background: color }}
  />
);

const lineSample = (color, dashed = false) => (
  <span className="inline-flex items-center justify-center w-14 h-6 rounded-xl border border-white/10 bg-white/5 px-2">
    <span
      className="inline-block h-1.5 w-full rounded-full"
      style={{
        background: dashed ? 'transparent' : color,
        boxShadow: dashed ? undefined : `0 0 10px ${color}33`,
        border: `1.5px ${dashed ? 'dashed' : 'solid'} ${color}`
      }}
    />
  </span>
);

const renderLegendIcon = (item) => {
  if (item.type === 'line') {
    return lineSample(item.color, item.dashed);
  }
  return markerSample(item.color);
};

export default function Legend() {
  const [items, setItems] = useState([]);
  const [visibility, setVisibility] = useState({});

  useEffect(() => {
    // load saved visibility from localStorage
    try {
      const saved = localStorage.getItem('overlayVisibility');
      if (saved) setVisibility(JSON.parse(saved));
    } catch (err) {
      console.warn('Failed to load overlay visibility', err);
    }
    const handler = (e) => {
      const payload = e.detail || {};
      const newItems = payload.items || [];
      setItems(newItems);
      // Preserve existing visibility where possible
      setVisibility((prev) => {
        const next = { ...prev };
        newItems.forEach(it => { if (!(it.id in next)) next[it.id] = it.visible !== undefined ? it.visible : true; });
        // remove old keys that no longer exist
        Object.keys(next).forEach(k => { if (!newItems.find(it => it.id === k)) delete next[k]; });
        try { localStorage.setItem('overlayVisibility', JSON.stringify(next)); } catch (err) { /* ignore */ }
        return next;
      });
    };
    window.addEventListener('overlayStateUpdate', handler);
    // request current state in case MapOverlay emitted before Legend mounted
    window.dispatchEvent(new CustomEvent('requestOverlayState'));
    return () => window.removeEventListener('overlayStateUpdate', handler);
  }, []);

  const toggle = (id) => {
    setVisibility((prev) => {
      const next = { ...prev, [id]: !prev[id] };
      try { localStorage.setItem('overlayVisibility', JSON.stringify(next)); } catch (err) { /* ignore */ }
      window.dispatchEvent(new CustomEvent('overlayVisibilityChange', { detail: { id, visible: next[id] } }));
      return next;
    });
  };

  const focus = (id, e) => {
    e && e.stopPropagation();
    window.dispatchEvent(new CustomEvent('overlayFocus', { detail: { id } }));
  };

  // Always render a compact floating legend so it's immediately visible on the map.
  return (
    <div style={{ position: 'absolute', top: 18, left: 18, zIndex: 9999, width: 300, maxHeight: 'calc(100% - 36px)', overflow: 'auto', pointerEvents: 'auto' }}>
      <div className="bg-[var(--color-surface)]/85 backdrop-blur-xl border border-[var(--color-border)]/80 rounded-xl p-3 text-sm text-[var(--color-text-main)] shadow-2xl">
        <div className="flex items-center justify-between mb-2">
          <div className="font-bold text-xs text-[var(--color-text-muted)] uppercase tracking-widest">Map Key</div>
          <div className="text-xs text-[var(--color-text-muted)]">{items.length} items</div>
        </div>
        <div className="flex flex-col gap-2">
          {items.length === 0 && (
            <div className="text-[13px] text-[var(--color-text-muted)]">No overlays currently visible. Try "Refresh Traffic" or "Launch Prediction".</div>
          )}
          {items.map(item => {
            const isVisible = visibility[item.id] ?? item.visible ?? true;
            return (
              <div key={item.id} className="flex items-center gap-3 text-left w-full">
                <button onClick={() => toggle(item.id)} className="flex items-center gap-3 w-full text-left">
                  <div className="shrink-0" style={{ opacity: isVisible ? 1 : 0.35 }}>
                  {renderLegendIcon(item)}
                </div>
                <div className={`text-[13px] text-[var(--color-text-main)] ${isVisible ? '' : 'opacity-50 line-through'}`}>{item.label}</div>
                </button>
                <div className="flex items-center gap-2">
                  <button onClick={(e) => focus(item.id, e)} className="text-xs px-2 py-1 bg-[var(--color-surface)] border border-[var(--color-border)] rounded text-[var(--color-text-muted)] hover:text-[var(--color-text-main)]">Focus</button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
