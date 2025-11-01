<script>
  import { onMount, onDestroy } from 'svelte';
  import { navigate } from 'svelte-routing';
  import { logout as authLogout, user } from '../../stores/auth';
  import { authenticatedNodes, authenticateNode, getNodePassword, clearAllNodeAuth } from '../../stores/nodeAuth';
  import { nodes, metrics, dashboard, exportData } from '../api/client';
  import MetricChart from './MetricChart.svelte';
  import ThresholdConfig from './ThresholdConfig.svelte';
  import AlertPanel from './AlertPanel.svelte';
  import NodePasswordModal from './NodePasswordModal.svelte';

  let currentUser = null;
  let loading = true;
  let error = '';
  
  // Dashboard data
  let nodesList = [];
  let selectedNode = null;
  let latestMetrics = {};
  let metricsHistory = {};
  let dashboardStats = {};
  
  // UI state
  let activeTab = 'overview'; // 'overview', 'metrics', 'thresholds', 'alerts'
  let showThresholdModal = false;
  
  // Node authentication
  let showNodePasswordModal = false;
  let pendingNodeSelection = null;
  let nodeAuthState = {};
  
  // Auto-refresh
  let refreshInterval;
  const REFRESH_INTERVAL = 5000; // 5 seconds

  user.subscribe(value => {
    currentUser = value;
  });

  authenticatedNodes.subscribe(value => {
    nodeAuthState = value;
  });

  onMount(async () => {
    await loadData();
    refreshInterval = setInterval(refreshMetrics, REFRESH_INTERVAL);
  });

  onDestroy(() => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
  });

  async function loadData() {
    try {
      loading = true;
      
      // Load all data in parallel
      const [nodesData, statsData, latestData] = await Promise.all([
        nodes.getAll(),
        dashboard.getStats(),
        metrics.getLatest()
      ]);

      nodesList = nodesData;
      dashboardStats = statsData;
      latestMetrics = latestData;

      // Don't auto-select a node - user must authenticate first
      // Keep selectedNode as null until user clicks a node and enters password

      error = '';
    } catch (err) {
      console.error('Error loading data:', err);
      error = 'Failed to load dashboard data';
    } finally {
      loading = false;
    }
  }

  async function refreshMetrics() {
    try {
      const [statsData, latestData] = await Promise.all([
        dashboard.getStats(),
        metrics.getLatest()
      ]);

      dashboardStats = statsData;
      latestMetrics = latestData;

      if (selectedNode && activeTab === 'metrics') {
        await loadNodeMetrics(selectedNode.node_id);
      }
    } catch (err) {
      console.error('Error refreshing metrics:', err);
    }
  }

  async function loadNodeMetrics(nodeId) {
    try {
      const nodePassword = getNodePassword(nodeId);
      if (!nodePassword) {
        console.error('No password for node:', nodeId);
        return;
      }
      const history = await metrics.getHistory(nodeId, nodePassword, null, 1); // Last 1 hour
      metricsHistory = history;
    } catch (err) {
      console.error('Error loading node metrics:', err);
      if (err.response?.status === 403) {
        error = 'Invalid node password. Please re-authenticate.';
        // Clear invalid authentication
        authenticateNode(nodeId, null);
      }
    }
  }

  async function handleNodeSelect(node) {
    // Check if node is already authenticated
    const nodePassword = getNodePassword(node.node_id);
    
    if (nodePassword) {
      // Already authenticated, select the node
      selectedNode = node;
      await loadNodeMetrics(node.node_id);
    } else {
      // Need authentication
      pendingNodeSelection = node;
      showNodePasswordModal = true;
    }
  }

  function handleNodeAuthenticated(event) {
    const { nodeId, password } = event.detail;
    authenticateNode(nodeId, password);
    
    // If this was the pending selection, select it now
    if (pendingNodeSelection && pendingNodeSelection.node_id === nodeId) {
      selectedNode = pendingNodeSelection;
      loadNodeMetrics(nodeId);
      pendingNodeSelection = null;
    }
  }

  function handleModalClose() {
    showNodePasswordModal = false;
    pendingNodeSelection = null;
  }

  function handleLogout() {
    clearAllNodeAuth();
    authLogout();
    navigate('/login', { replace: true });
  }

  function getNodeStatus(nodeId) {
    const node = nodesList.find(n => n.node_id === nodeId);
    if (!node || !node.last_seen) return 'inactive';
    
    const lastSeen = new Date(node.last_seen);
    const now = new Date();
    const diffMinutes = (now - lastSeen) / 1000 / 60;
    
    return diffMinutes < 2 ? 'active' : 'inactive';
  }

  function formatTimestamp(timestamp) {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    return date.toLocaleString();
  }

  async function handleExportCSV() {
    try {
      const blob = await exportData.downloadCSV(selectedNode?.node_id, null, 24);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `metrics_${selectedNode?.node_id || 'all'}_${new Date().toISOString()}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Error exporting CSV:', err);
      error = 'Failed to export data';
    }
  }

  $: nodeMetrics = selectedNode ? latestMetrics[selectedNode.node_id] || {} : {};
</script>

<!-- Node Password Modal -->
{#if pendingNodeSelection}
  <NodePasswordModal 
    nodeId={pendingNodeSelection.node_id}
    nodeName={pendingNodeSelection.node_name}
    bind:show={showNodePasswordModal}
    on:authenticated={handleNodeAuthenticated}
    on:close={handleModalClose}
  />
{/if}

<div class="dashboard">
  <!-- Header -->
  <div class="header">
    <div class="header-left">
      <h1>🚀 ReMo Dashboard</h1>
    </div>
    <div class="header-right">
      <span class="user-info">Welcome, {currentUser?.username || 'User'}</span>
      <button class="secondary" on:click={handleLogout}>Logout</button>
    </div>
  </div>

  {#if error}
    <div class="error">{error}</div>
  {/if}

  {#if loading}
    <div class="loading">Loading dashboard...</div>
  {:else}
    <div class="container">
      <!-- Stats Cards -->
      <div class="stats-grid grid grid-4">
        <div class="stat-card">
          <div class="stat-value">{dashboardStats.total_nodes || 0}</div>
          <div class="stat-label">Total Nodes</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color: var(--success-color)">
            {dashboardStats.active_nodes || 0}
          </div>
          <div class="stat-label">Active Nodes</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color: var(--danger-color)">
            {dashboardStats.unacknowledged_alerts || 0}
          </div>
          <div class="stat-label">Active Alerts</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{dashboardStats.metrics_last_hour || 0}</div>
          <div class="stat-label">Metrics (1h)</div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="tabs">
        <button 
          class:active={activeTab === 'overview'}
          on:click={() => activeTab = 'overview'}
        >
          Overview
        </button>
        <button 
          class:active={activeTab === 'metrics'}
          on:click={() => activeTab = 'metrics'}
        >
          Metrics
        </button>
        <button 
          class:active={activeTab === 'thresholds'}
          on:click={() => activeTab = 'thresholds'}
        >
          Thresholds
        </button>
        <button 
          class:active={activeTab === 'alerts'}
          on:click={() => activeTab = 'alerts'}
        >
          Alerts
        </button>
      </div>

      <!-- Tab Content -->
      {#if activeTab === 'overview'}
        <div class="tab-content">
          <div class="grid grid-2">
            <!-- Nodes List -->
            <div class="card">
              <h2>Nodes</h2>
              <div class="nodes-list">
                {#each nodesList as node}
                  <div 
                    class="node-item"
                    class:selected={selectedNode?.node_id === node.node_id}
                    on:click={() => handleNodeSelect(node)}
                  >
                    <div class="node-info">
                      <div class="node-name">
                        <span class="status-indicator {getNodeStatus(node.node_id)}"></span>
                        {node.node_name}
                        {#if nodeAuthState[node.node_id]}
                          <span class="auth-badge" title="Authenticated">🔓</span>
                        {:else}
                          <span class="auth-badge locked" title="Not Authenticated">🔒</span>
                        {/if}
                      </div>
                      <div class="node-id">{node.node_id}</div>
                      <div class="node-last-seen">
                        Last seen: {formatTimestamp(node.last_seen)}
                      </div>
                    </div>
                    {#if latestMetrics[node.node_id]}
                      <div class="node-metrics-preview">
                        <div class="metric-pill">
                          CPU: {latestMetrics[node.node_id].cpu_usage?.value.toFixed(1) || 'N/A'}%
                        </div>
                        <div class="metric-pill">
                          MEM: {latestMetrics[node.node_id].memory_usage?.value.toFixed(1) || 'N/A'}%
                        </div>
                      </div>
                    {/if}
                  </div>
                {/each}
              </div>
            </div>

            <!-- Current Metrics -->
            {#if selectedNode}
              <div class="card">
                <h2>{selectedNode.node_name} - Current Metrics</h2>
                <div class="current-metrics">
                  <div class="metric-row">
                    <span class="metric-label">CPU Usage:</span>
                    <span class="metric-value">
                      {nodeMetrics.cpu_usage?.value.toFixed(2) || 'N/A'}%
                    </span>
                  </div>
                  <div class="metric-row">
                    <span class="metric-label">Memory Usage:</span>
                    <span class="metric-value">
                      {nodeMetrics.memory_usage?.value.toFixed(2) || 'N/A'}%
                    </span>
                  </div>
                  <div class="metric-row">
                    <span class="metric-label">Disk I/O:</span>
                    <span class="metric-value">
                      {nodeMetrics.disk_io?.value.toFixed(2) || 'N/A'} MB/s
                    </span>
                  </div>
                  <div class="metric-row">
                    <span class="metric-label">Network Traffic:</span>
                    <span class="metric-value">
                      {nodeMetrics.network_traffic?.value.toFixed(2) || 'N/A'} Mbps
                    </span>
                  </div>
                </div>
              </div>
            {:else}
              <div class="card empty-state">
                <div class="empty-message">
                  <h3>🔒 No Node Selected</h3>
                  <p>Click on a node above and enter its password to view metrics</p>
                </div>
              </div>
            {/if}
          </div>
        </div>

      {:else if activeTab === 'metrics'}
        <div class="tab-content">
          {#if selectedNode}
            <div class="card">
              <div class="card-header">
                <h2>{selectedNode.node_name} - Metrics History</h2>
                <button class="secondary" on:click={handleExportCSV}>
                  Export CSV
                </button>
              </div>
              
              {#if Object.keys(metricsHistory).length > 0}
                <div class="charts-grid grid grid-2">
                  {#if metricsHistory.cpu_usage}
                    <div class="chart-card">
                      <h3>CPU Usage (%)</h3>
                      <MetricChart 
                        data={metricsHistory.cpu_usage}
                        label="CPU Usage"
                        color="#ef4444"
                        yAxisLabel="Percentage (%)"
                      />
                    </div>
                  {/if}

                  {#if metricsHistory.memory_usage}
                    <div class="chart-card">
                      <h3>Memory Usage (%)</h3>
                      <MetricChart 
                        data={metricsHistory.memory_usage}
                        label="Memory Usage"
                        color="#f59e0b"
                        yAxisLabel="Percentage (%)"
                      />
                    </div>
                  {/if}

                  {#if metricsHistory.disk_io}
                    <div class="chart-card">
                      <h3>Disk I/O (MB/s)</h3>
                      <MetricChart 
                        data={metricsHistory.disk_io}
                        label="Disk I/O"
                        color="#10b981"
                        yAxisLabel="MB/s"
                      />
                    </div>
                  {/if}

                  {#if metricsHistory.network_traffic}
                    <div class="chart-card">
                      <h3>Network Traffic (Mbps)</h3>
                      <MetricChart 
                        data={metricsHistory.network_traffic}
                        label="Network Traffic"
                        color="#6366f1"
                        yAxisLabel="Mbps"
                      />
                    </div>
                  {/if}
                </div>
              {:else}
                <div class="no-data">
                  <p>No metrics data available for this node</p>
                </div>
              {/if}
            </div>
          {:else}
            <div class="card empty-state">
              <div class="empty-message">
                <h3>🔒 No Node Selected</h3>
                <p>Click on a node and authenticate to view metrics history</p>
              </div>
            </div>
          {/if}
        </div>

      {:else if activeTab === 'thresholds'}
        <div class="tab-content">
          {#if selectedNode}
            <div class="card">
              <ThresholdConfig 
                nodeId={selectedNode.node_id}
                nodeName={selectedNode.node_name}
                onUpdate={loadData}
              />
            </div>
          {:else}
            <div class="card empty-state">
              <div class="empty-message">
                <h3>🔒 No Node Selected</h3>
                <p>Click on a node and authenticate to configure thresholds</p>
              </div>
            </div>
          {/if}
        </div>

      {:else if activeTab === 'alerts'}
        <div class="tab-content">
          <div class="card">
            <AlertPanel nodeId={selectedNode?.node_id} />
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .dashboard {
    min-height: 100vh;
    background: var(--bg-color);
  }

  .header-left {
    display: flex;
    align-items: center;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 15px;
  }

  .user-info {
    color: var(--text-muted);
    font-size: 0.9rem;
  }

  .stats-grid {
    margin-bottom: 20px;
  }

  .tabs {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
    border-bottom: 2px solid var(--border-color);
    padding-bottom: 10px;
  }

  .tabs button {
    padding: 10px 20px;
    background: transparent;
    color: var(--text-muted);
    border: none;
    border-bottom: 2px solid transparent;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s;
  }

  .tabs button:hover {
    color: var(--text-color);
  }

  .tabs button.active {
    color: var(--primary-color);
    border-bottom-color: var(--primary-color);
  }

  .tab-content {
    animation: fadeIn 0.3s;
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  .nodes-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .node-item {
    padding: 15px;
    background: var(--bg-color);
    border-radius: 6px;
    cursor: pointer;
    border: 2px solid transparent;
    transition: all 0.2s;
  }

  .node-item:hover {
    border-color: var(--primary-color);
  }

  .node-item.selected {
    border-color: var(--primary-color);
    background: rgba(79, 70, 229, 0.1);
  }

  .node-info {
    margin-bottom: 10px;
  }

  .node-name {
    font-weight: 600;
    color: var(--text-color);
    font-size: 1.1rem;
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 5px;
  }

  .auth-badge {
    font-size: 0.9rem;
    margin-left: auto;
  }

  .auth-badge.locked {
    opacity: 0.5;
  }

  .status-indicator {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    display: inline-block;
  }

  .status-indicator.active {
    background: var(--success-color);
    box-shadow: 0 0 8px var(--success-color);
  }

  .status-indicator.inactive {
    background: var(--text-muted);
  }

  .node-id {
    color: var(--text-muted);
    font-size: 0.85rem;
  }

  .node-last-seen {
    color: var(--text-muted);
    font-size: 0.8rem;
    margin-top: 3px;
  }

  .node-metrics-preview {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }

  .metric-pill {
    background: var(--card-bg);
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 0.85rem;
    color: var(--text-color);
  }

  .current-metrics {
    display: flex;
    flex-direction: column;
    gap: 15px;
  }

  .metric-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px;
    background: var(--bg-color);
    border-radius: 6px;
  }

  .metric-label {
    color: var(--text-muted);
    font-weight: 500;
  }

  .metric-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--primary-color);
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }

  .card-header h2 {
    margin: 0;
  }

  .charts-grid {
    gap: 20px;
  }

  .chart-card {
    background: var(--bg-color);
    padding: 15px;
    border-radius: 8px;
  }

  .chart-card h3 {
    margin-bottom: 15px;
    color: var(--text-color);
  }

  .no-data {
    text-align: center;
    padding: 60px 20px;
    color: var(--text-muted);
  }

  .empty-state {
    min-height: 300px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .empty-message {
    text-align: center;
    color: var(--text-muted);
  }

  .empty-message h3 {
    font-size: 1.5rem;
    margin-bottom: 10px;
    color: var(--text-color);
  }

  .empty-message p {
    font-size: 1rem;
    margin: 0;
  }
</style>
