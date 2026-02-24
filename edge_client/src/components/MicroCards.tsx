/**
 * 📰 NewsCard — AetherOS Micro-UI Component
 * 💻 CodeBlock — AetherOS Micro-UI Component
 * ℹ️ InfoCard — AetherOS Micro-UI Component (Fallback)
 */

import React from "react";

// ─── NewsCard ─────────────────────────────

interface Article {
    title: string;
    source: string;
    url: string;
    time: string;
}

interface NewsCardProps {
    title: string;
    articles: Article[];
}

export const NewsCard: React.FC<NewsCardProps> = ({ title, articles }) => (
    <div className="aether-card">
        <div className="aether-card-header">
            <span className="aether-card-icon">📰</span>
            <h3>{title}</h3>
        </div>
        <div className="aether-card-body">
            {articles.map((article, i) => (
                <div key={i} className="news-row">
                    <span className="news-title">{article.title}</span>
                    <span className="news-source">{article.source}</span>
                </div>
            ))}
        </div>
    </div>
);

// ─── CodeBlock ────────────────────────────

interface CodeBlockProps {
    title: string;
    language: string;
    code: string;
    filename?: string;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({ title, language, code, filename }) => (
    <div className="aether-card code-card">
        <div className="aether-card-header">
            <span className="aether-card-icon">💻</span>
            <h3>{filename || title}</h3>
            <span className="aether-badge">{language}</span>
        </div>
        <div className="aether-card-body">
            <pre className="code-block">
                <code>{code}</code>
            </pre>
        </div>
    </div>
);

// ─── InfoCard (Fallback) ──────────────────

interface InfoCardProps {
    title: string;
    content: Record<string, any>;
}

export const InfoCard: React.FC<InfoCardProps> = ({ title, content }) => (
    <div className="aether-card">
        <div className="aether-card-header">
            <span className="aether-card-icon">ℹ️</span>
            <h3>{title}</h3>
        </div>
        <div className="aether-card-body">
            {Object.entries(content).map(([key, value]) => (
                <div key={key} className="info-row">
                    <span className="info-key">{key}</span>
                    <span className="info-value">{String(value)}</span>
                </div>
            ))}
        </div>
    </div>
);

// ─── CalendarView ─────────────────────────

interface CalendarEvent {
    title: string;
    time?: string;
    duration?: string;
}

interface CalendarViewProps {
    title: string;
    events: CalendarEvent[];
    date: string;
}

export const CalendarView: React.FC<CalendarViewProps> = ({ title, events, date }) => (
    <div className="aether-card">
        <div className="aether-card-header">
            <span className="aether-card-icon">📅</span>
            <h3>{title}</h3>
            <span className="aether-badge">{date}</span>
        </div>
        <div className="aether-card-body">
            {events.map((event, i) => (
                <div key={i} className="calendar-row">
                    <span className="calendar-time">{event.time || "—"}</span>
                    <span className="calendar-title">{event.title}</span>
                </div>
            ))}
        </div>
    </div>
);

// ─── ChartCard (placeholder) ──────────────

interface ChartCardProps {
    title: string;
    type: string;
    labels: string[];
    datasets: any[];
}

export const ChartCard: React.FC<ChartCardProps> = ({ title, type }) => (
    <div className="aether-card">
        <div className="aether-card-header">
            <span className="aether-card-icon">📊</span>
            <h3>{title}</h3>
            <span className="aether-badge">{type}</span>
        </div>
        <div className="aether-card-body">
            <div className="chart-placeholder">Chart visualization ({type})</div>
        </div>
    </div>
);

// ─── DataTable ────────────────────────────

export const DataTable: React.FC<InfoCardProps> = InfoCard;
