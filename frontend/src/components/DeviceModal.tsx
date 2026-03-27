import { useState, useEffect } from 'react';
import { X, Loader2, Wifi, WifiOff } from 'lucide-react';

interface Device {
  id?: number;
  name: string;
  ip: string;
  port: number;
  user: string;
  password: string;
  active?: boolean;
}

interface DeviceModalProps {
  device: Device | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (device: Device) => Promise<void>;
  onTestConnection: (ip: string, port: number, user: string, password: string) => Promise<{ success: boolean; message: string }>;
}

export function DeviceModal({ device, isOpen, onClose, onSave, onTestConnection }: DeviceModalProps) {
  const [formData, setFormData] = useState<Device>({
    name: '',
    ip: '',
    port: 8080,
    user: 'admin',
    password: '',
    active: true,
  });
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  useEffect(() => {
    if (device) {
      setFormData({
        name: device.name || '',
        ip: device.ip || '',
        port: device.port || 8080,
        user: device.user || 'admin',
        password: device.password || '',
        active: device.active ?? true,
      });
    } else {
      setFormData({
        name: '',
        ip: '',
        port: 8080,
        user: 'admin',
        password: '',
        active: true,
      });
    }
    setTestResult(null);
  }, [device, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onSave(formData);
      onClose();
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async () => {
    if (!formData.ip || !formData.port || !formData.user || !formData.password) {
      setTestResult({ success: false, message: 'Preencha todos os campos' });
      return;
    }
    setTesting(true);
    setTestResult(null);
    try {
      const result = await onTestConnection(formData.ip, formData.port, formData.user, formData.password);
      setTestResult(result);
    } catch (error) {
      setTestResult({ success: false, message: 'Erro ao testar conexão' });
    } finally {
      setTesting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose}></div>
      <div className="relative bg-slate-900 border border-white/10 rounded-3xl p-6 w-full max-w-md shadow-2xl animate-slideUp">
        <button onClick={onClose} className="absolute top-4 right-4 text-slate-400 hover:text-white p-2">
          <X className="w-5 h-5" />
        </button>

        <h3 className="text-xl font-bold text-white mb-4">
          {device ? 'Editar Dispositivo' : 'Novo Dispositivo'}
        </h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Nome</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="Ex: IDFace Principal"
              className="w-full px-4 py-3 bg-slate-800 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
              required
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-slate-400 mb-1">IP</label>
              <input
                type="text"
                value={formData.ip}
                onChange={(e) => setFormData({ ...formData, ip: e.target.value })}
                placeholder="192.168.1.100"
                className="w-full px-4 py-3 bg-slate-800 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">Porta</label>
              <input
                type="number"
                value={formData.port}
                onChange={(e) => setFormData({ ...formData, port: parseInt(e.target.value) || 8080 })}
                className="w-full px-4 py-3 bg-slate-800 border border-white/10 rounded-xl text-white focus:outline-none focus:border-emerald-500"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Usuário</label>
            <input
              type="text"
              value={formData.user}
              onChange={(e) => setFormData({ ...formData, user: e.target.value })}
              placeholder="admin"
              className="w-full px-4 py-3 bg-slate-800 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Senha</label>
            <input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              placeholder={device ? '••••••••' : ''}
              className="w-full px-4 py-3 bg-slate-800 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
              required={!device}
            />
            {device && <p className="text-xs text-slate-500 mt-1">Deixe em branco para manter a senha atual</p>}
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="active"
              checked={formData.active}
              onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
              className="w-4 h-4 rounded bg-slate-800 border-white/20 text-emerald-500 focus:ring-emerald-500/20"
            />
            <label htmlFor="active" className="text-sm text-slate-300">Ativo</label>
          </div>

          {testResult && (
            <div className={`flex items-center gap-2 p-3 rounded-xl ${testResult.success ? 'bg-emerald-500/10 border border-emerald-500/30' : 'bg-rose-500/10 border border-rose-500/30'}`}>
              {testResult.success ? <Wifi className="w-4 h-4 text-emerald-400" /> : <WifiOff className="w-4 h-4 text-rose-400" />}
              <span className={`text-sm ${testResult.success ? 'text-emerald-400' : 'text-rose-400'}`}>
                {testResult.message}
              </span>
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={handleTestConnection}
              disabled={testing}
              className="flex-1 py-3 px-4 bg-slate-700 hover:bg-slate-600 rounded-xl text-slate-300 font-medium transition-colors flex items-center justify-center gap-2"
            >
              {testing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wifi className="w-4 h-4" />}
              Testar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 py-3 px-4 bg-emerald-500 hover:bg-emerald-600 disabled:bg-slate-700 rounded-xl text-white font-medium transition-colors flex items-center justify-center gap-2"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              {device ? 'Salvar' : 'Adicionar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
