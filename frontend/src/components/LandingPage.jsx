import React from 'react';

export const LandingPage = ({ onEnter }) => {
  return (
    <div className="min-h-screen flex flex-col justify-center relative overflow-hidden bg-[#050505]">
      
      {/* Background Image Layer */}
      <div 
        className="absolute inset-0 z-0"
        style={{
          backgroundImage: "url('/green-light-bg.jpg')",
          backgroundSize: '950px', // Increased size
          backgroundPosition: '85% center', // Moved slightly to the left
          backgroundRepeat: 'no-repeat'
        }}
      />

      {/* Ambient Pulsing Glow behind the light */}
      <div className="absolute inset-0 z-0 bg-[radial-gradient(circle_at_85%_center,_rgba(118,255,3,0.15),_transparent_50%)] animate-[pulse_4s_ease-in-out_infinite]" />

      {/* Seamless Gradient Overlay Layer */}
      <div className="absolute inset-0 z-0 bg-gradient-to-r from-[#050505] via-[#050505]/95 to-transparent w-full md:w-[80%]" />

      {/* Tech Grid Overlay */}
      <div className="absolute inset-0 z-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAwIDEwMCBMIDEwMCAxMDAgTCAxMDAgMCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJyZ2JhKDI1NSwyNTUsMjU1LDAuMDMpIiBzdHJva2Utd2lkdGg9IjEiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz48L3N2Zz4=')] opacity-30 pointer-events-none" />

      {/* Content Layer */}
      <div className="z-10 text-left space-y-6 max-w-2xl pl-8 md:pl-24 lg:pl-40 pt-10">
        <div className="flex justify-start mb-2">
          {/* Changed color to lime green to match the light */}
          <span className="text-sm font-bold text-[#76ff03] tracking-[0.2em] uppercase drop-shadow-md">EventFlow</span>
        </div>

        <h1 className="text-5xl md:text-7xl font-bold text-white tracking-tight leading-[1.1] drop-shadow-xl">
          PREDICTING<br/>INCIDENT SURGES
        </h1>
        
        <p className="text-lg text-gray-300 font-medium leading-relaxed max-w-lg drop-shadow-lg">
          City-Scale Traffic & Crowd Simulation Platform. We foresee gridlocks and optimize emergency dispatch before chaos happens.
        </p>

        <div className="pt-6">
          <button 
            onClick={onEnter}
            className="group relative px-8 py-4 bg-[#76ff03] font-bold text-black uppercase tracking-widest text-sm rounded transition-all duration-300 hover:bg-[#64dd17] hover:shadow-[0_0_20px_rgba(118,255,3,0.4)]"
          >
            Launch Dashboard
          </button>
        </div>
      </div>
    </div>
  );
};
