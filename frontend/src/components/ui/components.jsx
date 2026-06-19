import { Info } from 'lucide-react';

export const Card = ({ children, className = "" }) => (
  <div className={`bg-gradient-to-br from-[var(--color-surface)] to-[var(--color-base)] border border-[var(--color-border)] p-4 rounded-xl shadow-2xl backdrop-blur-sm ${className}`}>
    {children}
  </div>
);

export const MetricBox = ({ title, value, colorClass, subtitle, emoji, infoText }) => {
  const valueColor = colorClass || "text-[var(--color-accent)]";
  return (
    <Card className="text-center relative py-8 px-6 flex flex-col items-center justify-center min-h-[160px] hover:z-50 transition-all duration-300 hover:scale-[1.02] hover:shadow-[0_10px_40px_rgba(0,0,0,0.8)] border-t-2 border-t-[var(--color-accent)] overflow-hidden group">
      <div className="absolute inset-0 bg-gradient-to-t from-[var(--color-accent)]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
      {infoText && (
        <div className="absolute top-4 left-4 text-[var(--color-text-muted)] hover:text-[var(--color-text-main)] cursor-help z-50">
          <Info size={16} />
          <div className="hidden group-hover:block absolute top-full left-0 mt-2 w-64 p-3 bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded shadow-2xl text-xs text-left text-[var(--color-text-main)] z-50 normal-case tracking-normal font-medium leading-relaxed">
            {infoText}
          </div>
        </div>
      )}
      {emoji && <div className="text-4xl mb-3 drop-shadow-lg z-10">{emoji}</div>}
      {subtitle && <div className="text-xs text-[var(--color-text-muted)] uppercase tracking-wider mb-2 mt-2 font-bold z-10">{subtitle}</div>}
      <div className={`text-5xl font-bold ${valueColor} mb-3 z-10`}>{value}</div>
      <div className="text-sm text-[var(--color-text-muted)] mt-1 uppercase font-bold tracking-widest z-10">{title}</div>
    </Card>
  );
};

export const TabButton = ({ active, icon, label, onClick }) => (
  <button
    onClick={onClick}
    className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-all w-full md:w-auto justify-center ${active
        ? 'border-[var(--color-accent)] text-[var(--color-accent)] bg-[var(--color-surface)]'
        : 'border-transparent text-[var(--color-text-muted)] hover:text-[var(--color-text-main)] hover:bg-[var(--color-surface-hover)]'
      }`}
  >
    {icon}
    <span className="font-semibold text-sm">{label}</span>
  </button>
);
