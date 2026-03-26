import { useState, useEffect, useCallback } from 'react';
import { Users, UserCheck, DoorOpen, Plus, Search, Clock, CheckCircle, AlertCircle, RefreshCw, Fingerprint, Upload, Download } from 'lucide-react';
import { api } from '../services/api';
import type { User as UserType, Presence } from '../services/api';
import { useSocket } from '../hooks/useSocket';
import { CameraCapture } from '../components/CameraCapture';
import { StatCard } from '../components/StatCard';
import { UserRow } from '../components/UserRow';
import { UserModal } from '../components/UserModal';
import { PresenceList } from '../components/PresenceList';
import { ImportUsersModal } from '../components/ImportUsersModal';

export function Dashboard() {
  const [activeTab, setActiveTab] = useState<'users' | 'presence' | 'logs'>('users');
  const [users, setUsers] = useState<UserType[]>([]);
  const [presence, setPresence] = useState<Presence[]>([]);
  const [recognitions, setRecognitions] = useState<any[]>([]);
  const [stats, setStats] = useState({ total_users: 0, present_today: 0, absent_today: 0, total_entries_today: 0 });
  const [idfaceStatus, setIdfaceStatus] = useState({ connected: false, message: '' });
  const [showModal, setShowModal] = useState(false);
  const [showCamera, setShowCamera] = useState(false);
  const [editingUser, setEditingUser] = useState<UserType | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState({ name: '', registration: '', cpf: '', photo: '' });
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [showList, setShowList] = useState<'all' | 'present' | 'absent' | null>(null);
  const [showImportModal, setShowImportModal] = useState(false);

  const handlePresenceDetected = useCallback((data: unknown) => {
    const presenceData = data as Presence;
    setPresence((prev) => [presenceData, ...prev.slice(0, 49)]);
    setStats((prev) => ({ ...prev, present_today: prev.present_today + 1, total_entries_today: prev.total_entries_today + 1 }));
    showNotification('success', `${presenceData.name} registrado!`);
  }, []);

  const handleRecognitionDetected = useCallback((data: unknown) => {
    const rec = data as any;
    setRecognitions((prev) => [rec, ...prev.slice(0, 99)]);
  }, []);

  const { isConnected } = useSocket({
    onPresenceDetected: handlePresenceDetected,
    onRecognitionDetected: handleRecognitionDetected,
    onUserDeleted: (data) => { setUsers((prev) => prev.filter((u) => u.id !== (data as { user_id: number }).user_id)); setStats((prev) => ({ ...prev, total_users: Math.max(0, prev.total_users - 1) })); },
    onUserCreated: () => { loadData(); },
    onUserUpdated: () => { loadData(); },
  });

  const presentUserIds = new Set(presence.map(p => p.user_id));
  const allUsersList = users;
  const presentUsersList = users.filter(u => presentUserIds.has(u.id));

  const currentList = showList === 'all' ? allUsersList : showList === 'present' ? presentUsersList : [];

  const loadData = useCallback(async () => {
    try {
      const [u, p, s] = await Promise.all([api.getUsers(), api.getPresenceToday(), api.getPresenceStats()]);
      setUsers(u); setPresence(p.presence); setStats(s);
    } catch { console.error('Error loading data'); }
  }, []);

  const loadIdfaceStatus = useCallback(async () => {
    try { setIdfaceStatus(await api.testIdFace()); } catch { setIdfaceStatus({ connected: false, message: 'Erro' }); }
  }, []);

  useEffect(() => { loadData(); loadIdfaceStatus(); const iv = setInterval(loadIdfaceStatus, 30000); return () => clearInterval(iv); }, [loadData, loadIdfaceStatus]);

  const showNotification = (type: 'success' | 'error', message: string) => { setNotification({ type, message }); setTimeout(() => setNotification(null), 4000); };

  const openModal = (user?: UserType) => {
    if (user) { 
      setEditingUser(user); 
      // Se tem foto, usa a URL da API para exibir (não base64)
      const photoUrl = user.has_photo ? api.getUserPhotoUrl(user.id) : '';
      setFormData({ 
        name: user.name, 
        registration: user.registration, 
        cpf: user.cpf || '', 
        photo: photoUrl
      }); 
    }
    else { setEditingUser(null); setFormData({ name: '', registration: '', cpf: '', photo: '' }); }
    setShowModal(true);
  };

  const closeModal = () => { setShowModal(false); setEditingUser(null); setFormData({ name: '', registration: '', cpf: '', photo: '' }); };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); 
    if (!editingUser && !formData.photo) {
      showNotification('error', 'Por favor, capture a foto biométrica!');
      return;
    }
    setLoading(true);
    try {
      if (editingUser) {
        // Só enviar foto se for uma URL nova (não a foto existente)
        const sendPhoto = formData.photo && !formData.photo.startsWith('http');
        await api.updateUser(editingUser.id, { ...formData, photo: sendPhoto ? formData.photo : '' });
        setUsers(prev => prev.map(u => u.id === editingUser.id ? { 
          ...u, 
          name: formData.name, 
          registration: formData.registration,
          cpf: formData.cpf,
          has_photo: sendPhoto ? true : u.has_photo 
        } : u));
        showNotification('success', 'Usuário atualizado!');
      } else {
        const nu = await api.createUser(formData);
        setUsers(prev => [...prev, nu]); showNotification('success', 'Usuário cadastrado!');
      }
      closeModal();
    } catch (err: unknown) { showNotification('error', err instanceof Error ? err.message : 'Erro'); } finally { setLoading(false); }
  };

  const handleDelete = async (user: UserType) => {
    if (!confirm(`Excluir ${user.name}?`)) return;
    try { await api.deleteUser(user.id); setUsers(prev => prev.filter(u => u.id !== user.id)); showNotification('success', 'Excluído!'); }
    catch { showNotification('error', 'Erro'); }
  };

  const handleToggleStatus = async (user: UserType) => {
    try { const ns = await api.toggleUserStatus(user.id); setUsers(prev => prev.map(u => u.id === user.id ? { ...u, active: ns } : u)); showNotification('success', ns ? 'Ativado!' : 'Inativado!'); }
    catch { showNotification('error', 'Erro'); }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 selection:bg-emerald-500/30 font-sans flex flex-col items-center">
      {/* Dynamic Background Noise & Gradients */}
      <div className="fixed inset-0 z-0 pointer-events-none opacity-20 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-900/40 via-slate-950 to-emerald-900/10 mix-blend-screen"></div>

      {/* Header */}
      <header className="sticky top-0 z-40 w-full glass-panel border-b border-white/5 shadow-2xl shadow-black/50">
        <div className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-5 group cursor-pointer">
            <div className="relative">
              <div className="absolute inset-0 bg-emerald-500 rounded-2xl blur-xl opacity-30 group-hover:opacity-60 transition-opacity animate-pulse-glow"></div>
              <div className="w-14 h-14 bg-gradient-to-br from-emerald-400 to-indigo-500 rounded-2xl flex items-center justify-center relative shadow-inner shadow-white/20 border border-white/20 group-hover:scale-105 transition-transform duration-300">
                <Fingerprint className="w-8 h-8 text-white drop-shadow-md" />
              </div>
            </div>
            <div>
              <h1 className="text-3xl font-heading font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-emerald-300 to-indigo-300 tracking-tight">iDFace</h1>
              <p className="text-sm font-semibold text-emerald-500/80 uppercase tracking-widest mt-0.5">Control Center</p>
            </div>
          </div>
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3 px-5 py-2.5 glass-card rounded-full border-white/5 shadow-inner">
              <span className="relative flex h-3 w-3">
                {idfaceStatus.connected || isConnected ? (
                  <><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span><span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500 shadow-[0_0_10px_2px_rgba(16,185,129,0.5)]"></span></>
                ) : (
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-rose-500 shadow-[0_0_10px_2px_rgba(244,63,94,0.5)]"></span>
                )}
              </span>
              <span className="text-sm font-semibold tracking-wide uppercase text-slate-300">
                Data Hub {idfaceStatus.connected || isConnected ? <span className="text-emerald-400 ml-1">Online</span> : <span className="text-rose-400 ml-1">Offline</span>}
              </span>
            </div>
            <button onClick={() => api.openDoor(0)} className="group relative flex items-center gap-3 px-6 py-3.5 bg-gradient-to-r from-emerald-500 to-teal-600 rounded-2xl font-bold transition-all shadow-lg hover:shadow-emerald-500/30 overflow-hidden isolate">
              <span className="absolute inset-0 bg-gradient-to-r from-teal-400 to-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity -z-10"></span>
              <DoorOpen className="w-5 h-5 text-emerald-50 group-hover:scale-110 transition-transform" />
              <span className="text-white drop-shadow-sm tracking-wide">Desbloquear</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="w-full max-w-7xl px-6 py-10 relative z-10 space-y-8 flex-1">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 relative">
          <button onClick={() => setShowList(showList === 'all' ? null : 'all')} className="text-left">
            <StatCard icon={Users} label="Total de Usuários" value={stats.total_users} colorClass="from-indigo-500 to-purple-600" bgClass="from-indigo-600 to-purple-700" />
          </button>
          <button onClick={() => setShowList(showList === 'present' ? null : 'present')} className="text-left">
            <StatCard icon={UserCheck} label="Presentes Hoje" value={stats.present_today} colorClass="from-emerald-400 to-teal-500" bgClass="from-emerald-500 to-teal-600" />
          </button>
          <StatCard icon={Clock} label="Entradas Hoje" value={stats.total_entries_today} colorClass="from-rose-400 to-pink-500" bgClass="from-rose-500 to-pink-600" />
        </div>

        {/* Lista de usuários */}
        {showList && (
          <div className="glass-panel rounded-[2rem] border border-white/5 overflow-hidden shadow-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-white">
                {showList === 'all' ? 'Todos os Usuários' : showList === 'present' ? 'Usuários Presentes' : 'Usuários Faltantes'}
              </h3>
              <button onClick={() => setShowList(null)} className="text-slate-400 hover:text-white">✕</button>
            </div>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {currentList.length === 0 ? (
                <p className="text-slate-500 text-center py-8">Nenhum usuário nesta categoria</p>
              ) : (
                currentList.map(user => (
                  <div key={user.id} className="flex items-center gap-4 p-3 bg-slate-800/50 rounded-xl">
                    <img src={api.getUserPhotoUrl(user.id)} alt={user.name} className="w-10 h-10 rounded-full object-cover bg-slate-700" />
                    <div className="flex-1">
                      <p className="font-semibold text-white">{user.name}</p>
                      <p className="text-sm text-slate-400">Matrícula: {user.registration}</p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${user.active ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
                      {user.active ? 'ATIVO' : 'INATIVO'}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Tab Layout */}
        <div className="glass-panel rounded-[2rem] border border-white/5 overflow-hidden shadow-2xl flex flex-col min-h-[600px] relative">
          {/* Tab Headers */}
          <div className="flex border-b border-white/5 bg-slate-900/60 backdrop-blur-3xl sticky top-0 z-20">
            {[
              { id: 'users', icon: Users, label: 'Central de Usuários' },
              { id: 'logs', icon: Fingerprint, label: 'Reconhecimentos em Tempo Real' },
              { id: 'presence', icon: Clock, label: 'Feed de Acessos Real-Time' }
            ].map((tab) => (
              <button key={tab.id} onClick={() => setActiveTab(tab.id as 'users' | 'presence')} className={`flex-1 py-6 font-heading font-semibold text-lg transition-all flex items-center justify-center gap-3 relative focus:outline-none focus:ring-2 focus:ring-emerald-500/50 inset-0 ${activeTab === tab.id ? 'text-white' : 'text-slate-500 hover:bg-white/5 hover:text-slate-300'}`}>
                <tab.icon className={`w-6 h-6 ${activeTab === tab.id ? 'text-emerald-400' : 'opacity-70'}`} />
                {tab.label}
                {activeTab === tab.id && <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-400 to-teal-400 rounded-t-full shadow-[0_-2px_10px_rgba(52,211,153,0.5)]"></div>}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div className="p-8 flex-1 bg-slate-950/40 relative">
            {activeTab === 'users' ? (
              <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 fill-mode-forwards">
                {/* Search & Actions */}
                <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
                  <div className="relative flex-1 max-w-xl group">
                    <div className="absolute inset-y-0 left-5 flex items-center pointer-events-none">
                      <Search className="w-6 h-6 text-slate-500 group-focus-within:text-emerald-400 transition-colors" />
                    </div>
                    <input type="text" placeholder="Nome, Matrícula..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="w-full pl-14 pr-6 py-4 bg-slate-900/80 border border-white/10 rounded-2xl text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/20 transition-all font-medium text-lg shadow-inner" />
                  </div>
                  <div className="flex items-center gap-4">
                    <button onClick={() => { setLoading(true); api.syncAllUsers().then(() => { showNotification('success', 'Sync concluído'); setTimeout(() => loadData(), 500); }).catch(() => showNotification('error', 'Erro')).finally(() => setLoading(false)); }} disabled={loading} className="p-4 glass-card hover:bg-slate-800 rounded-2xl transition-all shadow-lg hover:shadow-emerald-500/20 group" title="Sincronizar com IDFace">
                      <RefreshCw className={`w-6 h-6 text-slate-300 group-hover:text-emerald-400 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                    <button onClick={() => { setLoading(true); api.syncFromIdFace().then((result) => { showNotification('success', `${result.synced} usuários importados do IDFace`); setTimeout(() => loadData(), 500); }).catch(() => showNotification('error', 'Erro')).finally(() => setLoading(false)); }} disabled={loading} className="flex items-center gap-3 px-6 py-4 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-2xl font-bold transition-all shadow-lg hover:shadow-cyan-500/40 hover:-translate-y-0.5 text-white tracking-wide">
                      <Download className="w-6 h-6" /> Importar IDFace
                    </button>
                    <button onClick={() => { setLoading(true); api.syncAllPendingUsers().then((result) => { showNotification('success', `${result.success_count} enviados, ${result.error_count} erros`); setTimeout(() => loadData(), 500); }).catch(() => showNotification('error', 'Erro')).finally(() => setLoading(false)); }} disabled={loading} className="flex items-center gap-3 px-6 py-4 bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl font-bold transition-all shadow-lg hover:shadow-amber-500/40 hover:-translate-y-0.5 text-white tracking-wide">
                      <Upload className="w-6 h-6" /> Forçar Pendentes
                    </button>
                    <button onClick={() => setShowImportModal(true)} className="flex items-center gap-3 px-6 py-4 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl font-bold transition-all shadow-lg hover:shadow-indigo-500/40 hover:-translate-y-0.5 text-white tracking-wide">
                      <Upload className="w-6 h-6" /> Importar CSV
                    </button>
                    <button onClick={() => openModal()} className="flex items-center gap-3 px-8 py-4 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-2xl font-bold transition-all shadow-lg hover:shadow-emerald-500/40 hover:-translate-y-0.5 text-white tracking-wide">
                      <Plus className="w-6 h-6" /> Novo Ativo
                    </button>
                  </div>
                </div>

                {/* Grid */}
                {users.filter(u => u.name.toLowerCase().includes(searchTerm.toLowerCase()) || u.registration.includes(searchTerm)).length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {users.filter(u => u.name.toLowerCase().includes(searchTerm.toLowerCase()) || u.registration.includes(searchTerm)).map(user => {
                      const photoUrl = user.photo_url ? `http://localhost:5000${user.photo_url}?t=${Date.now()}` : '';
                      return (
                        <UserRow key={user.id} user={user} photoUrl={photoUrl} onToggleStatus={handleToggleStatus} onEdit={openModal} onDelete={handleDelete} onUserUpdated={loadData} />
                      );
                    })}
                  </div>
                ) : (
                   <div className="flex flex-col items-center justify-center py-20 text-center">
                      <div className="w-32 h-32 bg-slate-800/50 rounded-full flex items-center justify-center mb-6 shadow-inner animate-pulse">
                        <Users className="w-16 h-16 text-slate-600 relative z-10" />
                      </div>
                      <p className="text-3xl font-heading font-bold text-slate-300 mb-3 tracking-tight">Nenhuma entidade localizada</p>
                      <p className="text-lg text-slate-500 max-w-sm mb-8">Refine a busca ou cadastre um novo acesso no sistema.</p>
                      {searchTerm === '' && (
                        <button onClick={() => openModal()} className="px-8 py-4 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 rounded-2xl font-bold transition-colors">
                          <Plus className="w-5 h-5 inline mr-2" /> Iniciar Cadastro
                        </button>
                      )}
                   </div>
                )}
              </div>
            ) : activeTab === 'logs' ? (
              <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="space-y-3">
                  {recognitions.length === 0 ? (
                    <div className="text-center py-16">
                      <div className="w-20 h-20 bg-slate-800/50 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Fingerprint className="w-10 h-10 text-slate-600" />
                      </div>
                      <p className="text-slate-500 text-lg">Aguardando reconhecimentos...</p>
                      <p className="text-slate-600 text-sm mt-2">Os reconhecimentos aparecerão aqui em tempo real</p>
                    </div>
                  ) : (
                    recognitions.map((rec, idx) => {
                      const statusText = rec.active ? 'AUTORIZADO' : rec.not_found ? 'NÃO CADASTRADO' : rec.not_recognized ? 'NÃO RECONHECIDO' : rec.blocked ? 'BLOQUEADO' : rec.event_description || `EVENTO ${rec.event_type}`;
                      const statusColor = rec.active ? 'text-emerald-400' : rec.not_found ? 'text-rose-400' : rec.not_recognized ? 'text-slate-400' : rec.blocked ? 'text-amber-400' : 'text-blue-400';
                      const borderColor = rec.active ? 'border-emerald-500/30' : rec.not_found ? 'border-rose-500/30' : rec.not_recognized ? 'border-slate-500/30' : rec.blocked ? 'border-amber-500/30' : 'border-blue-500/30';
                      const bgColor = rec.active ? 'bg-emerald-500/10' : rec.not_found ? 'bg-rose-500/10' : rec.not_recognized ? 'bg-slate-500/10' : rec.blocked ? 'bg-amber-500/10' : 'bg-blue-500/10';
                      const iconBg = rec.active ? 'bg-emerald-500/20' : rec.not_found ? 'bg-rose-500/20' : rec.not_recognized ? 'bg-slate-500/20' : rec.blocked ? 'bg-amber-500/20' : 'bg-blue-500/20';
                      const iconColor = rec.active ? 'text-emerald-400' : rec.not_found ? 'text-rose-400' : rec.not_recognized ? 'text-slate-400' : rec.blocked ? 'text-amber-400' : 'text-blue-400';
                      const Icon = rec.active ? CheckCircle : AlertCircle;
                      
                      return (
                        <div key={idx} className={`flex items-center gap-4 p-4 rounded-2xl border ${bgColor} ${borderColor}`}>
                          <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${iconBg}`}>
                            <Icon className={`w-6 h-6 ${iconColor}`} />
                          </div>
                          <div className="flex-1">
                            <p className="font-semibold text-white">{rec.name}</p>
                            <p className="text-sm text-slate-400">Matrícula: {rec.registration || 'N/A'} {rec.user_id ? `(ID: ${rec.user_id})` : ''}</p>
                          </div>
                          <div className="text-right">
                            <p className={`font-bold ${statusColor}`}>{statusText}</p>
                            <p className="text-xs text-slate-500">{new Date(rec.created_at).toLocaleTimeString('pt-BR')}</p>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            ) : (
               <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 max-w-4xl mx-auto">
                 <PresenceList presence={presence} />
               </div>
            )}
          </div>
        </div>
      </main>

      {/* Modals & Notifications */}
      {showModal && <UserModal editingUser={!!editingUser} formData={formData} setFormData={setFormData} setShowCamera={setShowCamera} closeModal={closeModal} handleSubmit={handleSubmit} loading={loading} />}
      {showCamera && <CameraCapture onCapture={(photo) => { setFormData(p => ({ ...p, photo })); setShowCamera(false); }} onClose={() => setShowCamera(false)} />}
      {showImportModal && <ImportUsersModal isOpen={showImportModal} onClose={() => setShowImportModal(false)} onImportComplete={loadData} />}
      
      {notification && (
        <div className={`fixed bottom-8 right-8 px-6 py-4 rounded-2xl flex items-center gap-4 shadow-[0_20px_40px_-15px_rgba(0,0,0,0.8)] z-[100] animate-slideUp border border-white/10 ${notification.type === 'success' ? 'bg-gradient-to-r from-emerald-600 to-teal-700' : 'bg-gradient-to-r from-rose-600 to-pink-700'}`}>
          <div className="bg-white/20 p-2 rounded-xl backdrop-blur-sm">
             {notification.type === 'success' ? <CheckCircle className="w-6 h-6 text-white" /> : <AlertCircle className="w-6 h-6 text-white" />}
          </div>
          <span className="font-heading font-semibold text-lg text-white tracking-wide">{notification.message}</span>
        </div>
      )}

      <style>{`
        @keyframes slideUp { from { opacity: 0; transform: translateY(2rem) scale(0.9); } to { opacity: 1; transform: translateY(0) scale(1); } }
        .animate-slideUp { animation: slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
      `}</style>
    </div>
  );
}
