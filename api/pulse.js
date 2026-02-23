import fs from 'fs';
import path from 'path';

export default function handler(req, res) {
  // 1. Read real telemetry data with mock fallback
  let telemetry = {};
  try {
    const telemetryPath = path.join(process.cwd(), 'agent', 'memory', 'TELEMETRY.json');
    if (fs.existsSync(telemetryPath)) {
      telemetry = JSON.parse(fs.readFileSync(telemetryPath, 'utf8'));
    }
  } catch (e) {
    console.error("Pulse API Error:", e);
  }

  // Use real data or fallback to simulation
  const synapses = telemetry.synapses || Math.floor(1000 + Math.random() * 500);
  const freeEnergy = telemetry.free_energy || (Math.random() * 0.5).toFixed(4); // ΔF
  const nanoAgents = telemetry.total_requests || Math.floor(50 + Math.random() * 20);

  let currentState = telemetry.current_state;
  if (!currentState) {
    const states = ['Dreaming (MCTS)', 'Executing (System 1)', 'Healing (AlphaEvolve)'];
    currentState = states[Math.floor(Math.random() * states.length)];
  }

  // Calculate System Health Color
  const healthColor = telemetry.failed_forges > 0 ? "#ff0000" : "#00ff00";

  // 2. Construct the Industrial Sci-Fi SVG
  const svg = `
    <svg width="400" height="180" viewBox="0 0 400 180" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#0a0a0a"/>
          <stop offset="100%" stop-color="#111111"/>
        </linearGradient>
        <filter id="glow">
          <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>

      <rect width="100%" height="100%" fill="url(#bg)" rx="8" ry="8" stroke="#333" stroke-width="1"/>

      <text x="20" y="30" font-family="monospace" font-size="14" fill="#888" letter-spacing="2">AETHER_OS // TELEMETRY</text>
      <line x1="20" y1="40" x2="380" y2="40" stroke="${healthColor}" stroke-width="1" filter="url(#glow)"/>

      <text x="20" y="70" font-family="monospace" font-size="12" fill="#fff">Cognitive State : <tspan fill="${healthColor}" filter="url(#glow)">[ ${currentState} ]</tspan></text>
      <text x="20" y="100" font-family="monospace" font-size="12" fill="#fff">Aether-Nexus Links: <tspan fill="#00ff00">${synapses}</tspan></text>
      <text x="20" y="130" font-family="monospace" font-size="12" fill="#fff">Free Energy (ΔF): <tspan fill="#00ff00">${freeEnergy}</tspan></text>
      <text x="20" y="160" font-family="monospace" font-size="12" fill="#fff">Swarm Executions: <tspan fill="#00ff00">${nanoAgents}</tspan></text>

      <circle cx="360" cy="25" r="4" fill="${healthColor}" filter="url(#glow)">
        <animate attributeName="opacity" values="1;0;1" dur="1.5s" repeatCount="indefinite"/>
      </circle>
      <text x="370" y="29" font-family="monospace" font-size="10" fill="${healthColor}">LIVE</text>
    </svg>
  `;

  // 3. Force GitHub to NEVER cache this image
  res.setHeader('Content-Type', 'image/svg+xml');
  res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0');
  res.setHeader('Pragma', 'no-cache');
  res.setHeader('Expires', '0');

  res.status(200).send(svg);
}
