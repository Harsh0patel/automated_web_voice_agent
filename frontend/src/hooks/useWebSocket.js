import { useEffect, useRef, useCallback } from 'react';

const WS_PORT = window.location.port || '8000';
const WS_URL = `ws://${location.hostname}:${WS_PORT}/ws`;

export default function useWebSocket({ onMessage, onStatusChange }) {
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const mountedRef = useRef(true);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      if (mountedRef.current) onStatusChange?.('connected', 'Connected');
    };

    ws.onclose = () => {
      if (mountedRef.current) {
        onStatusChange?.('disconnected', 'Disconnected');
        reconnectTimer.current = setTimeout(connect, 2000);
      }
    };

    ws.onerror = () => {
      if (mountedRef.current) onStatusChange?.('error', 'Connection error');
    };

    ws.onmessage = (event) => {
      if (event.data instanceof Blob) {
        onMessage?.({ type: '__audio__', blob: event.data });
        return;
      }
      try {
        const data = JSON.parse(event.data);
        onMessage?.(data);
      } catch {
        // ignore unparseable messages
      }
    };
  }, [onMessage, onStatusChange]);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data));
      return true;
    }
    return false;
  }, []);

  return { send, reconnect: connect };
}
