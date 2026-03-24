# Troubleshooting

Common issues and their solutions when running AgentAnycast components.

### Enable verbose logging

For any CLI command, pass `--verbose` (or `-v`) to see daemon startup logs, gRPC calls, and detailed error information:

```bash
agentanycast --verbose demo
agentanycast --verbose send 12D3KooW... "Hello!"
```

This is especially useful when diagnosing daemon startup failures or connection issues.

## Connection Issues

### "Connection refused" when starting the daemon

**Symptom:** The Python or TypeScript SDK throws a connection error when trying to communicate with the daemon, typically with a message like `failed to connect to daemon: connection refused`.

**Possible Causes:**
- The daemon (`agentanycastd`) is not running.
- The gRPC socket path does not match between the SDK and the daemon.
- A previous daemon instance left a stale socket file.

**Solution:**
1. Verify the daemon is running:
   ```bash
   ps aux | grep agentanycastd
   ```
2. Check the default socket path exists:
   ```bash
   ls -la ~/.agentanycast/daemon.sock
   ```
3. If a stale socket file exists from a crashed daemon, remove it:
   ```bash
   rm ~/.agentanycast/daemon.sock
   ```
4. Restart the daemon. If using a custom gRPC listen address, ensure the SDK is configured to match:
   ```bash
   agentanycastd --grpc-listen unix:///tmp/custom.sock
   ```

### Peers cannot discover each other on the same LAN

**Symptom:** Two agents on the same local network do not appear in each other's peer lists despite both running successfully.

**Possible Causes:**
- mDNS is disabled on one or both nodes.
- A firewall is blocking multicast UDP traffic (port 5353).
- The nodes are on different network subnets or VLANs.

**Solution:**
1. Verify mDNS is enabled in the daemon config (`~/.agentanycast/config.toml`):
   ```toml
   enable_mdns = true
   ```
2. Check firewall rules for multicast traffic:
   ```bash
   # macOS
   sudo pfctl -sr | grep 5353
   # Linux
   sudo iptables -L -n | grep 5353
   ```
3. Confirm both nodes are on the same subnet:
   ```bash
   ip addr show  # or ifconfig on macOS
   ```
4. Enable debug logging to observe mDNS events:
   ```bash
   agentanycastd --log-level debug 2>&1 | grep -i mdns
   ```

### NAT traversal fails -- peers behind different NATs cannot connect

**Symptom:** Two peers behind different NATs cannot establish a direct connection. Task delivery times out or fails with a "no route to peer" error.

**Possible Causes:**
- No relay server is configured as a bootstrap peer.
- The relay server is unreachable from one or both peers.
- Symmetric NAT on both sides prevents hole punching.

**Solution:**
1. Ensure both peers have a relay server configured:
   ```toml
   bootstrap_peers = ["/ip4/<relay-ip>/tcp/4001/p2p/<relay-peer-id>"]
   enable_relay_client = true
   enable_hole_punching = true
   ```
2. Verify the relay is reachable:
   ```bash
   nc -zv <relay-ip> 4001
   ```
3. Check the daemon logs for NAT type detection:
   ```bash
   agentanycastd --log-level debug 2>&1 | grep -i "nat\|autonat\|relay"
   ```
4. If both peers are behind symmetric NATs, direct hole punching will fail. Communication will be relayed through the Circuit Relay v2 server. Ensure the relay has sufficient capacity (`--max-reservations`).

### Connection drops after 2 minutes when relayed

**Symptom:** Relayed connections between peers are terminated after approximately 2 minutes.

**Possible Causes:**
- Circuit Relay v2 enforces a default connection duration limit of 2 minutes.
- This is expected behavior to prevent resource exhaustion on the relay.

**Solution:**
1. This is by design. For long-running interactions, peers should establish a direct connection via hole punching.
2. If direct connections are not possible, the application should handle reconnection. The offline queue will buffer messages during disconnections.
3. For relay operators who need longer durations, modify the relay resource limits in the relay server source code.

### Daemon fails to start with "address already in use"

**Symptom:** The daemon exits immediately with an error about the listen address being in use.

