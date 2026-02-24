/**
 * 🪙 CryptoCard — AetherOS Micro-UI Component
 *
 * Glassmorphism crypto price card with sparkline visualization.
 * Materializes when user says "show me bitcoin price"
 */

import React from "react";

interface Coin {
    id: string;
    name: string;
    price: string;
    change: string;
    sparkline?: number[];
}

interface CryptoCardProps {
    title: string;
    coins: Coin[];
}

export const CryptoCard: React.FC<CryptoCardProps> = ({ title, coins }) => {
    return (
        <div className="aether-card">
            <div className="aether-card-header">
                <span className="aether-card-icon">🪙</span>
                <h3>{title}</h3>
            </div>
            <div className="aether-card-body">
                {coins.map((coin) => {
                    const isUp = coin.change?.includes("+") || coin.change?.includes("▲");
                    return (
                        <div key={coin.id} className="crypto-row">
                            <div className="crypto-name">{coin.name}</div>
                            <div className="crypto-price">{coin.price}</div>
                            <div className={`crypto-change ${isUp ? "up" : "down"}`}>
                                {coin.change}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};
