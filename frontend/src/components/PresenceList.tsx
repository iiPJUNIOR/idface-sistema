import type { Presence } from '../services/api';
import { Clock, CheckCircle } from 'lucide-react';

export function PresenceList({ presence }: { presence: Presence[] }) {
  if (presence.length === 0) {
    return (
      <div className="text-center py-20 glass-card rounded-3xl">
        <div className="w-24 h-24 bg-indigo-500/10 rounded-full flex items-center justify-center mx-auto mb-6 shadow-inner animate-pulse">
          <Clock className="w-12 h-12 text-indigo-400/50" />
        </div>
        <p className="text-xl font-heading font-semibold text-slate-300 mb-2">Sem registros</p>
        <p className="text-slate-500">Aguardando marcações de presença para hoje.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {presence.map((p, idx) => (
        <div key={p.id} className="group flex items-center gap-5 p-5 glass-card rounded-2xl hover:-translate-y-1 hover:shadow-2xl hover:shadow-indigo-500/10 transition-all duration-300 animate-slide-in relative overflow-hidden" style={{ animationDelay: `${idx * 40}ms` }}>
          <div className="absolute inset-x-0 bottom-0 h-0.5 bg-gradient-to-r from-emerald-500 to-indigo-500 scale-x-0 group-hover:scale-x-100 transition-transform origin-left duration-500"></div>
          
          <div className="relative">
            <div className="w-14 h-14 bg-gradient-to-br from-emerald-500/20 to-teal-500/20 rounded-2xl flex items-center justify-center border border-emerald-500/20 rotate-3 group-hover:-rotate-3 transition-transform duration-300">
              <CheckCircle className="w-7 h-7 text-emerald-400 drop-shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-lg sm:text-xl font-heading font-semibold text-white tracking-tight truncate">{p.name}</p>
            <p className="text-xs sm:text-sm font-medium text-slate-400">Mat: {p.registration}</p>
          </div>
          <div className="text-right shrink-0">
             <div className="bg-white/5 rounded-xl px-3 py-1.5 sm:px-4 sm:py-2 border border-white/5 flex flex-col items-center">
                <p className="text-base sm:text-lg font-bold text-white font-mono tracking-wider drop-shadow-sm">
                  {new Date(p.created_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                </p>
                {p.entries_count > 1 && (
                  <p className="text-[10px] sm:text-xs font-semibold text-indigo-400 uppercase tracking-wider mt-0.5">{p.entries_count} ACESSOS</p>
                )}
             </div>
          </div>
        </div>
      ))}
      <style>{`
        @keyframes slideIn {
          from { opacity: 0; transform: translateX(-20px); }
          to { opacity: 1; transform: translateX(0); }
        }
        .animate-slide-in { animation: slideIn 0.4s ease-out forwards; opacity: 0; }
      `}</style>
    </div>
  );
}
