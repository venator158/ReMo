<script>
  import { createEventDispatcher } from 'svelte';
  import { nodes } from '../api/client';

  export let nodeId;
  export let nodeName;
  export let show = false;

  const dispatch = createEventDispatcher();

  let password = '';
  let error = '';
  let loading = false;

  async function handleSubmit() {
    if (!password) {
      error = 'Please enter node password';
      return;
    }

    loading = true;
    error = '';

    try {
      const response = await nodes.authenticate(nodeId, password);
      
      if (response.access_granted) {
        dispatch('authenticated', { nodeId, password });
        closeModal();
      } else {
        error = response.message || 'Invalid password';
      }
    } catch (err) {
      console.error('Node authentication error:', err);
      error = err.response?.data?.detail || 'Authentication failed';
    } finally {
      loading = false;
    }
  }

  function closeModal() {
    show = false;
    password = '';
    error = '';
    dispatch('close');
  }

  function handleKeyPress(event) {
    if (event.key === 'Enter') {
      handleSubmit();
    } else if (event.key === 'Escape') {
      closeModal();
    }
  }
</script>

{#if show}
  <div class="modal-overlay" on:click={closeModal}>
    <div class="modal-content" on:click|stopPropagation>
      <div class="modal-header">
        <h3>🔒 Node Authentication Required</h3>
        <button class="close-btn" on:click={closeModal}>&times;</button>
      </div>

      <div class="modal-body">
        <p class="node-info">
          Enter password to access <strong>{nodeName}</strong> ({nodeId})
        </p>

        {#if error}
          <div class="error">{error}</div>
        {/if}

        <form on:submit|preventDefault={handleSubmit}>
          <div class="form-group">
            <label for="node-password">Node Password</label>
            <input
              id="node-password"
              type="password"
              bind:value={password}
              on:keypress={handleKeyPress}
              placeholder="Enter node password"
              disabled={loading}
              autofocus
            />
          </div>

          <div class="button-group">
            <button type="button" class="secondary" on:click={closeModal} disabled={loading}>
              Cancel
            </button>
            <button type="submit" class="primary" disabled={loading}>
              {loading ? 'Authenticating...' : 'Authenticate'}
            </button>
          </div>
        </form>

        <div class="help-text">
          <p>💡 Default node password: <code>node123</code></p>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    backdrop-filter: blur(4px);
  }

  .modal-content {
    background: var(--card-bg);
    border-radius: 12px;
    width: 90%;
    max-width: 500px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
    animation: slideIn 0.3s ease-out;
  }

  @keyframes slideIn {
    from {
      transform: translateY(-50px);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 25px;
    border-bottom: 1px solid var(--border-color);
  }

  .modal-header h3 {
    margin: 0;
    color: var(--text-color);
    font-size: 1.3rem;
  }

  .close-btn {
    background: none;
    border: none;
    font-size: 2rem;
    color: var(--text-muted);
    cursor: pointer;
    padding: 0;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 6px;
    transition: all 0.2s;
  }

  .close-btn:hover {
    background: var(--bg-color);
    color: var(--text-color);
  }

  .modal-body {
    padding: 25px;
  }

  .node-info {
    color: var(--text-muted);
    margin-bottom: 20px;
    font-size: 0.95rem;
  }

  .node-info strong {
    color: var(--text-color);
  }

  .button-group {
    display: flex;
    gap: 10px;
    margin-top: 20px;
  }

  .button-group button {
    flex: 1;
  }

  .help-text {
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid var(--border-color);
  }

  .help-text p {
    color: var(--text-muted);
    font-size: 0.85rem;
    margin: 0;
  }

  .help-text code {
    background: var(--bg-color);
    padding: 2px 6px;
    border-radius: 4px;
    color: var(--primary-color);
    font-family: 'Courier New', monospace;
  }
</style>
