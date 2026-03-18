# Contributing to AgentAnycast

Thank you for your interest in contributing to AgentAnycast! This document provides guidelines for contributing to any repository under the `@AgentAnycast` organization.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

AgentAnycast is organized as multiple repositories. Choose the one that matches your contribution:

| I want to... | Repository | Language | Setup |
|---|---|---|---|
| Fix/improve the P2P daemon | [agentanycast-node](https://github.com/AgentAnycast/agentanycast-node) | Go 1.22+ | `make build && make test` |
| Fix/improve the Python SDK | [agentanycast-python](https://github.com/AgentAnycast/agentanycast-python) | Python 3.10+ | `pip install -e ".[dev]" && pytest` |
| Fix/improve Protobuf definitions | [agentanycast-proto](https://github.com/AgentAnycast/agentanycast-proto) | Protobuf | `buf lint && buf generate` |
| Fix/improve the Relay server | [agentanycast-relay](https://github.com/AgentAnycast/agentanycast-relay) | Go 1.22+ | `make build && make test` |
| Improve docs or report bugs | [agentanycast](https://github.com/AgentAnycast/agentanycast) | Markdown | — |

## Contribution Workflow

1. **Check existing issues** — Look for open issues or discussions before starting work.
2. **Open an issue first** — For non-trivial changes, open an issue in the [main repo](https://github.com/AgentAnycast/agentanycast/issues) to discuss your approach.
3. **Fork & branch** — Fork the relevant repository and create a feature branch.
4. **Make changes** — Follow the coding standards for that repository (see below).
5. **Test** — Ensure all existing tests pass and add tests for new functionality.
6. **Submit a PR** — Open a pull request with a clear description of your changes.

## Contributor License Agreement (CLA)

All repositories under the AgentAnycast organization require a **Contributor License Agreement (CLA)**. A CLA bot will automatically ask you to sign the CLA when you open your first pull request. You only need to sign once — it covers all repositories in the organization.

The CLA ensures the project maintainers can continue to distribute, relicense, and offer all components under their current or future license terms. You can read the full CLA at [CLA.md](CLA.md).

## Coding Standards

### Go (node, relay)

- Follow [Effective Go](https://go.dev/doc/effective_go) conventions
- Run `golangci-lint run` before submitting
- Write table-driven tests
- Use structured logging (`slog`)

### Python (python SDK)

- Format with `ruff format`
- Lint with `ruff check`
- Type-check with `mypy`
- Test with `pytest`
- Use `async/await` for all I/O operations
- Provide type hints for all public APIs

### Protobuf (proto)

- Run `buf lint` before submitting
- Never break backward compatibility — only add fields, never remove or rename
- Run `buf breaking` to verify

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add agent discovery via DHT
fix: handle reconnection after relay timeout
docs: update getting started guide
test: add NAT traversal integration tests
refactor: extract task state machine into separate module
```

## Cross-Repository Changes

Some changes span multiple repositories (e.g., adding a new RPC method):

1. Start with `agentanycast-proto` — define the new interface
2. Update `agentanycast-node` — implement the server side
3. Update `agentanycast-python` — implement the client side

Open linked PRs in each repository and reference them in your descriptions.

## Reporting Security Issues

Please do **NOT** open a public issue for security vulnerabilities. See [SECURITY.md](SECURITY.md) for responsible disclosure instructions.

## Questions?

- Open a [Discussion](https://github.com/AgentAnycast/agentanycast/discussions) for general questions
- Join the conversation in existing issues
