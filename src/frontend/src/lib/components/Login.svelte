<script>
  import { navigate } from 'svelte-routing';
  import { login as authLogin } from '../../stores/auth';
  import { auth } from '../api/client';

  let username = '';
  let password = '';
  let error = '';
  let loading = false;

  async function handleLogin() {
    if (!username || !password) {
      error = 'Please enter username and password';
      return;
    }

    loading = true;
    error = '';

    try {
      const response = await auth.login(username, password);
      
      // Set token first so it's available for subsequent requests
      authLogin(response.access_token, { username });
      
      // Now fetch user data with the token set
      const userData = await auth.getMe();
      
      // Update with complete user data
      authLogin(response.access_token, userData);
      navigate('/', { replace: true });
    } catch (err) {
      console.error('Login error:', err);
      error = err.response?.data?.detail || 'Login failed. Please check your credentials.';
    } finally {
      loading = false;
    }
  }

  function handleKeyPress(event) {
    if (event.key === 'Enter') {
      handleLogin();
    }
  }
</script>

<div class="login-container">
  <div class="login-card">
    <div class="login-header">
      <h1>ReMo</h1>
      <p>Real-time Monitoring System</p>
    </div>

    {#if error}
      <div class="error">
        {error}
      </div>
    {/if}

    <form on:submit|preventDefault={handleLogin}>
      <div class="form-group">
        <label for="username">Username</label>
        <input
          id="username"
          type="text"
          bind:value={username}
          on:keypress={handleKeyPress}
          placeholder="Enter your username"
          disabled={loading}
        />
      </div>

      <div class="form-group">
        <label for="password">Password</label>
        <input
          id="password"
          type="password"
          bind:value={password}
          on:keypress={handleKeyPress}
          placeholder="Enter your password"
          disabled={loading}
        />
      </div>

      <button type="submit" class="primary login-btn" disabled={loading}>
        {loading ? 'Logging in...' : 'Login'}
      </button>
    </form>

    <div class="login-footer">
      <p>Default credentials: admin / admin123</p>
    </div>
  </div>
</div>

<style>
  .login-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }

  .login-card {
    background: var(--card-bg);
    border-radius: 12px;
    padding: 40px;
    width: 100%;
    max-width: 400px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  }

  .login-header {
    text-align: center;
    margin-bottom: 30px;
  }

  .login-header h1 {
    font-size: 2.5rem;
    margin-bottom: 5px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .login-header p {
    color: var(--text-muted);
    font-size: 0.9rem;
  }

  .login-btn {
    width: 100%;
    padding: 12px;
    font-size: 16px;
    margin-top: 10px;
  }

  .login-footer {
    margin-top: 20px;
    text-align: center;
    padding-top: 20px;
    border-top: 1px solid var(--border-color);
  }

  .login-footer p {
    color: var(--text-muted);
    font-size: 0.85rem;
  }
</style>