**Possible Causes:**
- Another daemon instance is already running.
- Another process is using the same port.

**Solution:**
1. Find the existing process:
   ```bash
   lsof -i :4001  # Check default libp2p port
   lsof -U | grep daemon.sock  # Check Unix socket
   ```
2. Stop the existing daemon gracefully (send SIGTERM) or kill the process:
   ```bash
   kill $(pgrep agentanycastd)
   ```
3. Use a different listen address if running multiple instances:
   ```bash
   agentanycastd --grpc-listen unix:///tmp/node2.sock
   ```

## Discovery & Routing

### Anycast fails with "no agents found for skill"

**Symptom:** `agentanycast discover <skill>` returns no results, or `send_task()` with a skill ID fails with a routing error.

**Possible Causes:**
- The target agent has not registered its skills with the relay registry.
- The agent's skill registration has expired (TTL exceeded without heartbeat).
- The sender is not connected to the same relay registry.
- DHT discovery is not enabled and no relay registry is configured.

**Solution:**
1. Verify the target agent's skills are registered. On the relay server, check the registry:
   ```bash
   curl http://<relay-ip>:9090/health | jq .registry
   ```
2. Confirm the agent has `auto_register = true` in its anycast config:
   ```toml
   [anycast]
   auto_register = true
   registry_addr = "<relay-grpc-address>:50052"
   ```
3. Ensure both sender and target use the same relay registry address.
4. Enable DHT discovery as a fallback:
   ```toml
   [anycast]
   enable_dht = true
   ```

### DHT discovery is slow or returns stale results

**Symptom:** Skill discovery via DHT takes several seconds or returns agents that are no longer available.

**Possible Causes:**
- The DHT routing table has not been fully populated.
- Cache TTL is too long, serving stale entries.
- Insufficient bootstrap peers for DHT connectivity.

**Solution:**
1. Allow more time for DHT bootstrap (typically 30-60 seconds after startup).
2. Reduce the anycast cache TTL:
   ```toml
   [anycast]
   cache_ttl = "10s"
   ```
3. Add more bootstrap peers to improve DHT connectivity:
   ```toml
   bootstrap_peers = [
     "/ip4/<relay1>/tcp/4001/p2p/<id1>",
     "/ip4/<relay2>/tcp/4001/p2p/<id2>"
   ]
   ```

### Agent cards are not exchanged between peers

**Symptom:** Connected peers do not appear with their agent card information. `list_peers()` shows peer IDs but no card metadata.

**Possible Causes:**
- The agent card has not been set before the connection was established.
- The card exchange protocol handler is not registered.

**Solution:**
1. Ensure the agent card is configured before starting the node:
   ```python
   card = AgentCard(name="My Agent", skills=[...])
   async with Node(card=card) as node:
       ...
   ```
2. Card exchange happens automatically on peer connection. If a peer connected before the card was set, manually trigger re-exchange by reconnecting.
3. Check debug logs for card exchange activity:
   ```bash
   agentanycastd --log-level debug 2>&1 | grep "card exchange"
   ```

### HTTP bridge returns 404 for agent card endpoint

**Symptom:** Requests to `http://<bridge-addr>/.well-known/agent.json` return 404.

**Possible Causes:**
- The HTTP bridge is not enabled.
- No agent card has been configured on the node.

**Solution:**
1. Enable the HTTP bridge:
   ```bash
   agentanycastd --bridge-listen :8080
   ```
2. Verify the card endpoint is accessible:
   ```bash
   curl http://localhost:8080/.well-known/agent.json
   ```

## Task Delivery

### Task times out waiting for response

**Symptom:** `handle.wait(timeout=30)` raises a timeout error. The task was sent but no response was received.

**Possible Causes:**
- The remote agent does not have a task handler registered.
- The remote agent is unreachable (behind NAT without relay).
- Network latency exceeds the timeout value.
- The remote agent's task handler is taking too long.

**Solution:**
1. Verify the remote agent has a task handler:
   ```python
   @node.on_task
   async def handle(task: IncomingTask) -> None:
       await task.complete(artifacts=[...])
   ```
