# Contributing

Thank you for your interest in contributing to AgentAnycast!

Please see the [Contributing Guide](https://github.com/AgentAnycast/agentanycast/blob/main/CONTRIBUTING.md) in the main repository for guidelines on:

- Development workflow (fork → branch → PR → squash merge)
- Coding standards and commit message conventions
- Cross-repository changes
- CLA requirements

## Proto-Specific Guidelines

- All changes must pass `buf lint` (STANDARD rules)
- Never remove or rename existing fields — only additive changes
- Run `buf breaking --against '.git#branch=main'` before submitting
- Update downstream repos (agentanycast-node, agentanycast-python, agentanycast-ts) if adding new RPCs

## Required CI Checks

All of the following must pass before a PR can be merged:

- **buf-lint** — Protobuf linting with STANDARD rules
- **buf-breaking** — Backward compatibility check against `main`
- **go-build** — Verify generated Go code compiles
