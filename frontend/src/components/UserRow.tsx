import { useState, useEffect } from 'react';
import type { User as UserType } from '../services/api';
import { User, CheckCircle, ShieldOff, ToggleLeft, ToggleRight, AlertCircle, Edit, Trash2, RefreshCw, Upload } from 'lucide-react';
import { api } from '../services/api';

interface UserRowProps {
  user: UserType;
  photoUrl: string;
  onToggleStatus: (user: UserType) => void;
  onEdit: (user: UserType) => void;
  onDelete: (user: UserType) => void;
  onUserUpdated: () => void;
}

export function UserRow({ user, photoUrl, onToggleStatus, onEdit, onDelete, onUserUpdated }: UserRowProps) {
  const [isSynced, setIsSynced] = useState<boolean | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);

  const checkSync = () => {
    if (user.idface_id) {
      api.checkUserSync(user.id).then(result => {
        setIsSynced(result.synced);
      }).catch(() => {
        setIsSynced(false);
      });
    } else {
      setIsSynced(false);
    }
  };

  useEffect(() => {
    checkSync();
  }, [user.id, user.idface_id]);

  const handleSync = async () => {
    setIsSyncing(true);
    try {
      await api.syncUserToIdFace(user.id);
      checkSync();
      onUserUpdated();
    } catch (err) {
      alert('Erro ao sincronizar: ' + (err as Error).message);
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <div className="group glass-card rounded-2xl p-5 hover:bg-white/10 transition-all duration-300 hover:shadow-2xl hover:shadow-emerald-500/10 border border-transparent hover:border-white/10">
      <div className="flex items-start gap-4">
        <div className="relative">
          <div className="w-16 h-16 bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl overflow-hidden flex-shrink-0 border border-white/5 group-hover:border-emerald-500/30 transition-colors shadow-inner">
            {user.has_photo ? (
              <img src={photoUrl} alt={user.name} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" onError={(e) => { console.log('Photo load error for', user.name, photoUrl); (e.target as HTMLImageElement).style.display = 'none'; }} />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <User className="w-7 h-7 text-slate-500" />
              </div>
            )}
          </div>
          <div className={`absolute -bottom-1 -right-1 w-5 h-5 rounded-full flex items-center justify-center border-2 border-slate-900 shadow-sm ${user.active ? 'bg-emerald-500' : 'bg-rose-500'}`}>
            {user.active ? <CheckCircle className="w-3 h-3 text-white" /> : <ShieldOff className="w-3 h-3 text-white" />}
          </div>
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-heading font-semibold text-lg text-white truncate group-hover:text-emerald-400 transition-colors">{user.name}</h3>
          <p className="text-sm text-slate-400 font-medium">Mat: <span className="text-slate-300">{user.registration}</span></p>
          <div className="flex items-center gap-2 mt-1">
            {isSynced === true ? (
              <span className="flex items-center gap-1 text-xs font-medium text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded-full">
                <CheckCircle className="w-3 h-3" /> Sincronizado
              </span>
            ) : isSynced === false ? (
              <button onClick={handleSync} disabled={isSyncing} className="flex items-center gap-1 text-xs font-medium text-amber-400 bg-amber-400/10 px-2 py-0.5 rounded-full hover:bg-amber-400/20 transition-colors">
                {isSyncing ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Upload className="w-3 h-3" />}
                {isSyncing ? 'Enviando...' : 'Pendente - Enviar'}
              </button>
            ) : (
              <span className="flex items-center gap-1 text-xs font-medium text-slate-500 bg-slate-500/10 px-2 py-0.5 rounded-full">
                <RefreshCw className="w-3 h-3 animate-spin" /> Verificando
              </span>
            )}
          </div>
        </div>
      </div>
      
      <div className="flex items-center gap-3 mt-5 pt-4 border-t border-white/5 opacity-80 group-hover:opacity-100 transition-opacity">
        <button onClick={() => onToggleStatus(user)} className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-xl text-sm font-medium transition-all ${user.active ? 'bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/10 hover:bg-rose-500/20 text-rose-400'}`}>
          {user.active ? <ToggleRight className="w-4 h-4" /> : <ToggleLeft className="w-4 h-4" />}
          {user.active ? 'Ativo' : 'Inativo'}
        </button>
        <button onClick={() => onEdit(user)} className="p-2 bg-white/5 hover:bg-emerald-500/20 rounded-xl text-slate-300 hover:text-emerald-400 transition-all shadow-sm">
          <Edit className="w-4 h-4" />
        </button>
        <button onClick={() => onDelete(user)} className="p-2 bg-white/5 hover:bg-rose-500/20 rounded-xl text-slate-300 hover:text-rose-400 transition-all shadow-sm">
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
