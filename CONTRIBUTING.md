# Contributing to AgentAnycast

Thank you for your interest in contributing to AgentAnycast! This document provides guidelines for contributing to any repository under the `@AgentAnycast` organization.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

AgentAnycast is organized as multiple repositories. Choose the one that matches your contribution:

| I want to... | Repository | Language | Setup |
|---|---|---|---|
| Fix/improve the P2P daemon | [agentanycast-node](https://github.com/AgentAnycast/agentanycast-node) | Go 1.25+ | `make build && make test` |
| Fix/improve the Python SDK | [agentanycast-python](https://github.com/AgentAnycast/agentanycast-python) | Python 3.10+ | `pip install -e ".[dev]" && pytest` |
| Fix/improve the TypeScript SDK | [agentanycast-ts](https://github.com/AgentAnycast/agentanycast-ts) | TypeScript | `npm install && npm test` |
| Fix/improve Protobuf definitions | [agentanycast-proto](https://github.com/AgentAnycast/agentanycast-proto) | Protobuf | `buf lint && buf generate` |
| Fix/improve the Relay server | [agentanycast-relay](https://github.com/AgentAnycast/agentanycast-relay) | Go 1.25+ | `go build ./cmd/relay && go test ./...` |
| Improve docs or report bugs | [agentanycast](https://github.com/AgentAnycast/agentanycast) | Markdown | — |

## Development Workflow

The `main` branch is protected across all repositories. All changes must go through a pull request.

### Step by Step

1. **Check existing issues** — Look for open issues or discussions before starting work.
2. **Open an issue first** — For non-trivial changes, open an issue in the [main repo](https://github.com/AgentAnycast/agentanycast/issues) to discuss your approach.
3. **Fork & branch** — Fork the relevant repository and create a feature branch from `main`:
   ```bash
   git checkout -b feat/my-feature
   ```
   Use a descriptive branch name with a prefix: `feat/`, `fix/`, `docs/`, `test/`, `chore/`.
4. **Make changes** — Follow the coding standards for that repository (see below).
5. **Test** — Ensure all existing tests pass and add tests for new functionality.
6. **Submit a PR** — Open a pull request against `main` with a clear description of your changes.

### Pull Request Requirements

- **CI must pass** — Every repository has automated checks (lint, test, build) that must all pass before merging. See each repository's README for the specific checks.
- **Squash merge** — All PRs are squash-merged to keep the `main` branch history clean and linear. Write a clear PR title — it becomes the commit message.
- **Keep PRs focused** — One logical change per PR. If you're fixing a bug and also want to refactor nearby code, submit separate PRs.

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

### TypeScript (ts SDK)

- Build with `npm run build`
- Test with `npm test` (Vitest)
- Lint with `npm run lint`
- All public APIs must have JSDoc comments and TypeScript type annotations
- Do not modify files under `src/generated/` — those are auto-generated from proto

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
3. Update `agentanycast-python` and/or `agentanycast-ts` — implement the client side

Open linked PRs in each repository and reference them in your descriptions.

## Reporting Security Issues

Please do **NOT** open a public issue for security vulnerabilities. See [SECURITY.md](SECURITY.md) for responsible disclosure instructions.

## Questions?

- Open a [Discussion](https://github.com/AgentAnycast/agentanycast/discussions) for general questions
- Join the conversation in existing issues
