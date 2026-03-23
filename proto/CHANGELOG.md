# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-03-17

### Added

- Protocol Buffer definitions for the AgentAnycast ecosystem
- `node_service.proto` — 13 gRPC RPCs for SDK-daemon communication
- `a2a_models.proto` — A2A data models (Task, Message, Artifact, Part, A2AEnvelope)
- `agent_card.proto` — Agent Card with P2P extensions
- `common.proto` — PeerInfo, NodeInfo, TaskStatus enum
- Buf v2 configuration with STANDARD lint and FILE-level breaking change detection
- CI pipeline with buf lint, breaking change detection, and Go build verification

[0.1.0]: https://github.com/AgentAnycast/agentanycast-proto/releases/tag/v0.1.0
