import React, { useEffect, useRef } from 'react';
import { ArrowRight, Cpu, Activity, Globe } from 'lucide-react';

export const LandingPage = ({ onEnter }) => {
  const vantaRef = useRef(null);

  useEffect(() => {
    let vantaEffect;
    if (window.VANTA && window.VANTA.NET) {
      vantaEffect = window.VANTA.NET({
        el: vantaRef.current,
        mouseControls: true,
        touchControls: true,
        gyroControls: false,
        minHeight: 200.00,
        minWidth: 200.00,
        scale: 1.00,
        scaleMobile: 1.00,
        color: 0x00e676,
        backgroundColor: 0x050505,
        points: 12.00,
        maxDistance: 22.00,
        spacing: 18.00,
        showDots: true
      });
    }
    return () => {
      if (vantaEffect) vantaEffect.destroy();
    };
  }, []);

  return (
    <div ref={vantaRef} className="min-h-screen flex flex-col justify-center relative overflow-hidden bg-[#050505]">

      {/* Seamless Gradient Overlay Layer so text is legible */}
      <div className="absolute inset-0 z-0 bg-gradient-to-r from-[#050505]/90 via-[#050505]/60 to-transparent w-full" />

      {/* Content Layer */}
      <div className="z-10 text-left space-y-8 max-w-3xl pl-8 md:pl-24 lg:pl-40 pt-10">

        {/* Removed Glassmorphism Background Panel */}
        <div className="p-4">

          <div className="flex justify-start mb-6">
            <span className="px-3 py-1 text-xs font-bold text-[#050505] bg-[var(--color-accent)] tracking-[0.2em] uppercase rounded-full shadow-[0_0_15px_rgba(0,230,118,0.5)]">
              EventFlow
            </span>
          </div>

          <h1 className="text-5xl md:text-6xl lg:text-7xl font-extrabold text-white tracking-tighter leading-[1.05] drop-shadow-2xl mb-6">
            PREDICTIVE <br />
            <span className="text-[var(--color-accent)]">
              INCIDENT MITIGATION
            </span>
          </h1>

          <p className="text-lg md:text-xl text-gray-300 font-medium leading-relaxed max-w-xl drop-shadow-lg mb-8">
            City-Scale Traffic & Crowd Simulation Platform. We foresee gridlocks and optimize emergency dispatch before chaos happens.
          </p>

          {/* Feature Badges */}
          <div className="flex flex-wrap gap-3 mb-10">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs font-semibold text-gray-300">
              <Activity size={14} className="text-[var(--color-accent)]" /> Reinforcement Learning
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs font-semibold text-gray-300">
              <Globe size={14} className="text-[var(--color-accent)]" /> Geospatial Networking
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs font-semibold text-gray-300">
              <Cpu size={14} className="text-[var(--color-accent)]" /> 3D Digital Twin
            </div>
          </div>

          <div className="pt-2">
            <button
              onClick={onEnter}
              className="group relative inline-flex items-center gap-3 px-8 py-4 bg-transparent border-2 border-[var(--color-accent)] font-extrabold text-[var(--color-accent)] hover:bg-[var(--color-accent)] hover:text-[#050505] uppercase tracking-widest text-sm rounded-xl transition-all duration-500 overflow-hidden cursor-pointer"
            >
              Launch Dashboard
              <ArrowRight className="w-5 h-5 transition-transform duration-500 group-hover:translate-x-2" />
            </button>
          </div>

        </div>
      </div>
    </div>
  );
};