import { Info } from 'lucide-react';

export const Card = ({ children, className = "" }) => (
  <div className={`bg-white/5 border border-white/10 p-4 rounded-xl shadow-lg backdrop-blur-sm ${className}`}>
    {children}
  </div>
);

export const MetricBox = ({ title, value, colorClass, subtitle, emoji, infoText }) => (
  <Card className="text-center relative py-8 px-6 flex flex-col items-center justify-center min-h-[160px] hover:z-50 transition-all duration-300 hover:scale-[1.02] hover:shadow-2xl">
    {infoText && (
      <div className="absolute top-3 left-3 text-gray-500 hover:text-white cursor-help group">
        <Info size={16} />
        <div className="hidden group-hover:block absolute top-full left-0 mt-2 w-64 p-3 bg-[#1a1a1a] border border-white/10 rounded shadow-2xl text-xs text-left text-gray-300 z-50 normal-case tracking-normal font-medium leading-relaxed">
          {infoText}
        </div>
      </div>
    )}
    {emoji && <div className="text-4xl mb-3 drop-shadow-lg">{emoji}</div>}
    {subtitle && <div className="text-xs text-gray-400 uppercase tracking-wider mb-2 mt-2 font-bold">{subtitle}</div>}
    <div className={`text-6xl font-black ${colorClass} mb-3`}>{value}</div>
    <div className="text-sm text-gray-300 mt-1 uppercase font-bold tracking-widest">{title}</div>
  </Card>
);

export const TabButton = ({ active, icon, label, onClick }) => (
  <button
    onClick={onClick}
    className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-all w-full md:w-auto justify-center ${
      active 
        ? 'border-[#00d2ff] text-[#00d2ff] bg-white/5' 
        : 'border-transparent text-gray-400 hover:text-white hover:bg-white/5'
    }`}
  >
    {icon}
    <span className="font-semibold text-sm">{label}</span>
  </button>
);
