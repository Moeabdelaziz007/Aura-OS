/**
 * 🌐 useAetherSocket — WebSocket hook for AetherOS Edge Client
 *
 * Connects to the AetherOS UI Server and receives Micro-UI manifests.
 * Each manifest triggers a component render with animation.
 *
 * Protocol:
 *   RENDER_UI   → Add component to render queue
 *   UPDATE_UI   → Update existing component props
 *   DISSOLVE_UI → Remove component with dissolve animation
 *   CLEAR_ALL   → Remove all components
 */

import { useState, useEffect, useCallback, useRef } from "react";

export interface UIManifest {
    action: "RENDER_UI" | "UPDATE_UI" | "DISSOLVE_UI" | "CLEAR_ALL";
    component: string;
    props: Record<string, any>;
    animation: string;
    layout: string;
    id: string;
    timestamp: number;
    ttl_seconds: number;
    priority: number;
}

interface UseAetherSocketReturn {
    components: UIManifest[];
    connected: boolean;
    dissolve: (id: string) => void;
    clearAll: () => void;
}

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8765";
const RECONNECT_DELAY = 3000;
const HEARTBEAT_INTERVAL = 25000;

export function useAetherSocket(): UseAetherSocketReturn {
    const [components, setComponents] = useState<UIManifest[]>([]);
    const [connected, setConnected] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);
    const heartbeatRef = useRef<number | null>(null);
    const reconnectRef = useRef<number | null>(null);

    const connect = useCallback(() => {
        try {
            const ws = new WebSocket(WS_URL);
            wsRef.current = ws;

            ws.onopen = () => {
                setConnected(true);
                console.log("✅ Connected to AetherOS UI Server");

                // Start heartbeat
                heartbeatRef.current = window.setInterval(() => {
                    if (ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({ action: "HEARTBEAT" }));
                    }
                }, HEARTBEAT_INTERVAL);
            };

            ws.onmessage = (event) => {
                try {
                    const manifest: UIManifest = JSON.parse(event.data);
                    handleManifest(manifest);
                } catch (err) {
                    console.warn("⚠️ Invalid message from server:", err);
                }
            };

            ws.onclose = () => {
                setConnected(false);
                cleanup();
                console.log("📤 Disconnected. Reconnecting...");
                reconnectRef.current = window.setTimeout(connect, RECONNECT_DELAY);
            };

            ws.onerror = (err) => {
                console.error("❌ WebSocket error:", err);
            };
        } catch (err) {
            console.error("❌ Connection failed:", err);
            reconnectRef.current = window.setTimeout(connect, RECONNECT_DELAY);
        }
    }, []);

    const handleManifest = useCallback((manifest: UIManifest) => {
        switch (manifest.action) {
            case "RENDER_UI":
                setComponents((prev) => {
                    // Replace if same ID exists, otherwise append
                    const exists = prev.findIndex((c) => c.id === manifest.id);
                    if (exists >= 0) {
                        const next = [...prev];
                        next[exists] = manifest;
                        return next;
                    }
                    return [...prev, manifest].sort((a, b) => b.priority - a.priority);
                });
                break;

            case "UPDATE_UI":
                setComponents((prev) =>
                    prev.map((c) =>
                        c.id === manifest.id ? { ...c, props: { ...c.props, ...manifest.props } } : c
                    )
                );
                break;

            case "DISSOLVE_UI":
                setComponents((prev) => prev.filter((c) => c.id !== manifest.id));
                break;

            case "CLEAR_ALL":
                setComponents([]);
                break;
        }
    }, []);

    const dissolve = useCallback((id: string) => {
        setComponents((prev) => prev.filter((c) => c.id !== id));
        wsRef.current?.send(JSON.stringify({ action: "UI_EVENT", event: "dissolve", id }));
    }, []);

    const clearAll = useCallback(() => {
        setComponents([]);
    }, []);

    const cleanup = () => {
        if (heartbeatRef.current) clearInterval(heartbeatRef.current);
        if (reconnectRef.current) clearTimeout(reconnectRef.current);
    };

    useEffect(() => {
        connect();
        return () => {
            cleanup();
            wsRef.current?.close();
        };
    }, [connect]);

    return { components, connected, dissolve, clearAll };
}
