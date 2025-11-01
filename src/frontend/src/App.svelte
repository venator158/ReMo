<script>
  import { Router, Route, navigate } from 'svelte-routing';
  import { onMount } from 'svelte';
  import { isAuthenticated } from './stores/auth';
  import Login from './lib/components/Login.svelte';
  import Dashboard from './lib/components/Dashboard.svelte';

  let authenticated = false;

  isAuthenticated.subscribe(value => {
    authenticated = value;
  });

  onMount(() => {
    if (!authenticated) {
      navigate('/login', { replace: true });
    }
  });
</script>

<Router>
  <Route path="/login" component={Login} />
  <Route path="/" component={Dashboard} />
  <Route path="/*" component={Dashboard} />
</Router>
