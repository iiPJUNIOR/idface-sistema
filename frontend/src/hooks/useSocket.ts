import { useEffect, useCallback, useRef, useState } from 'react';
import { io, Socket } from 'socket.io-client';

const WS_URL = import.meta.env.VITE_WS_URL || 'https://iiiPJUNIOR.pythonanywhere.com';

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
  const [isConnected, setIsConnected] = useState(false);
  
  const optionsRef = useRef(options);
  optionsRef.current = options;

  const connect = useCallback(() => {
    if (socketRef.current?.connected) return;

    socketRef.current = io(WS_URL, {
      transports: ['websocket', 'polling'],
      autoConnect: true,
    });

    socketRef.current.on('connect', () => {
      console.log('WebSocket conectado');
      setIsConnected(true);
      socketRef.current?.emit('subscribe', { room: 'admin' });
    });

    socketRef.current.on('presence_detected', (data) => {
      optionsRef.current.onPresenceDetected?.(data);
    });

    socketRef.current.on('recognition_detected', (data) => {
      optionsRef.current.onRecognitionDetected?.(data);
    });

    socketRef.current.on('user_created', (data) => {
      const newUser = data as { id: number };
      if (newUser && newUser.id) {
        console.log('user_created received via socket');
        optionsRef.current.onUserCreated?.(data);
      }
    });

    socketRef.current.on('user_updated', (data) => {
      console.log('user_updated received via socket');
      optionsRef.current.onUserUpdated?.(data);
    });

    socketRef.current.on('users_synced', (data) => {
      console.log('users_synced received via socket');
      optionsRef.current.onUserUpdated?.(data);
    });

    socketRef.current.on('user_deleted', (data) => {
      optionsRef.current.onUserDeleted?.(data);
    });

    socketRef.current.on('device_heartbeat', (data) => {
      optionsRef.current.onDeviceHeartbeat?.(data);
    });

    socketRef.current.on('disconnect', () => {
      console.log('WebSocket desconectado');
      setIsConnected(false);
    });
  }, []);

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
    isConnected,
  };
}
