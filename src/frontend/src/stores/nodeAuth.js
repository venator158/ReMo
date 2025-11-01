import { writable } from 'svelte/store';

const isBrowser = typeof window !== 'undefined';

// Store authenticated nodes { nodeId: password }
const storedNodeAuth = isBrowser ? sessionStorage.getItem('node_auth') : null;
export const authenticatedNodes = writable(storedNodeAuth ? JSON.parse(storedNodeAuth) : {});

// Subscribe to changes and update sessionStorage
authenticatedNodes.subscribe(value => {
  if (isBrowser) {
    sessionStorage.setItem('node_auth', JSON.stringify(value));
  }
});

export function authenticateNode(nodeId, password) {
  authenticatedNodes.update(nodes => ({
    ...nodes,
    [nodeId]: password
  }));
}

export function isNodeAuthenticated(nodeId) {
  let authenticated = false;
  authenticatedNodes.subscribe(nodes => {
    authenticated = !!nodes[nodeId];
  })();
  return authenticated;
}

export function getNodePassword(nodeId) {
  let password = null;
  authenticatedNodes.subscribe(nodes => {
    password = nodes[nodeId];
  })();
  return password;
}

export function clearNodeAuth(nodeId = null) {
  if (nodeId) {
    authenticatedNodes.update(nodes => {
      const updated = { ...nodes };
      delete updated[nodeId];
      return updated;
    });
  } else {
    authenticatedNodes.set({});
  }
}

export function clearAllNodeAuth() {
  authenticatedNodes.set({});
  if (isBrowser) {
    sessionStorage.removeItem('node_auth');
  }
}
