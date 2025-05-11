import { useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';

export function useWebSocket(type, symbol = null) {
  const { token } = useAuth();
  const ws = useRef(null);
  const reconnectTimeout = useRef(null);

  const connect = useCallback(() => {
    let url = `${process.env.REACT_APP_WS_URL || 'ws://localhost:8000'}/api/v1/ws/${type}`;
    if (symbol) {
      url += `/${symbol}`;
    }
    if (type === 'portfolio') {
      url += `?token=${token}`;
    }

    ws.current = new WebSocket(url);

    ws.current.onopen = () => {
      console.log(`WebSocket ${type} connected`);
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
        reconnectTimeout.current = null;
      }
    };

    ws.current.onclose = () => {
      console.log(`WebSocket ${type} disconnected`);
      // Attempt to reconnect after 5 seconds
      reconnectTimeout.current = setTimeout(connect, 5000);
    };

    ws.current.onerror = (error) => {
      console.error(`WebSocket ${type} error:`, error);
    };
  }, [type, symbol, token]);

  useEffect(() => {
    connect();

    return () => {
      if (ws.current) {
        ws.current.close();
      }
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
    };
  }, [connect]);

  const sendMessage = useCallback((message) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    }
  }, []);

  return {
    sendMessage,
    ws: ws.current
  };
} 