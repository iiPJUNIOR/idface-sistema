import React from 'react';
import { Camera, X } from 'lucide-react';

interface FormData {
  name: string;
  registration: string;
  cpf: string;
  photo: string;
}

interface UserModalProps {
  editingUser: boolean;
  formData: FormData;
  setFormData: React.Dispatch<React.SetStateAction<FormData>>;
  setShowCamera: (show: boolean) => void;
  closeModal: () => void;
  handleSubmit: (e: React.FormEvent) => void;
  loading: boolean;
}

export function UserModal({ editingUser, formData, setFormData, setShowCamera, closeModal, handleSubmit, loading }: UserModalProps) {
  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-xl flex items-center justify-center z-50 p-4 transition-all duration-300">
      <div className="bg-slate-900 rounded-3xl w-full max-w-md border border-white/10 shadow-2xl relative overflow-hidden animate-float-up">
        {/* Glow effect */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/20 rounded-full blur-[100px] pointer-events-none"></div>
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-indigo-500/20 rounded-full blur-[100px] pointer-events-none"></div>

        <div className="p-6 border-b border-white/5 flex items-center justify-between relative z-10">
          <h3 className="text-2xl font-heading font-bold text-white tracking-tight">
            {editingUser ? 'Editar Usuário' : 'Novo Usuário'}
          </h3>
          <button onClick={closeModal} className="p-2.5 bg-white/5 hover:bg-rose-500/20 hover:text-rose-400 rounded-xl transition-colors text-slate-400">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-8 space-y-6 relative z-10">
          <div className="flex justify-center mb-2">
            <div
              onClick={() => setShowCamera(true)}
              className="w-32 h-32 bg-slate-800/50 rounded-3xl border-2 border-dashed border-emerald-500/30 hover:border-emerald-500 cursor-pointer flex flex-col items-center justify-center transition-all duration-300 group shadow-inner relative overflow-hidden"
            >
              {formData.photo ? (
                <>
                  <img 
                    src={formData.photo.startsWith('http') ? formData.photo : `data:image/jpeg;base64,${formData.photo}`} 
                    alt="Preview" 
                    className="w-full h-full object-cover" 
                  />
                  <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center shadow-[inset_0_0_40px_rgba(0,0,0,0.8)]">
                    <Camera className="w-8 h-8 text-white" />
                    <span className="text-xs font-semibold text-white mt-2">Alterar</span>
                  </div>
                </>
              ) : (
                <>
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-2 group-hover:scale-110 transition-transform ${!editingUser && !formData.photo ? 'bg-rose-500/20' : 'bg-white/5'}`}>
                    <Camera className={`w-6 h-6 ${!editingUser && !formData.photo ? 'text-rose-400' : 'text-emerald-400'}`} />
                  </div>
                  <span className={`text-xs font-medium group-hover:text-emerald-300 ${!editingUser && !formData.photo ? 'text-rose-400' : 'text-slate-400'}`}>
                    Capturar Biometria *
                  </span>
                </>
              )}
            </div>
          </div>

          <div className="space-y-4">
            <div className="relative">
               <input type="text" required value={formData.name} onChange={(e) => setFormData((prev: FormData) => ({ ...prev, name: e.target.value }))} className="peer w-full px-5 pt-8 pb-3 bg-slate-950/50 border border-white/10 rounded-2xl text-white placeholder-transparent focus:outline-none focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/20 transition-all font-medium" placeholder="Nome" />
               <label className="absolute top-4 left-5 text-sm font-medium text-slate-400 peer-focus:text-emerald-400 peer-focus:-translate-y-2 peer-focus:scale-[0.85] peer-valid:-translate-y-2 peer-valid:scale-[0.85] transition-all origin-left pointer-events-none">Nome Completo *</label>
            </div>

            <div className="relative">
               <input type="text" required value={formData.registration} onChange={(e) => setFormData((prev: FormData) => ({ ...prev, registration: e.target.value }))} className="peer w-full px-5 pt-8 pb-3 bg-slate-950/50 border border-white/10 rounded-2xl text-white placeholder-transparent focus:outline-none focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/20 transition-all font-medium" placeholder="Matrícula" />
               <label className="absolute top-4 left-5 text-sm font-medium text-slate-400 peer-focus:text-emerald-400 peer-focus:-translate-y-2 peer-focus:scale-[0.85] peer-valid:-translate-y-2 peer-valid:scale-[0.85] transition-all origin-left pointer-events-none">Matrícula *</label>
            </div>

            <div className="relative">
               <input type="text" required value={formData.cpf} onChange={(e) => setFormData((prev: FormData) => ({ ...prev, cpf: e.target.value }))} className="peer w-full px-5 pt-8 pb-3 bg-slate-950/50 border border-white/10 rounded-2xl text-white placeholder-transparent focus:outline-none focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/20 transition-all font-medium" placeholder="CPF" />
               <label className="absolute top-4 left-5 text-sm font-medium text-slate-400 peer-focus:text-emerald-400 peer-focus:-translate-y-2 peer-focus:scale-[0.85] peer-valid:-translate-y-2 peer-valid:scale-[0.85] transition-all origin-left pointer-events-none">CPF *</label>
            </div>
          </div>

          <div className="flex gap-4 pt-4 mt-8 border-t border-white/5">
            <button type="button" onClick={closeModal} className="flex-1 px-5 py-3.5 bg-slate-800 hover:bg-slate-700 border border-white/5 rounded-2xl transition-all text-slate-300 font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-500">
              Cancelar
            </button>
            <button type="submit" disabled={loading} className="flex-1 px-5 py-3.5 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 shadow-lg shadow-emerald-500/20 rounded-2xl font-bold text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 tracking-wide text-lg">
              {loading ? 'Processando...' : editingUser ? 'Atualizar' : 'Cadastrar'}
            </button>
          </div>
        </form>
      </div>
      <style>{`
        @keyframes floatUp {
          from { opacity: 0; transform: translateY(20px) scale(0.95); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }
        .animate-float-up { animation: floatUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
      `}</style>
    </div>
  );
}
