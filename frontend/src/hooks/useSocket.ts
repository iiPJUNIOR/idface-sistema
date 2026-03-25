import { useEffect, useCallback, useRef } from 'react';
import { io, Socket } from 'socket.io-client';

const WS_URL = import.meta.env.VITE_WS_URL || 'http://localhost:5000';

type EventCallback = (data: unknown) => void;

interface UseSocketOptions {
  onPresenceDetected?: EventCallback;
  onRecognitionDetected?: EventCallback;
  onUserCreated?: EventCallback;
  onUserUpdated?: EventCallback;
  onUserDeleted?: EventCallback;
  onDeviceHeartbeat?: EventCallback;
}

export function useSocket(options: UseSocketOptions = {}) {
  const socketRef = useRef<Socket | null>(null);

  const connect = useCallback(() => {
    if (socketRef.current?.connected) return;

    socketRef.current = io(WS_URL, {
      transports: ['websocket', 'polling'],
      autoConnect: true,
    });

    socketRef.current.on('connect', () => {
      console.log('WebSocket conectado');
      socketRef.current?.emit('subscribe', { room: 'admin' });
    });

    socketRef.current.on('presence_detected', (data) => {
      options.onPresenceDetected?.(data);
    });

    socketRef.current.on('recognition_detected', (data) => {
      options.onRecognitionDetected?.(data);
    });

    socketRef.current.on('user_created', (data) => {
      const newUser = data as { id: number };
      if (newUser && newUser.id) {
        options.onUserCreated?.(data);
      }
    });

    socketRef.current.on('user_updated', (data) => {
      options.onUserUpdated?.(data);
    });

    socketRef.current.on('user_deleted', (data) => {
      options.onUserDeleted?.(data);
    });

    socketRef.current.on('device_heartbeat', (data) => {
      options.onDeviceHeartbeat?.(data);
    });

    socketRef.current.on('disconnect', () => {
      console.log('WebSocket desconectado');
    });
  }, [options]);

  const disconnect = useCallback(() => {
    socketRef.current?.disconnect();
    socketRef.current = null;
  }, []);

  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    socket: socketRef.current,
    connect,
    disconnect,
    isConnected: socketRef.current?.connected ?? false,
  };
}
