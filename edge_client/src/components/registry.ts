/**
 * 🗂️ AetherOS — Component Registry
 *
 * Maps component names from UI manifests to React components.
 * When a manifest arrives via WebSocket with component: "CryptoCard",
 * the registry resolves it to the CryptoCard React component.
 */

import React from "react";

import { CryptoCard } from "./CryptoCard";
import { TaskListCard } from "./TaskListCard";
import { WeatherCard } from "./WeatherCard";
import {
    NewsCard,
    CodeBlock,
    InfoCard,
    CalendarView,
    ChartCard,
    DataTable,
} from "./MicroCards";

/**
 * Registry mapping component names (from server manifests)
 * to React component implementations.
 */
export const COMPONENT_REGISTRY: Record<string, React.FC<any>> = {
    CryptoCard,
    TaskListCard,
    WeatherCard,
    NewsCard,
    CodeBlock,
    InfoCard,
    CalendarView,
    ChartCard,
    DataTable,
};

/**
 * Resolve a component name to its React implementation.
 * Falls back to InfoCard for unknown types.
 */
export function resolveComponent(name: string): React.FC<any> {
    return COMPONENT_REGISTRY[name] || InfoCard;
}
