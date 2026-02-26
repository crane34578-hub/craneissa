const layers = [
  { key: 'transport', name: 'Transit Corridors', weight: 'High', status: 'stable' },
  { key: 'infrastructure', name: 'Critical Infrastructure', weight: 'Medium', status: 'stable' },
  { key: 'risk', name: 'Risk Signals', weight: 'High', status: 'watch' },
];

const nodes = [
  { id: 'A1', type: 'transport', name: 'Rail Junction', risk: 28, signal: 'Nominal flow' },
  { id: 'A2', type: 'infrastructure', name: 'Power Relay', risk: 22, signal: 'Load balancing' },
  { id: 'A3', type: 'risk', name: 'Anomaly Cluster', risk: 71, signal: 'Abnormal pattern' },
  { id: 'A4', type: 'transport', name: 'Port Node', risk: 40, signal: 'Moderate congestion' },
  { id: 'A5', type: 'infrastructure', name: 'Water Hub', risk: 19, signal: 'Pressure normal' },
  { id: 'A6', type: 'risk', name: 'Cyber Signal', risk: 63, signal: 'Persistent probing' },
  { id: 'B1', type: 'transport', name: 'Freight Spine', risk: 32, signal: 'Backlog clearing' },
  { id: 'B2', type: 'infrastructure', name: 'Data Center', risk: 35, signal: 'Usage up +8%' },
  { id: 'B3', type: 'risk', name: 'Route Deviation', risk: 77, signal: 'Unauthorized routing' },
  { id: 'B4', type: 'transport', name: 'Airport Grid', risk: 25, signal: 'On-time operations' },
  { id: 'B5', type: 'infrastructure', name: 'Hospital Network', risk: 14, signal: 'Capacity healthy' },
  { id: 'B6', type: 'risk', name: 'Flood Probability', risk: 58, signal: 'Rain front projected' },
  { id: 'C1', type: 'transport', name: 'Transit Hub', risk: 31, signal: 'Steady throughput' },
  { id: 'C2', type: 'infrastructure', name: 'Fuel Depot', risk: 44, signal: 'Supply dip' },
  { id: 'C3', type: 'risk', name: 'Crowd Spike', risk: 67, signal: 'Event overflow' },
  { id: 'C4', type: 'transport', name: 'Bridge Arc', risk: 29, signal: 'Maintenance planned' },
  { id: 'C5', type: 'infrastructure', name: 'Fiber Backbone', risk: 26, signal: 'Packet loss minimal' },
  { id: 'C6', type: 'risk', name: 'Border Alert', risk: 73, signal: 'Crossing anomaly' },
];

const mapGrid = document.getElementById('mapGrid');
const nodeDetails = document.getElementById('nodeDetails');
const layerList = document.getElementById('layerList');
const timeline = document.getElementById('timeline');
const activeFilter = document.getElementById('activeFilter');
const simulateFeed = document.getElementById('simulateFeed');
const clearSelection = document.getElementById('clearSelection');

let selectedNodeId = null;
let currentFilter = 'all';

function renderLayers() {
  layerList.innerHTML = layers
    .map(
      (layer) => `<li><span>${layer.name}</span><span>${layer.weight}</span></li>`
    )
    .join('');
}

function renderTimeline(node) {
  const events = node
    ? [
        `Node ${node.id} refreshed 3m ago`,
        `${node.name} emits signal: ${node.signal}`,
        `Risk score at ${node.risk}% (${node.risk > 60 ? 'escalated' : 'within threshold'})`,
      ]
    : [
        'Awaiting node selection',
        'System ingesting telemetry',
        'No active intervention request',
      ];

  timeline.innerHTML = events.map((event) => `<li>${event}</li>`).join('');
}

function renderDetails(node) {
  if (!node) {
    nodeDetails.classList.add('empty');
    nodeDetails.textContent = 'Pick any map tile to inspect mission context.';
    renderTimeline(null);
    return;
  }

  nodeDetails.classList.remove('empty');
  const statusClass = node.risk > 60 ? 'status-risk' : 'status-ok';
  const statusText = node.risk > 60 ? 'Escalate response' : 'Monitor';
  nodeDetails.innerHTML = `
    <strong>${node.id}: ${node.name}</strong><br />
    Category: ${node.type}<br />
    Signal: ${node.signal}<br />
    Risk Index: <span class="${statusClass}">${node.risk}%</span><br />
    Recommendation: <span class="${statusClass}">${statusText}</span>
  `;

  renderTimeline(node);
}

function renderMap() {
  const visibleNodes =
    currentFilter === 'all' ? nodes : nodes.filter((node) => node.type === currentFilter);

  mapGrid.innerHTML = visibleNodes
    .map(
      (node) => `
      <button class="tile ${node.type} ${selectedNodeId === node.id ? 'selected' : ''}" data-id="${node.id}">
        <strong>${node.id}</strong>
        <small>${node.name}</small>
      </button>
    `
    )
    .join('');

  mapGrid.querySelectorAll('.tile').forEach((tile) => {
    tile.addEventListener('click', () => {
      selectedNodeId = tile.dataset.id;
      renderMap();
      renderDetails(nodes.find((node) => node.id === selectedNodeId));
    });
  });
}

function wireFilters() {
  document.querySelectorAll('.filter-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilter = btn.dataset.filter;
      activeFilter.textContent = `Filter: ${btn.textContent} Layers`;
      selectedNodeId = null;
      renderMap();
      renderDetails(null);
    });
  });
}

simulateFeed.addEventListener('click', () => {
  nodes.forEach((node) => {
    const drift = Math.floor(Math.random() * 11) - 5;
    node.risk = Math.max(5, Math.min(95, node.risk + drift));
  });

  renderMap();
  if (selectedNodeId) {
    renderDetails(nodes.find((node) => node.id === selectedNodeId));
  }
});

clearSelection.addEventListener('click', () => {
  selectedNodeId = null;
  renderMap();
  renderDetails(null);
});

renderLayers();
wireFilters();
renderMap();
renderDetails(null);