2. Increase the timeout value:
   ```python
   result = await handle.wait(timeout=120)
   ```
3. Check if the task was delivered to the offline queue by examining the sender's logs:
   ```bash
   agentanycastd --log-level debug 2>&1 | grep "offline queue"
   ```

### Task stuck in "working" status

**Symptom:** A task transitions to "working" but never reaches "completed" or "failed".

**Possible Causes:**
- The task handler on the remote agent raised an unhandled exception.
- The handler is blocked on an I/O operation or deadlock.
- The remote agent crashed after acknowledging the task.

**Solution:**
1. Check the remote agent's logs for errors in the task handler.
2. Implement proper error handling in the task handler:
   ```python
   @node.on_task
   async def handle(task: IncomingTask) -> None:
       try:
           result = await process(task)
           await task.complete(artifacts=[result])
       except Exception as e:
           await task.fail(message=str(e))
   ```
3. Cancel the stuck task from the sender side:
   ```python
   await handle.cancel()
   ```

### Duplicate task delivery

**Symptom:** The same task is delivered to the handler multiple times.

**Possible Causes:**
- The acknowledgment (ACK) for the task was lost, triggering a retry.
- The sender retried after a timeout, but the original delivery succeeded.

**Solution:**
1. The daemon includes a built-in deduplication cache. Verify it is functioning by checking debug logs for "dedup" entries.
2. Implement idempotent task handlers that can safely process the same task ID multiple times.
3. If the issue persists, check network stability between the peers.

### Streaming artifacts fail mid-transfer

**Symptom:** A streaming artifact transfer starts but fails partway through with a missing chunk or timeout error.

**Possible Causes:**
- The connection was interrupted during the stream.
- The relay's data limit (128 KiB per connection) was exceeded for relayed connections.
- Memory pressure on the sender or receiver.

**Solution:**
1. For large artifacts over relayed connections, reduce chunk sizes to stay within the 128 KiB relay data limit.
2. Ensure direct connectivity between peers for large transfers.
3. Check stream metrics:
   ```bash
   curl http://localhost:9090/metrics | grep stream_chunks
   ```

## MCP Server

### MCP server fails to connect to AI assistant

**Symptom:** Claude Desktop, Cursor, or another AI assistant cannot connect to the AgentAnycast MCP server.

**Possible Causes:**
- The MCP server is not running in the correct transport mode.
- The AI assistant configuration file points to the wrong command or path.
- The daemon is not running (MCP server depends on it).

**Solution:**
1. For stdio-based assistants (Claude Desktop, Cursor), use stdio mode:
   ```bash
   agentanycast mcp  # defaults to --transport stdio
   ```
2. Verify the AI assistant's configuration file references the correct command:
   ```json
   {
     "mcpServers": {
       "agentanycast": {
         "command": "agentanycast",
         "args": ["mcp"]
       }
     }
   }
   ```
3. For remote clients, use HTTP mode:
   ```bash
   agentanycast mcp --transport http --port 8080
   ```

### MCP tools return empty results

**Symptom:** MCP tool calls execute without errors but return empty or minimal results.

**Possible Causes:**
- The underlying daemon has no peers connected.
- The agent card has no skills registered.
- The relay registry is empty.

**Solution:**
1. Check the daemon status through the MCP tools to verify connectivity.
2. Ensure the daemon is configured with relay bootstrap peers for discovery.
3. Check daemon logs for errors:
   ```bash
   agentanycastd --log-level debug 2>&1 | grep "mcp\|tool"
   ```

### MCP proxy does not expose tools from wrapped server

**Symptom:** When using `--mcp-proxy` to wrap an MCP server, no tools appear as skills.

**Possible Causes:**
- The wrapped MCP server command is incorrect or fails to start.
- The wrapped server does not list any tools.
- The proxy failed to initialize.

**Solution:**
1. Verify the wrapped command works standalone:
   ```bash
   uvx mcp-server-filesystem /tmp  # Test the wrapped server directly
   ```
2. Check daemon logs for proxy initialization:
   ```bash
   agentanycastd --mcp-proxy "uvx mcp-server-filesystem /tmp" --log-level debug
   ```
