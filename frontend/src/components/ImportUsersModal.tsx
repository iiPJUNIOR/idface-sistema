import { useState, useRef } from 'react';
import { Upload, X, FileText, Check, AlertCircle, Loader2, Download } from 'lucide-react';
import { api } from '../services/api';

const SAMPLE_CSV = 'name\tregistration\tcpf\nJoão Silva\t12345\t12345678901\nMaria Santos\t12346\t\nPedro Oliveira\t12347\t12345678903';

interface ImportUsersModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportComplete: () => void;
}

interface ParsedUser {
  name: string;
  registration: string;
  cpf?: string;
}

interface Result {
  registration: string;
  name: string;
  success: boolean;
  error?: string;
}

export function ImportUsersModal({ isOpen, onClose, onImportComplete }: ImportUsersModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [parsedUsers, setParsedUsers] = useState<ParsedUser[]>([]);
  const [isParsing, setIsParsing] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [results, setResults] = useState<Result[]>([]);
  const [importStatus, setImportStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const downloadTemplate = () => {
    const header = ['name', 'registration', 'cpf'].join(';');
    const row1 = ['João Silva', '12345', '12345678901'].join(';');
    const row2 = ['Maria Santos', '12346', ''].join(';');
    const row3 = ['Pedro Oliveira', '12347', '12345678903'].join(';');
    const csvContent = [header, row1, row2, row3].join('\n');
    
    const BOM = '\uFEFF';
    const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'modelo_cadastros.csv';
    link.click();
    URL.revokeObjectURL(link.href);
  };

  if (!isOpen) return null;

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    if (!selectedFile.name.endsWith('.csv')) {
      alert('Por favor, selecione um arquivo CSV');
      return;
    }

    setFile(selectedFile);
    setIsParsing(true);
    setResults([]);
    setImportStatus('idle');

    try {
      const { users } = await api.importUsersCSV(selectedFile);
      setParsedUsers(users);
    } catch (error) {
      alert('Erro ao processar arquivo: ' + (error as Error).message);
      setFile(null);
    } finally {
      setIsParsing(false);
    }
  };

  const handleImport = async () => {
    if (parsedUsers.length === 0) return;

    setIsImporting(true);
    setResults([]);

    try {
      const response = await api.batchCreateUsers(parsedUsers);
      setResults(response.results);
      setImportStatus('success');
      onImportComplete();
    } catch (error) {
      alert('Erro ao importar usuários: ' + (error as Error).message);
      setImportStatus('error');
    } finally {
      setIsImporting(false);
    }
  };

  const handleClose = () => {
    setFile(null);
    setParsedUsers([]);
    setResults([]);
    setImportStatus('idle');
    onClose();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && fileInputRef.current) {
      const dt = new DataTransfer();
      dt.items.add(droppedFile);
      fileInputRef.current.files = dt.files;
      handleFileChange({ target: { files: dt.files } } as any);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const successCount = results.filter(r => r.success).length;
  const errorCount = results.filter(r => !r.success).length;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-slate-800 rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden border border-white/10">
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
          <h2 className="text-xl font-semibold text-white">Importar Cadastros</h2>
          <button onClick={handleClose} className="text-slate-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {!file && (
            <div className="space-y-4">
              <div className="border-2 border-dashed border-slate-600 rounded-lg p-8 text-center hover:border-blue-500 transition-colors cursor-pointer bg-slate-900/50"
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  className="hidden"
                  onChange={handleFileChange}
                />
                <Upload className="w-12 h-12 mx-auto text-slate-400 mb-4" />
                <p className="text-slate-300 mb-2">
                  Arraste um arquivo CSV ou clique para selecionar
                </p>
                <p className="text-sm text-slate-500">
                  Separador: ponto e vírgula (;)
                </p>
              <div className="mt-2 p-3 bg-slate-950 rounded text-xs font-mono text-slate-300">
                <div className="font-bold text-slate-200">name;registration;cpf</div>
                <div>João Silva;12345;12345678901</div>
                <div>Maria Santos;12346;</div>
              </div>
              </div>
              <button
                onClick={downloadTemplate}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 text-blue-400 hover:text-blue-300 transition-colors"
              >
                <Download className="w-4 h-4" />
                Baixar modelo de arquivo CSV
              </button>
            </div>
          )}

          {isParsing && (
            <div className="text-center py-8">
              <Loader2 className="w-8 h-8 mx-auto text-blue-500 animate-spin" />
              <p className="mt-2 text-slate-300">Processando arquivo...</p>
            </div>
          )}

          {file && parsedUsers.length > 0 && importStatus === 'idle' && (
            <div>
              <div className="flex items-center gap-2 mb-4 p-3 bg-slate-900 rounded-lg border border-slate-700">
                <FileText className="w-5 h-5 text-blue-400" />
                <span className="text-slate-200">{file.name}</span>
                <span className="text-slate-400">({parsedUsers.length} usuários)</span>
                <button
                  onClick={() => { setFile(null); setParsedUsers([]); }}
                  className="ml-auto text-slate-400 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="max-h-64 overflow-y-auto border border-slate-700 rounded-lg">
                <table className="w-full text-sm">
                  <thead className="bg-slate-900 sticky top-0">
                    <tr>
                      <th className="px-4 py-2 text-left text-slate-400">Nome</th>
                      <th className="px-4 py-2 text-left text-slate-400">Matrícula</th>
                      <th className="px-4 py-2 text-left text-slate-400">CPF</th>
                    </tr>
                  </thead>
                  <tbody>
                    {parsedUsers.map((user, idx) => (
                      <tr key={idx} className="border-t border-slate-700">
                        <td className="px-4 py-2 text-slate-200">{user.name}</td>
                        <td className="px-4 py-2 text-slate-300">{user.registration}</td>
                        <td className="px-4 py-2 text-slate-500">{user.cpf || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex justify-end gap-3 mt-4">
                <button
                  onClick={handleClose}
                  className="px-4 py-2 text-slate-400 hover:text-white"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleImport}
                  disabled={isImporting}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 flex items-center gap-2"
                >
                  {isImporting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Importando...
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4" />
                      Importar {parsedUsers.length} usuários
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {results.length > 0 && importStatus === 'success' && (
            <div>
              <div className="flex items-center gap-4 mb-4">
                <div className="flex items-center gap-2 text-green-400">
                  <Check className="w-5 h-5" />
                  <span className="font-medium text-white">Importação concluída!</span>
                </div>
                <span className="text-slate-400">
                  {successCount} sucesso, {errorCount} erros
                </span>
              </div>

              <div className="max-h-64 overflow-y-auto border border-slate-700 rounded-lg">
                <table className="w-full text-sm">
                  <thead className="bg-slate-900 sticky top-0">
                    <tr>
                      <th className="px-4 py-2 text-left text-slate-400">Status</th>
                      <th className="px-4 py-2 text-left text-slate-400">Nome</th>
                      <th className="px-4 py-2 text-left text-slate-400">Matrícula</th>
                      <th className="px-4 py-2 text-left text-slate-400">Mensagem</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.map((result, idx) => (
                      <tr key={idx} className="border-t border-slate-700">
                        <td className="px-4 py-2">
                          {result.success ? (
                            <Check className="w-4 h-4 text-green-500" />
                          ) : (
                            <AlertCircle className="w-4 h-4 text-red-500" />
                          )}
                        </td>
                        <td className="px-4 py-2 text-slate-200">{result.name}</td>
                        <td className="px-4 py-2 text-slate-300">{result.registration}</td>
                        <td className="px-4 py-2 text-slate-500">
                          {result.success ? 'Cadastrado com sucesso' : result.error}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex justify-end mt-4">
                <button
                  onClick={handleClose}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                >
                  Fechar
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
