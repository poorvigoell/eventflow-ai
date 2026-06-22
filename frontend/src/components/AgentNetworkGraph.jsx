import { useState, useEffect, useRef } from 'react';

/**
 * AgentNetworkGraph — SVG visualization of the MARL agent network.
 * 
 * Renders N agent nodes in a pentagon layout, with edges between
 * adjacent agents. Animates message-passing as colored pulses
 * traveling along edges.
 */

const AGENT_COLORS = [
  '#06d6a0', // mint green
  '#118ab2', // cerulean blue
  '#ef476f', // pink
  '#ffd166', // amber
  '#8338ec', // purple
];

const NODE_RADIUS = 38;

function getNodePositions(numAgents, width, height) {
  const cx = width / 2;
  const cy = height / 2;
  
  // Use elliptical layout to take advantage of the wide container
  // Keep enough padding for the node radius (~38), glow, and text (~20 below)
  const paddingX = 100;
  const paddingY = 85;
  
  const rx = Math.max(width / 2 - paddingX, 100);
  const ry = Math.max(height / 2 - paddingY, 60);

  const positions = [];
  for (let i = 0; i < numAgents; i++) {
    // Start from top (-90°) and go clockwise
    const angle = (-Math.PI / 2) + (2 * Math.PI * i) / numAgents;
    positions.push({
      x: cx + rx * Math.cos(angle),
      y: cy + ry * Math.sin(angle),
    });
  }
  return positions;
}

function MessagePulse({ x1, y1, x2, y2, color, delay }) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    setVisible(true);
    const timer = setTimeout(() => setVisible(false), 1200);
    return () => clearTimeout(timer);
  }, [x1, y1, x2, y2]);

  if (!visible) return null;

  const id = `pulse-${x1.toFixed(0)}-${y1.toFixed(0)}-${x2.toFixed(0)}-${y2.toFixed(0)}`;

  return (
    <>
      <circle r="5" fill={color} opacity="0.9" filter="url(#glow)">
        <animateMotion
          dur="0.8s"
          begin={`${delay}s`}
          repeatCount="1"
          fill="freeze"
          path={`M${x1},${y1} L${x2},${y2}`}
        />
        <animate attributeName="r" values="5;8;3" dur="0.8s" begin={`${delay}s`} repeatCount="1" />
        <animate attributeName="opacity" values="0.9;1;0" dur="0.8s" begin={`${delay}s`} repeatCount="1" />
      </circle>
    </>
  );
}