3. The logs should show "MCP proxy started" with the tool count.

## Relay Server

### Relay server runs out of reservations

**Symptom:** New peers cannot establish relay reservations. The relay logs show "max reservations reached."

**Possible Causes:**
- The relay has reached `--max-reservations` (default: 128).
- Peers are not properly cleaning up reservations on disconnect.

**Solution:**
1. Increase the reservation limit:
   ```bash
   agentanycast-relay --max-reservations 512
   ```
2. Monitor current reservations via the health endpoint:
   ```bash
   curl http://<relay-ip>:9090/health | jq .
   ```
3. Ensure clients disconnect gracefully to release reservations.

### Federation sync between relays fails

**Symptom:** Agents registered on one relay are not discoverable from another federated relay.

**Possible Causes:**
- Federation peers are not correctly configured.
- The gRPC port for the registry is unreachable between relays.
- Clock skew between relay servers causes TTL issues.

**Solution:**
1. Verify federation configuration on both relays:
   ```bash
   agentanycast-relay --federation-peers "relay2.example.com:50052"
   ```
2. Ensure bidirectional gRPC connectivity on the registry port (default: 50052):
   ```bash
   nc -zv relay2.example.com 50052
   ```
3. Check federation health via the health endpoint:
   ```bash
   curl http://<relay-ip>:9090/health | jq .federation
   ```
4. Adjust the sync interval if needed:
   ```bash
   agentanycast-relay --federation-sync-interval 5s
   ```

### Relay skill registrations expire unexpectedly

**Symptom:** Agents are periodically removed from the registry and become undiscoverable.

**Possible Causes:**
- The registration TTL is too short relative to the heartbeat interval.
- Network issues prevent heartbeat delivery.

**Solution:**
1. Increase the registry TTL:
   ```bash
   agentanycast-relay --registry-ttl 60s
   ```
2. Verify the agent is sending heartbeats by checking debug logs on both the agent and relay.
3. Ensure the agent's `auto_register` is enabled for automatic heartbeats.

## Performance

### High memory usage on the daemon

**Symptom:** The `agentanycastd` process consumes significantly more memory than expected.

**Possible Causes:**
- A large number of concurrent peer connections.
- The offline queue has accumulated many undelivered messages.
- The BoltDB store has grown due to retained task history.

**Solution:**
1. Monitor connection count:
   ```bash
   curl http://localhost:9090/metrics | grep connected_peers
   ```
2. Reduce the offline queue TTL to expire old messages sooner:
   ```toml
   offline_queue_ttl = "1h"
   ```
3. Check the BoltDB store size:
   ```bash
   ls -lh ~/.agentanycast/data/
   ```

### Task latency is higher than expected

**Symptom:** Round-trip task delivery takes significantly longer than network latency would suggest.

**Possible Causes:**
- Tasks are being routed through a relay instead of direct connections.
- Anycast resolution is slow due to cache misses.
- The gRPC Unix domain socket is under contention.

**Solution:**
1. Check whether connections are relayed or direct:
   ```bash
   curl http://localhost:9090/metrics | grep connections_by_transport
   ```
2. Verify direct connectivity between the peers by checking connection types in debug logs.
3. Increase the anycast cache TTL to reduce resolution overhead:
   ```toml
   [anycast]
   cache_ttl = "60s"
   ```
4. Enable QUIC transport for lower-latency connections:
   ```toml
   enable_quic = true
   ```

### Prometheus scraping causes CPU spikes

**Symptom:** Periodic CPU usage spikes that correlate with Prometheus scrape intervals.

**Possible Causes:**
- The scrape interval is too frequent.
- A large number of metric labels are creating high cardinality.

**Solution:**
1. Increase the Prometheus scrape interval to 30s or 60s:
   ```yaml
   scrape_configs:
     - job_name: agentanycast
       scrape_interval: 30s
   ```
2. Review custom metric labels for unnecessary cardinality.
3. If the metrics endpoint is not needed, disable it:
   ```toml
   [metrics]
   enabled = false
   ```
