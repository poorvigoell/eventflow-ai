import React from 'react';
import { Activity } from 'lucide-react';

export const LandingPage = ({ onEnter }) => {
  return (
    <div className="min-h-screen bg-[#050505] flex flex-col items-center justify-center relative overflow-hidden">
      {/* Sleek Gradient Background */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-to-tr from-[#00d2ff]/20 to-[#3a7bd5]/20 rounded-full blur-[120px] pointer-events-none" />
      
      <div className="z-10 text-center space-y-8 p-8 max-w-3xl">
        <div className="flex justify-center mb-6">
          <div className="bg-white/5 p-4 rounded-2xl border border-white/10 shadow-[0_0_50px_rgba(0,210,255,0.2)]">
            <Activity className="text-[#00d2ff]" size={64} />
          </div>
        </div>

        <h1 className="text-6xl font-black bg-clip-text text-transparent bg-gradient-to-r from-[#00d2ff] to-[#c77dff] tracking-tight">
          EventFlow AI
        </h1>
        
        <p className="text-xl text-gray-400 font-medium leading-relaxed">
          City-Scale Traffic & Crowd Simulation Platform. <br/>
          Predicting incident surges before they happen.
        </p>

        <div className="pt-8">
          <button 
            onClick={onEnter}
            className="group relative px-8 py-4 bg-transparent font-bold text-white uppercase tracking-widest text-sm overflow-hidden rounded-full border border-white/20 hover:border-[#00d2ff]/50 transition-all duration-300"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-[#00d2ff]/20 to-[#3a7bd5]/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out" />
            <span className="relative flex items-center gap-2">
              Launch Dashboard <Activity size={16} />
            </span>
          </button>
        </div>
      </div>
      
      {/* Subtle grid pattern overlay */}
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAwIDEwMCBMIDEwMCAxMDAgTCAxMDAgMCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJyZ2JhKDI1NSwyNTUsMjU1LDAuMDMpIiBzdHJva2Utd2lkdGg9IjEiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz48L3N2Zz4=')] opacity-50 pointer-events-none" />
    </div>
  );
};