export function AgentNetworkGraph({ agents, adjacency, step }) {
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 500, height: 400 });

  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          setDimensions({ width, height });
        }
      }
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  if (!agents || agents.length === 0 || !adjacency) return null;

  const { width, height } = dimensions;
  const positions = getNodePositions(agents.length, width, height);

  // Collect edges from adjacency matrix
  const edges = [];
  for (let i = 0; i < adjacency.length; i++) {
    for (let j = i + 1; j < adjacency[i].length; j++) {
      if (adjacency[i][j]) {
        edges.push({ from: i, to: j });
      }
    }
  }

  // Determine which agents sent messages this step (non-zero message_sent)
  const activeMessages = [];
  if (agents) {
    for (const agent of agents) {
      if (agent.message_sent && agent.messages_received) {
        const msgMagnitude = agent.message_sent.reduce((s, v) => s + Math.abs(v), 0);
        if (msgMagnitude > 0.1) {
          // This agent sent a message; animate to each neighbor
          const neighbors = Object.keys(agent.messages_received);
          for (const nKey of neighbors) {
            const nIdx = parseInt(nKey);
            activeMessages.push({
              from: agent.id,
              to: nIdx,
              magnitude: msgMagnitude,
            });
          }
        }
      }
    }
  }

  return (
    <div ref={containerRef} className="w-full h-full min-h-[320px] relative">
      <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`}>
        <defs>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <radialGradient id="nodeGlow">
            <stop offset="0%" stopColor="var(--color-accent)" stopOpacity="0.15" />
            <stop offset="100%" stopColor="var(--color-accent)" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Edges */}
        {edges.map(({ from, to }, idx) => (
          <line
            key={`edge-${idx}`}
            x1={positions[from].x}
            y1={positions[from].y}
            x2={positions[to].x}
            y2={positions[to].y}
            stroke="var(--color-border)"
            strokeWidth="2"
            strokeDasharray="6 4"
            opacity="0.5"
          />
        ))}

        {/* Message pulses */}
        {activeMessages.map((msg, idx) => {
          const fromPos = positions[msg.from];
          const toPos = positions[msg.to];
          const color = msg.magnitude > 2 ? '#ef476f' : '#06d6a0';
          return (
            <MessagePulse
              key={`msg-${step}-${msg.from}-${msg.to}-${idx}`}
              x1={fromPos.x}
              y1={fromPos.y}
              x2={toPos.x}
              y2={toPos.y}
              color={color}
              delay={idx * 0.1}
            />
          );
        })}

        {/* Agent nodes */}
        {agents.map((agent, i) => {
          const pos = positions[i];
          const queuePct = Math.min(100, (agent.queue / 600) * 100);
          const isPositive = agent.adjustment_sec > 0;
          const isNegative = agent.adjustment_sec < 0;

          return (
            <g key={`agent-${i}`}>
              {/* Glow circle */}
              <circle cx={pos.x} cy={pos.y} r={NODE_RADIUS + 15} fill="url(#nodeGlow)" />

              {/* Background circle */}
              <circle
                cx={pos.x}
                cy={pos.y}
                r={NODE_RADIUS}
                fill="var(--color-surface)"
                stroke={AGENT_COLORS[i]}
                strokeWidth="3"
                style={{
                  filter: isPositive ? 'drop-shadow(0 0 8px rgba(6, 214, 160, 0.5))' :
                         isNegative ? 'drop-shadow(0 0 8px rgba(239, 71, 111, 0.5))' : 'none',
                  transition: 'filter 0.3s ease',
                }}
              />

              {/* Queue arc (progress ring) */}
              <circle
                cx={pos.x}
                cy={pos.y}
                r={NODE_RADIUS - 3}
                fill="none"
                stroke={queuePct > 70 ? '#ef476f' : queuePct > 40 ? '#ffd166' : '#06d6a0'}
                strokeWidth="4"
                strokeDasharray={`${(queuePct / 100) * (2 * Math.PI * (NODE_RADIUS - 3))} ${2 * Math.PI * (NODE_RADIUS - 3)}`}
                strokeLinecap="round"
                transform={`rotate(-90, ${pos.x}, ${pos.y})`}
                opacity="0.7"
                style={{ transition: 'stroke-dasharray 0.5s ease' }}
              />

              {/* Green time text */}
              <text
                x={pos.x}
                y={pos.y - 6}
                textAnchor="middle"
                fill="var(--color-text-main)"
                fontSize="16"
                fontWeight="bold"
                fontFamily="monospace"
              >
                {Math.round(agent.new_green_sec)}s
              </text>

              {/* Agent ID */}
              <text
                x={pos.x}
                y={pos.y + 12}
                textAnchor="middle"
                fill={AGENT_COLORS[i]}
                fontSize="10"
                fontWeight="bold"
              >
                A{i + 1}
              </text>

              {/* Junction name below node */}
              <text
                x={pos.x}
                y={pos.y + NODE_RADIUS + 18}
                textAnchor="middle"
                fill="var(--color-text-muted)"
                fontSize="9"
                fontWeight="600"
              >
                {(agent.junction || '').substring(0, 18)}
              </text>

              {/* Adjustment badge */}
              {agent.adjustment_sec !== 0 && (
                <g>
                  <rect
                    x={pos.x + NODE_RADIUS - 8}
                    y={pos.y - NODE_RADIUS - 4}
                    width="28"
                    height="18"
                    rx="9"
                    fill={isPositive ? 'rgba(6, 214, 160, 0.2)' : 'rgba(239, 71, 111, 0.2)'}
                    stroke={isPositive ? '#06d6a0' : '#ef476f'}
                    strokeWidth="1"
                  />
                  <text
                    x={pos.x + NODE_RADIUS + 6}
                    y={pos.y - NODE_RADIUS + 9}
                    textAnchor="middle"
                    fill={isPositive ? '#06d6a0' : '#ef476f'}
                    fontSize="10"
                    fontWeight="bold"
                    fontFamily="monospace"
                  >
                    {isPositive ? '+' : ''}{agent.adjustment_sec}
                  </text>
                </g>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}
