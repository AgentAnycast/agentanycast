# Cross-Repo Version Coordination

AgentAnycast is split across multiple repositories, each with its own independent release cycle. This guide explains how versions are coordinated to ensure compatibility.

## Independent Versioning

Each repository follows [Semantic Versioning](https://semver.org/) independently:

| Repository | Current | Versioning |
|---|---|---|
| agentanycast-proto | v0.x.y | Protobuf API contract |
| agentanycast-node | v0.x.y | Go daemon binary |
| agentanycast-relay | v0.x.y | Relay server binary |
| agentanycast-python | v0.x.y | Python SDK (PyPI) |
| agentanycast-ts | v0.x.y | TypeScript SDK (npm) |
| agentanycast | v0.x.y | Documentation (this repo) |

Tags follow the format `v{major}.{minor}.{patch}` (e.g., `v0.3.1`).

## Proto as the Coordination Point

The `agentanycast-proto` repository is the single source of truth for all gRPC service definitions and A2A data models. Breaking changes to proto files require a coordinated release across all downstream repositories.

**Proto compatibility rules:**

- Fields are never removed or renamed — only additive changes are allowed.
- New RPC methods can be added without breaking existing clients.
- Buf's breaking change detection (`buf breaking`) enforces this in CI.

## Release Order

When a change touches the proto definitions, releases must happen in this order:

```
agentanycast-proto
       │
       ├──► agentanycast-node
       │
       ├──► agentanycast-relay
       │
       ├──► agentanycast-python
       │
       └──► agentanycast-ts
```

1. **Proto** — publish the new proto version first.
2. **Node / Relay** — update the Go module's `go.mod` replace directive, regenerate stubs, release.
3. **Python / TypeScript SDKs** — regenerate stubs from the new proto, update vendored files, release.

For changes that do not touch proto (e.g., bug fixes in the daemon or SDK-only features), repositories can release independently without coordination.

## Generated Stubs

Each SDK repository commits pre-generated protobuf/gRPC stubs so that downstream users do not need `protoc` or `buf` installed:

- **Python:** `src/agentanycast/_generated/`
- **TypeScript:** `src/generated/`
- **Go (node/relay):** `gen/go/` (via `buf generate`)

CI in each SDK repo runs a **proto freshness check** that regenerates stubs from the latest proto and verifies they match the committed versions. A mismatch fails the build, ensuring stubs are always up to date.

## Compatibility Matrix

| Proto | Node | Relay | Python SDK | TypeScript SDK |
|---|---|---|---|---|
| v0.1.x | v0.1.x | v0.1.x | v0.1.x | v0.1.x |
| v0.2.x | v0.2.x | v0.2.x | v0.2.x | v0.2.x |
| v0.3.x | v0.3.x+ | v0.3.x+ | v0.3.x+ | v0.3.x+ |

**Reading the matrix:** a proto v0.3.x release is compatible with node/relay/SDK versions at v0.3.x or later within the same minor series. Patch releases within a minor version are always backward compatible.

## Daemon–SDK Compatibility

The SDK communicates with the daemon over a Unix domain socket using gRPC. The SDK auto-downloads a compatible daemon binary based on version constraints defined in the SDK's release metadata. If you manage the daemon binary manually (via `AGENTANYCAST_DAEMON_PATH`), ensure the daemon version matches the SDK's expected proto version.

## Checking Versions

```bash
# Python SDK version
pip show agentanycast

# TypeScript SDK version
npm list agentanycast

# Daemon version
agentanycastd --version

# Relay version
agentanycast-relay --version
```
