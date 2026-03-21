# Frequently Asked Questions

Common questions about AgentAnycast — architecture, networking, and day-to-day usage.

## General

### Do I need a relay server for local development?

No. On a local network, agents discover each other automatically via mDNS — no relay, no configuration. A relay is only needed when agents are on different networks (e.g., across the internet or behind separate NATs).

### Can Python and TypeScript agents communicate?

Yes. Both SDKs communicate with the same Go daemon over gRPC and use the same A2A wire protocol. A Python agent and a TypeScript agent on the same machine (or across the network) can exchange tasks seamlessly.

### Is traffic encrypted through relay servers?

Yes. All agent-to-agent communication is end-to-end encrypted using the Noise_XX protocol. Relay servers forward only ciphertext — they cannot read, modify, or inspect the contents of any message. There is no plaintext transport path in the codebase.

### How do I run multiple agents on one machine?

Use the `home` parameter to give each agent its own daemon instance and data directory:

```python
async with Node(card=card_a, home="/tmp/agent-a") as agent_a:
    async with Node(card=card_b, home="/tmp/agent-b") as agent_b:
        ...
```

Each `home` directory gets its own Unix socket, key pair, and daemon process.

### What happens if the daemon crashes?

The SDK automatically restarts the daemon on the next operation (e.g., `send_task`, `serve_forever`). The daemon's state (keys, peer store) is persisted in BoltDB, so nothing is lost across restarts.

### Can I connect to agents behind different NATs?

Yes. The daemon first attempts direct hole-punching using the DCUtR protocol. If that fails (e.g., due to symmetric NAT), it automatically falls back to routing through a relay server. From your application's perspective, the connection just works — no code changes needed.

---

# Troubleshooting

Common issues and how to resolve them.

## "Connection refused" on daemon socket

The daemon is not running or the socket path is wrong.

- Verify the daemon is running: `ps aux | grep agentanycastd`
- Check the default socket path: `~/.agentanycast/daemon.sock`
- If using a custom `home`, ensure the path matches: `<home>/daemon.sock`
- The SDK normally starts the daemon automatically. If it fails, check stderr output for download or permission errors.

## "Peer not found"

The target peer is unreachable.

- Confirm the peer is online and its agent is running.
- Double-check the Peer ID string — a single wrong character will cause this error.
- If the peer is on a different network, ensure both agents are configured with the same relay address.
- Try `agentanycast discover <skill>` to verify the peer is registered in the skill registry.

## "Daemon binary not found"

The daemon binary was not downloaded or is not on the expected path.

- The SDK auto-downloads the daemon on first use. Check your internet connection.
- Set `AGENTANYCAST_DAEMON_PATH` to point to a manually downloaded binary.
- On CI environments, pre-download the binary and set the environment variable to avoid network calls during tests.

## "Permission denied on socket"

File permissions prevent access to the Unix domain socket.

- Check ownership and permissions: `ls -la ~/.agentanycast/daemon.sock`
- The socket is created by the daemon process. If you ran the daemon as root and are now running as a regular user (or vice versa), permissions will mismatch.
- Delete the stale socket file and restart: `rm ~/.agentanycast/daemon.sock`

## "NAT traversal failed"

Direct hole-punching did not succeed.

- This is common with symmetric NATs or strict corporate firewalls.
- Ensure a relay is configured — the daemon will automatically fall back to relay routing.
- If using UDP, check that your firewall allows outbound UDP traffic.
- Verify the relay server is reachable: `agentanycast status`
