export const Card = ({ children, className = "" }) => (
  <div className={`bg-white/5 border border-white/10 p-4 rounded-xl shadow-lg backdrop-blur-sm ${className}`}>
    {children}
  </div>
);

export const MetricBox = ({ title, value, colorClass, subtitle }) => (
  <Card className="text-center">
    {subtitle && <div className="text-[10px] text-gray-400 uppercase tracking-wider mb-1">{subtitle}</div>}
    <div className={`text-3xl font-black ${colorClass}`}>{value}</div>
    <div className="text-xs text-gray-400 mt-1 uppercase font-semibold">{title}</div>
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
