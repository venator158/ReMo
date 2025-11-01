<script>
  import { onMount, onDestroy } from 'svelte';
  import { alerts } from '../api/client';

  export let nodeId = null;
  export let autoRefresh = true;

  let alertsList = [];
  let loading = true;
  let error = '';
  let filter = 'unacknowledged'; // 'all', 'unacknowledged', 'acknowledged'
  let refreshInterval;

  onMount(async () => {
    await loadAlerts();
    
    if (autoRefresh) {
      refreshInterval = setInterval(loadAlerts, 10000); // Refresh every 10 seconds
    }
  });

  onDestroy(() => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
  });

  async function loadAlerts() {
    try {
      const acknowledged = filter === 'all' ? null : filter === 'acknowledged';
      alertsList = await alerts.getAll(nodeId, acknowledged);
      error = '';
    } catch (err) {
      console.error('Error loading alerts:', err);
      error = 'Failed to load alerts';
    } finally {
      loading = false;
    }
  }

  async function handleAcknowledge(alertId) {
    try {
      await alerts.acknowledge(alertId);
      await loadAlerts();
    } catch (err) {
      console.error('Error acknowledging alert:', err);
      error = 'Failed to acknowledge alert';
    }
  }

  function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  $: {
    if (filter) {
      loadAlerts();
    }
  }
</script>

<div class="alert-panel">
  <div class="panel-header">
    <h3>Alerts</h3>
    <div class="filter-group">
      <button 
        class:active={filter === 'unacknowledged'}
        on:click={() => filter = 'unacknowledged'}
      >
        Unacknowledged
      </button>
      <button 
        class:active={filter === 'all'}
        on:click={() => filter = 'all'}
      >
        All
      </button>
      <button 
        class:active={filter === 'acknowledged'}
        on:click={() => filter = 'acknowledged'}
      >
        Acknowledged
      </button>
    </div>
  </div>

  {#if error}
    <div class="error">{error}</div>
  {/if}

  {#if loading}
    <div class="loading">Loading alerts...</div>
  {:else if alertsList.length === 0}
    <div class="no-alerts">
      <p>No alerts to display</p>
    </div>
  {:else}
    <div class="alerts-list">
      {#each alertsList as alert}
        <div class="alert-item {alert.severity}" class:acknowledged={alert.acknowledged}>
          <div class="alert-content">
            <div class="alert-header">
              <span class="badge {alert.severity}">{alert.severity.toUpperCase()}</span>
              <span class="alert-node">{alert.node_id}</span>
              <span class="alert-time">{formatTimestamp(alert.created_at)}</span>
            </div>
            <div class="alert-message">
              {alert.message}
            </div>
            <div class="alert-details">
              <span>Metric: {alert.metric_type}</span>
              <span>Value: {alert.metric_value}</span>
              <span>Threshold: {alert.threshold_value}</span>
            </div>
          </div>
          {#if !alert.acknowledged}
            <div class="alert-actions">
              <button 
                class="secondary small"
                on:click={() => handleAcknowledge(alert.id)}
              >
                Acknowledge
              </button>
            </div>
          {:else}
            <div class="alert-status">
              <span class="ack-badge">✓ Acknowledged</span>
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .alert-panel {
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
    padding-bottom: 15px;
    border-bottom: 1px solid var(--border-color);
  }

  .panel-header h3 {
    margin: 0;
  }

  .filter-group {
    display: flex;
    gap: 5px;
  }

  .filter-group button {
    padding: 6px 12px;
    font-size: 12px;
    background: var(--bg-color);
    color: var(--text-muted);
    border: 1px solid var(--border-color);
  }

  .filter-group button.active {
    background: var(--primary-color);
    color: white;
    border-color: var(--primary-color);
  }

  .alerts-list {
    flex: 1;
    overflow-y: auto;
    max-height: 600px;
  }

  .alert-item {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 15px;
    margin-bottom: 10px;
    border-radius: 6px;
    border-left: 4px solid;
  }

  .alert-item.warning {
    background: rgba(245, 158, 11, 0.1);
    border-left-color: var(--warning-color);
  }

  .alert-item.critical {
    background: rgba(239, 68, 68, 0.1);
    border-left-color: var(--danger-color);
  }

  .alert-item.acknowledged {
    opacity: 0.6;
  }

  .alert-content {
    flex: 1;
  }

  .alert-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
  }

  .alert-node {
    font-weight: 600;
    color: var(--text-color);
  }

  .alert-time {
    color: var(--text-muted);
    font-size: 0.85rem;
    margin-left: auto;
  }

  .alert-message {
    color: var(--text-color);
    margin-bottom: 8px;
  }

  .alert-details {
    display: flex;
    gap: 15px;
    font-size: 0.85rem;
    color: var(--text-muted);
  }

  .alert-actions {
    margin-left: 15px;
  }

  .alert-status {
    margin-left: 15px;
  }

  .ack-badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 12px;
    background: rgba(16, 185, 129, 0.2);
    color: var(--success-color);
  }

  button.small {
    padding: 6px 12px;
    font-size: 12px;
  }

  .no-alerts {
    text-align: center;
    padding: 40px;
    color: var(--text-muted);
  }

  .loading {
    text-align: center;
    padding: 40px;
    color: var(--text-muted);
  }
</style>
