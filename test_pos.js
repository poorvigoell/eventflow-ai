function getNodePositions(numAgents, width, height) {
  const cx = width / 2;
  const cy = height / 2;
  const maxRadius = Math.min(width / 2, height / 2) - 75;
  const radius = Math.max(maxRadius, 50);

  const positions = [];
  for (let i = 0; i < numAgents; i++) {
    const angle = (-Math.PI / 2) + (2 * Math.PI * i) / numAgents;
    positions.push({
      i,
      angle: angle * 180 / Math.PI,
      x: cx + radius * Math.cos(angle),
      y: cy + radius * Math.sin(angle),
    });
  }
  return positions;
}
console.log(getNodePositions(5, 1000, 300));
console.log(getNodePositions(3, 1000, 300));
