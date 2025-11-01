<script>
  import { onMount } from 'svelte';
  import { thresholds } from '../api/client';

  export let nodeId;
  export let nodeName;
  export let onUpdate = () => {};

  let loading = false;
  let error = '';
  let success = '';
  let currentThresholds = [];

  const metricTypes = [
    { value: 'cpu_usage', label: 'CPU Usage (%)' },
    { value: 'memory_usage', label: 'Memory Usage (%)' },
    { value: 'disk_io', label: 'Disk I/O (MB/s)' },
    { value: 'network_traffic', label: 'Network Traffic (Mbps)' }
  ];

  let newThreshold = {
    metric_type: 'cpu_usage',
    threshold_value: 80,
    condition: 'greater'
  };

  onMount(async () => {
    await loadThresholds();
  });

  async function loadThresholds() {
    try {
      const allThresholds = await thresholds.getAll(nodeId);
      currentThresholds = allThresholds;
    } catch (err) {
      console.error('Error loading thresholds:', err);
    }
  }

  async function handleSubmit() {
    error = '';
    success = '';
    loading = true;

    try {
      await thresholds.create(
        nodeId,
        newThreshold.metric_type,
        parseFloat(newThreshold.threshold_value),
        newThreshold.condition
      );

      success = 'Threshold saved successfully!';
      await loadThresholds();
      onUpdate();

      setTimeout(() => {
        success = '';
      }, 3000);
    } catch (err) {
      console.error('Error creating threshold:', err);
      error = err.response?.data?.detail || 'Failed to save threshold';
    } finally {
      loading = false;
    }
  }

  async function handleDelete(thresholdId) {
    if (!confirm('Are you sure you want to delete this threshold?')) {
      return;
    }

    try {
      await thresholds.delete(thresholdId);
      success = 'Threshold deleted successfully!';
      await loadThresholds();
      onUpdate();

      setTimeout(() => {
        success = '';
      }, 3000);
    } catch (err) {
      console.error('Error deleting threshold:', err);
      error = err.response?.data?.detail || 'Failed to delete threshold';
    }
  }

  function getMetricLabel(metricType) {
    const metric = metricTypes.find(m => m.value === metricType);
    return metric ? metric.label : metricType;
  }
</script>

<div class="threshold-config">
  <h3>Configure Thresholds for {nodeName}</h3>

  {#if error}
    <div class="error">{error}</div>
  {/if}

  {#if success}
    <div class="alert success">{success}</div>
  {/if}

  <div class="form-section">
    <h4>Add/Update Threshold</h4>
    <form on:submit|preventDefault={handleSubmit}>
      <div class="form-row">
        <div class="form-group">
          <label for="metric_type">Metric Type</label>
          <select id="metric_type" bind:value={newThreshold.metric_type}>
            {#each metricTypes as metric}
              <option value={metric.value}>{metric.label}</option>
            {/each}
          </select>
        </div>

        <div class="form-group">
          <label for="threshold_value">Threshold Value</label>
          <input
            id="threshold_value"
            type="number"
            step="0.01"
            bind:value={newThreshold.threshold_value}
            required
          />
        </div>

        <div class="form-group">
          <label for="condition">Condition</label>
          <select id="condition" bind:value={newThreshold.condition}>
            <option value="greater">Greater Than</option>
            <option value="less">Less Than</option>
          </select>
        </div>
      </div>

      <button type="submit" class="primary" disabled={loading}>
        {loading ? 'Saving...' : 'Save Threshold'}
      </button>
    </form>
  </div>

  {#if currentThresholds.length > 0}
    <div class="thresholds-list">
      <h4>Active Thresholds</h4>
      <table>
        <thead>
          <tr>
            <th>Metric</th>
            <th>Condition</th>
            <th>Threshold</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {#each currentThresholds as threshold}
            <tr>
              <td>{getMetricLabel(threshold.metric_type)}</td>
              <td>
                {threshold.condition === 'greater' ? '>' : '<'}
              </td>
              <td>{threshold.threshold_value}</td>
              <td>
                <button 
                  class="danger small"
                  on:click={() => handleDelete(threshold.id)}
                >
                  Delete
                </button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {:else}
    <div class="no-data">
      <p>No thresholds configured for this node.</p>
    </div>
  {/if}
</div>

<style>
  .threshold-config {
    padding: 20px;
  }

  h3 {
    margin-bottom: 20px;
    color: var(--text-color);
  }

  h4 {
    margin-bottom: 15px;
    color: var(--text-muted);
    font-size: 1rem;
  }

  .form-section {
    background: var(--bg-color);
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 20px;
  }

  .form-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
    margin-bottom: 15px;
  }

  .thresholds-list {
    background: var(--bg-color);
    padding: 20px;
    border-radius: 8px;
  }

  button.small {
    padding: 6px 12px;
    font-size: 12px;
  }

  .no-data {
    text-align: center;
    padding: 40px;
    color: var(--text-muted);
  }
</style>
