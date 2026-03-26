import type { LucideIcon } from 'lucide-react';

interface StatCardProps {
  icon: LucideIcon;
  label: string;
  value: number;
  colorClass: string;
  bgClass: string;
}

export function StatCard({ icon: Icon, label, value, colorClass, bgClass }: StatCardProps) {
  return (
    <div className="glass-panel rounded-2xl p-4 sm:p-6 relative overflow-hidden group hover:-translate-y-1 transition-transform duration-300">
      <div className={`absolute -right-6 -top-6 w-32 h-32 rounded-full blur-3xl opacity-20 group-hover:opacity-40 transition-opacity duration-500 bg-gradient-to-br ${colorClass}`}></div>
      
      <div className="flex items-center justify-between relative z-10">
        <div>
          <p className="text-3xl sm:text-4xl font-heading font-bold text-white mb-1 group-hover:scale-105 transition-transform origin-left">{value}</p>
          <p className="text-xs sm:text-sm font-medium text-slate-400 uppercase tracking-wider">{label}</p>
        </div>
        <div className={`w-12 h-12 sm:w-14 sm:h-14 bg-gradient-to-br ${bgClass} rounded-2xl flex items-center justify-center shadow-lg border border-white/10 group-hover:rotate-6 transition-transform duration-300`}>
          <Icon className={`w-6 h-6 sm:w-7 sm:h-7 text-white`} />
        </div>
      </div>
    </div>
  );
}
