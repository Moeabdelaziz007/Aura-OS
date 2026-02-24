#!/bin/bash
set -e

# AetherOS Orchestrator Docker Entrypoint
# This script sets up the environment and starts the main application

echo "🚀 Starting AetherOS Orchestrator..."
echo "Environment: ${AETHER_ENV:-production}"
echo "Log Level: ${AETHER_LOG_LEVEL:-INFO}"

# Ensure data directories exist (ownership set by Dockerfile at build time)
mkdir -p /app/data /app/logs /app/config/.aether

# Execute the main application
exec python -m agent.aether_orchestrator.main "$@"
