/**
 * ✅ TaskListCard — AetherOS Micro-UI Component
 *
 * Shows tasks/tickets with status pills.
 * Materializes when user says "show my tickets" or "what are my tasks"
 */

import React from "react";

interface Task {
    id: string;
    title: string;
    status: string;
    priority: string;
    assignee?: string;
}

interface TaskListCardProps {
    title: string;
    items: Task[];
    count: number;
}

const STATUS_COLORS: Record<string, string> = {
    open: "#00d4ff",
    in_progress: "#ffd700",
    done: "#00ff88",
    closed: "#666",
    blocked: "#ff4444",
};

const PRIORITY_ICONS: Record<string, string> = {
    P1: "🔴",
    P2: "🟠",
    P3: "🟡",
    high: "🔴",
    normal: "🟡",
    low: "🟢",
};

export const TaskListCard: React.FC<TaskListCardProps> = ({ title, items, count }) => {
    return (
        <div className="aether-card">
            <div className="aether-card-header">
                <span className="aether-card-icon">✅</span>
                <h3>{title}</h3>
                <span className="aether-badge">{count}</span>
            </div>
            <div className="aether-card-body">
                {items.map((task) => (
                    <div key={task.id} className="task-row">
                        <span className="task-priority">
                            {PRIORITY_ICONS[task.priority] || "⚪"}
                        </span>
                        <div className="task-info">
                            <span className="task-title">{task.title}</span>
                            <span className="task-id">{task.id}</span>
                        </div>
                        <span
                            className="task-status"
                            style={{ color: STATUS_COLORS[task.status] || "#888" }}
                        >
                            {task.status.replace("_", " ")}
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
};
