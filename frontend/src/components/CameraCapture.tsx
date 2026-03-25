import { useRef, useState, useEffect, useCallback } from 'react';
import { Camera, RefreshCw, X, Check } from 'lucide-react';

interface CameraCaptureProps {
  onCapture: (photoBase64: string) => void;
  onClose?: () => void;
}

export function CameraCapture({ onCapture, onClose }: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [capturedPhoto, setCapturedPhoto] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const startCamera = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);

      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user',
        },
      });

      setStream(mediaStream);

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (err) {
      console.error('Erro ao acessar câmera:', err);
      setError('Não foi possível acessar a câmera. Verifique as permissões.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    startCamera();

    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.drawImage(video, 0, 0);

    const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
    setCapturedPhoto(dataUrl);

    stream?.getTracks().forEach((track) => track.stop());
    setStream(null);
  };

  const retakePhoto = () => {
    setCapturedPhoto(null);
    startCamera();
  };

  const confirmPhoto = () => {
    if (capturedPhoto) {
      const base64Data = capturedPhoto.replace(/^data:image\/jpeg;base64,/, '');
      onCapture(base64Data);
    }
  };

  const handleClose = () => {
    stream?.getTracks().forEach((track) => track.stop());
    setStream(null);
    onClose?.();
  };

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
      <div className="bg-gray-900 rounded-2xl overflow-hidden max-w-lg w-full mx-4">
        <div className="p-4 border-b border-gray-800 flex items-center justify-between">
          <h3 className="text-white font-semibold flex items-center gap-2">
            <Camera className="w-5 h-5" />
            Capturar Foto
          </h3>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        <div className="relative aspect-[4/3] bg-gray-950">
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
            </div>
          )}

          {error && (
            <div className="absolute inset-0 flex items-center justify-center p-4">
              <div className="text-center">
                <p className="text-red-400 mb-2">{error}</p>
                <button
                  onClick={startCamera}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Tentar novamente
                </button>
              </div>
            </div>
          )}

          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className={`w-full h-full object-cover ${!stream || loading ? 'hidden' : ''}`}
          />

          {capturedPhoto && (
            <img
              src={capturedPhoto}
              alt="Foto capturada"
              className="w-full h-full object-cover"
            />
          )}

          <canvas ref={canvasRef} className="hidden" />
        </div>

        <div className="p-4 flex gap-3 justify-end">
          {capturedPhoto ? (
            <>
              <button
                onClick={retakePhoto}
                className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors flex items-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Tirar outra
              </button>
              <button
                onClick={confirmPhoto}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
              >
                <Check className="w-4 h-4" />
                Usar foto
              </button>
            </>
          ) : (
            <button
              onClick={capturePhoto}
              disabled={!stream || loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Camera className="w-4 h-4" />
              Capturar
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
