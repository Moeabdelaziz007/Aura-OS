/**
 * 🌤️ WeatherCard — AetherOS Micro-UI Component
 *
 * Weather information with glassmorphism card.
 * Materializes when user says "how's the weather" or "is it hot outside"
 */

import React from "react";

interface WeatherCardProps {
    title: string;
    city: string;
    temp_c: number;
    condition: number;
    wind_kmh: number;
    humidity: number;
}

const WEATHER_ICONS: Record<number, string> = {
    0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️",
    45: "🌫️", 48: "🌫️",
    51: "🌦️", 53: "🌦️", 55: "🌧️",
    61: "🌧️", 63: "🌧️", 65: "🌧️",
    71: "🌨️", 73: "🌨️", 75: "❄️",
    80: "🌦️", 81: "🌧️", 82: "⛈️",
    95: "⛈️", 99: "⛈️",
};

function getFeelLabel(temp: number): string {
    if (temp > 35) return "🥵 Hot";
    if (temp > 20) return "☀️ Warm";
    if (temp > 10) return "🧥 Cool";
    return "🥶 Cold";
}

export const WeatherCard: React.FC<WeatherCardProps> = ({
    title, city, temp_c, condition, wind_kmh, humidity,
}) => {
    const icon = WEATHER_ICONS[condition] || "🌡️";

    return (
        <div className="aether-card weather-card">
            <div className="aether-card-header">
                <span className="aether-card-icon">{icon}</span>
                <h3>{city}</h3>
            </div>
            <div className="aether-card-body">
                <div className="weather-hero">
                    <span className="weather-temp">{temp_c.toFixed(1)}°C</span>
                    <span className="weather-feel">{getFeelLabel(temp_c)}</span>
                </div>
                <div className="weather-details">
                    <div className="weather-detail">
                        <span>💨</span> {wind_kmh} km/h
                    </div>
                    <div className="weather-detail">
                        <span>💧</span> {humidity}%
                    </div>
                </div>
            </div>
        </div>
    );
};
