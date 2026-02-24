/**
 * 🌌 AetherOS — Edge Client App
 *
 * Main application entry point.
 * Connects to the AetherOS UI Server via WebSocket
 * and renders Micro-UI components as they materialize from voice commands.
 *
 * "من العدم، الأثير يُبدع" — From nothing, Aether creates.
 */

import React from "react";
import { AnimatePresence } from "framer-motion";
import { useAetherSocket } from "./hooks/useAetherSocket";
import { resolveComponent } from "./components/registry";
import { Materialize } from "./components/Materialize";
import "./index.css";

const App: React.FC = () => {
    const { components, connected, dissolve, clearAll } = useAetherSocket();

    return (
        <div className="aether-root">
            {/* Status Bar */}
            <header className="aether-status-bar">
                <div className="aether-logo">
                    <span className="logo-glyph">⬡</span>
                    <span className="logo-text">AetherOS</span>
                </div>
                <div className="aether-status">
                    <span className={`status-dot ${connected ? "connected" : "disconnected"}`} />
                    <span className="status-label">
                        {connected ? "Whisper Flow Active" : "Connecting..."}
                    </span>
                </div>
                {components.length > 0 && (
                    <button className="clear-btn" onClick={clearAll}>
                        Clear All
                    </button>
                )}
            </header>

            {/* Micro-UI Render Area */}
            <main className="aether-canvas">
                <AnimatePresence mode="popLayout">
                    {components.length === 0 && (
                        <Materialize id="empty-state" animation="fade" layout="card">
                            <div className="empty-state">
                                <div className="empty-glyph">⬡</div>
                                <h2>من العدم، الأثير يُبدع</h2>
                                <p>Speak to materialize. Your voice creates the interface.</p>
                            </div>
                        </Materialize>
                    )}

                    {components.map((manifest) => {
                        const Component = resolveComponent(manifest.component);
                        return (
                            <Materialize
                                key={manifest.id}
                                id={manifest.id}
                                animation={manifest.animation}
                                layout={manifest.layout}
                            >
                                <div className="manifest-wrapper" onClick={() => dissolve(manifest.id)}>
                                    <Component {...manifest.props} />
                                </div>
                            </Materialize>
                        );
                    })}
                </AnimatePresence>
            </main>

            {/* Footer */}
            <footer className="aether-footer">
                <span>AetherOS v2.0 — Power from Nothing</span>
                <span className="component-count">{components.length} active</span>
            </footer>
        </div>
    );
};

export default App;
