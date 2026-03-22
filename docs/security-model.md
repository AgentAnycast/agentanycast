# Security Model

AgentAnycast provides defense-in-depth security through multiple complementary layers: transport-level encryption via Noise_XX, optional envelope-level end-to-end encryption via NaCl box, cryptographic identity with W3C DIDs, skill-level access control, per-source rate limiting, and audit logging.

## Transport Encryption

### Noise_XX (libp2p)

All peer-to-peer connections are secured with the [Noise_XX](http://www.noiseprotocol.org/noise.html) handshake, enforced by libp2p. There is no plaintext transport path in the codebase.

The handshake proceeds as follows:

1. Both peers exchange **ephemeral Curve25519** keys.
2. Both peers authenticate with their **static Ed25519** keys.
3. A shared secret is derived; all subsequent traffic is encrypted with **ChaCha20-Poly1305**.

Properties:

| Property | Guarantee |
|---|---|
| Mutual authentication | Both sides prove their identity during the handshake |
| Forward secrecy | Compromising a long-term key does not compromise past sessions |
| Confidentiality | Intermediaries (including relay servers) only see ciphertext |
| Integrity | AEAD construction detects any modification in transit |

Supported transports (all Noise-encrypted):

- **TCP** -- default, always enabled
- **QUIC** -- enabled by default (`enable_quic = true`)
- **WebTransport** -- opt-in (`enable_webtransport = true`), QUIC-based, browser-compatible

### TLS (NATS Transport)

When the optional NATS transport adapter is enabled, connections to the NATS broker can use TLS:

```toml
[transport.nats]
enabled = true
broker = "tls://nats.example.com:4222"
tls_enabled = true
tls_cert_file = "/path/to/cert.pem"
tls_key_file = "/path/to/key.pem"
```

The broker URL scheme determines encryption: `nats://` for plaintext, `tls://` for TLS.

### TLS (HTTP Bridge)

When the HTTP Bridge is enabled for A2A interoperability, TLS should be configured for production:

```toml
[bridge]
enabled = true
listen = ":8443"
tls_cert = "/etc/agentanycast/cert.pem"
tls_key = "/etc/agentanycast/key.pem"
```

## End-to-End Encryption

### Envelope-Layer NaCl Box

Beyond transport-level Noise encryption, the Connection Core supports an additional envelope-level encryption layer using **NaCl box** (X25519 + XSalsa20-Poly1305). This provides true end-to-end encryption for scenarios where the payload must remain confidential even if a transport adapter or intermediary is not fully trusted.

When enabled, the encryption pipeline in `Core.Route()` works as follows:

1. The sender's Ed25519 private key is converted to an X25519 private key (SHA-512 hash of the seed, clamped per RFC 7748).
2. The recipient's Ed25519 public key is converted to an X25519 public key (birational map from the Edwards curve to the Montgomery curve).
3. A random 24-byte nonce is generated using `crypto/rand`.
4. The payload is encrypted with `nacl/box.Seal` (Diffie-Hellman shared secret + XSalsa20-Poly1305 AEAD).
5. The nonce is prepended to the ciphertext.
6. The envelope metadata field `encrypted` is set to `nacl-box`.

### Key Exchange

The recipient's public key is communicated via the envelope metadata field `recipient_pubkey` (hex-encoded Ed25519 public key). When this field is present and the Core has a local private key set (`Core.SetEncryptionKey()`), encryption is applied automatically.

Decryption reverses the process: the first 24 bytes are extracted as the nonce, and `nacl/box.Open` is called with the converted keys.

### Encryption vs. Transport Security

| Layer | Scope | Algorithm | What it protects |
|---|---|---|---|
| **Transport (Noise_XX)** | Per-connection | ChaCha20-Poly1305 | All traffic on a single libp2p connection |
| **Envelope (NaCl box)** | Per-message | XSalsa20-Poly1305 | Individual envelope payloads, end-to-end |

Both layers can be active simultaneously. The envelope-layer encryption is especially valuable when messages traverse relay servers or NATS brokers.

## Identity & Authentication

### Ed25519 Key Pair

Every node generates an **Ed25519 key pair** on first start. The private key is persisted at `~/.agentanycast/key` (file permissions `0600`, directory permissions `0700`). The public key derives the node's **Peer ID** (a Base58-encoded multihash of the public key), which serves as its cryptographic identity.

- No certificate authorities or DNS required -- identity is self-sovereign
- Peer IDs are stable across restarts as long as the key file is preserved
- Format: `12D3KooW...` (Base58-encoded multihash)

### did:key

The primary DID method. Derived directly from the Ed25519 public key:

```
did:key:z6Mk...
```

The SDK provides bidirectional conversion: `peer_id_to_did_key()` / `did_key_to_peer_id()`. The `did:key` identifier is used as the source identity in ACL rules and rate limiting.

### did:web

Web-based DID resolution for agents with a web presence:

```toml
[identity]
did_web = "did:web:example.com:agents:myagent"
```

When configured, the daemon serves a DID Document at the corresponding well-known path via the HTTP Bridge. Resolution follows the [did:web specification](https://w3c-ccg.github.io/did-method-web/).

### did:dns

DNS-based DID resolution using TXT records:

```toml
[identity]
did_dns_domain = "example.com"
```

The domain's DNS TXT records at `_did.<domain>` contain `did:key` URIs that map to the agent's identity.

### W3C Verifiable Credentials

Agent Cards can carry **Verifiable Credentials** (W3C VC Data Model v2.0) for capability attestation. An agent can issue a self-signed credential attesting its skills:

- Credential type: `AgentCapabilityCredential`
- Proof suite: `Ed25519Signature2020`
- Canonical JSON serialization with sorted keys for deterministic signing
- Issuer DID resolution supports `did:key` (default) and custom `DIDResolver` implementations

Verification checks the Ed25519 signature against the issuer's public key extracted from their DID.

**Known limitations:**

- No expiration checking on credentials
- No revocation list support
- Default resolver only handles `did:key` issuers (custom resolvers can support `did:web` and others)
- Canonical JSON may differ from JSON-LD canonicalization (URDNA2015) used by some VC implementations

## Access Control (ACL)

The ACL system enforces **skill-level access control** based on the source identity (DID or Peer ID) of incoming envelopes. Rules are evaluated in the `Core.Route()` pipeline before a message is dispatched.

### Behavior

- Rules are evaluated **in order** -- the first matching rule wins.
- If **no rules are configured**, all access is allowed (open by default).
- If rules are configured but **none match**, access is **denied** (default-deny when rules exist).
- Source identity is resolved as: `DIDKey` if available, otherwise `PeerID`.

### Configuration

ACL rules are defined in the `[policy]` section of the TOML config:

```toml
[policy]

[[policy.acl]]
source = "did:web:trusted.example.com:*"
skill = "*"
allow = true

[[policy.acl]]
source = "did:key:z6MkPartner..."
skill = "translate"
allow = true

[[policy.acl]]
source = "*"
skill = "internal-*"
allow = false

[[policy.acl]]
source = "*"
skill = "*"
allow = true
```

### Pattern Matching

The `source` and `skill` fields support glob patterns:

| Pattern | Meaning |
|---|---|
| `*` | Matches everything |
| `did:web:trusted.com:*` | Matches any DID under `trusted.com` |
| `did:key:z6Mk...` | Exact match on a specific DID |
| `internal-*` | Matches skills prefixed with `internal-` |

Under the hood, prefix patterns ending in `:*` use `strings.HasPrefix`, and other patterns use `filepath.Match` glob semantics.

### Rule Examples

**Allow all access (no rules):**

```toml
# Empty [policy] section or omit entirely
[policy]
```

**Allowlist mode (deny by default):**

```toml
[policy]
[[policy.acl]]
source = "did:web:partner.com:*"
skill = "*"
allow = true
# All other source/skill combinations are denied (default-deny)
```

**Block specific skills:**

```toml
[policy]
[[policy.acl]]
source = "*"
skill = "admin-*"
allow = false

[[policy.acl]]
source = "*"
skill = "*"
allow = true
```

## Rate Limiting

Per-source rate limiting uses a **token bucket algorithm** (via `golang.org/x/time/rate`). Limiters are lazily created per source identity and evicted after 10 minutes of inactivity.

### Configuration

```toml
[policy.rate_limit]
default_rps = 100   # Requests per second (default: 100, burst = RPS)

[[policy.rate_limit.overrides]]
source = "did:key:z6MkHighVolume..."
rps = 500

[[policy.rate_limit.overrides]]
source = "did:web:untrusted.example.com:agent1"
rps = 10
```

### Behavior

- **Default:** 100 requests per second per source identity
- **Burst:** equals the RPS value (token bucket capacity)
- **Unknown sources** (no DID or Peer ID) are always allowed
- **Exceeded limits** return an error and are logged at INFO level
- Rate limit entries are **evicted** after 10 minutes without activity (cleanup runs every 5 minutes)

Rate limiting is checked in `Core.Route()` after ACL but before dispatch.

## Audit Logging

The audit logger writes security events as **JSON Lines** to a file. Each event records the access decision made by the Core pipeline.

### Configuration

```toml
[policy]
audit_log_path = "/var/log/agentanycast/audit.jsonl"
```

When the path is empty or omitted, audit logging is disabled. A nil `AuditLogger` is safe to use -- all methods are no-ops.

### Event Format

Each line is a JSON object with the following fields:

```json
{
  "timestamp": "2026-03-21T12:00:00.123456789Z",
  "source": "did:key:z6MkSender...",
  "target": "12D3KooWRecipient...",
  "skill": "translate",
  "action": "allow",
  "transport": "libp2p",
  "envelope_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

The `action` field is one of:

| Action | Meaning |
|---|---|
| `allow` | ACL and rate limit both passed |
| `deny` | ACL rule denied the request |
| `rate_limit` | Rate limit exceeded for the source |

### Log Rotation

The audit logger appends to the configured file. Use external log rotation tools (e.g., `logrotate`) to manage file size. The file is opened with `O_APPEND` mode.

## Threat Model

### In Scope

AgentAnycast's security model addresses the following threats:

- **Eavesdropping on agent traffic** -- mitigated by Noise_XX transport encryption and optional NaCl box envelope encryption
- **Man-in-the-middle attacks** -- mitigated by mutual authentication during the Noise_XX handshake (both peers prove their identity)
- **Replay attacks** -- mitigated by unique nonces in both Noise_XX sessions and NaCl box envelopes
- **Unauthorized skill invocation** -- mitigated by ACL rules with default-deny semantics
- **Denial of service from individual sources** -- mitigated by per-source rate limiting with token bucket
- **Identity spoofing** -- mitigated by cryptographic Peer IDs derived from Ed25519 public keys
- **Relay server reading traffic** -- mitigated by Noise_XX encryption; relay is a zero-knowledge forwarder

### Relay Trust Model

The relay server is designed as a **zero-knowledge forwarder**:

- All traffic is end-to-end encrypted with Noise_XX before reaching the relay
- The relay cannot decrypt, inspect, or modify message content
- The relay only sees: source Peer ID, destination Peer ID, and encrypted bytes
- The skill registry stores only metadata (skill IDs, tags, Peer IDs) -- no message content
- Resource limits prevent abuse: max 2 minutes and 128 KiB per relayed connection, with per-peer and per-IP caps

You can run your own relay server, eliminating any reliance on third-party infrastructure.

### Relay Resource Limits

| Limit | Value | Purpose |
|---|---|---|
| Duration | 2 min | Max duration of a single relayed connection |
| Data | 128 KiB | Max data per relayed connection |
| Reservations | 128 | Global max concurrent reservations |
| Circuits | 16 | Max concurrent active relay circuits |
| Per Peer | 4 | Max reservations per Peer ID |
| Per IP | 8 | Max reservations per IP address |

### Known Limitations

- **No credential expiration checking** -- Verifiable Credentials without an `expirationDate` are accepted indefinitely
- **No revocation support** -- there is no credential status or revocation list mechanism
- **ACL is local only** -- access control rules are per-node; there is no distributed policy synchronization
- **Rate limiting is in-memory** -- rate limit state is not persisted across daemon restarts
- **mDNS broadcasts presence** -- agents on a LAN broadcast their presence via mDNS (disable with `enable_mdns = false` if not needed)
- **gRPC socket is not authenticated** -- the Unix domain socket between SDK and daemon relies on OS-level file permissions for access control
- **NaCl box key exchange is out-of-band** -- the recipient's public key must be known in advance (communicated via envelope metadata)

## Security Checklist

### Identity

- [ ] Ensure identity key file (`~/.agentanycast/key`) has `600` permissions
- [ ] Back up identity keys for persistent agents
- [ ] Never share keys between agents
- [ ] Rotate keys by deleting the key file and restarting (generates a new Peer ID)

### Network

- [ ] Verify gRPC listens on Unix socket or localhost only (default)
- [ ] Never expose the gRPC port to the public network
- [ ] Disable mDNS if LAN discovery is not needed (`enable_mdns = false`)
- [ ] Use relay-only mode for controlled connectivity in sensitive environments

### HTTP Bridge

- [ ] Enable TLS with valid certificates (`tls_cert` + `tls_key`)
- [ ] Restrict CORS origins (`cors_origins`) to known domains
- [ ] Place behind a reverse proxy for additional rate limiting and DDoS protection

### NATS Transport

- [ ] Use `tls://` broker URLs in production
- [ ] Configure `tls_cert_file` and `tls_key_file` for mutual TLS
- [ ] Use `auth_user` and `auth_pass` for NATS authentication

### Relay Server

- [ ] Use `--key` with a persistent file path (stable Peer ID across restarts)
- [ ] Open only required ports: 4001 TCP+UDP (relay), 50052 TCP (registry)
- [ ] Monitor logs for resource limit hits
- [ ] Deploy on infrastructure you control

### Access Control

- [ ] Define ACL rules for production agents (default-deny when rules exist)
- [ ] Configure per-source rate limits for known high-volume or untrusted clients
- [ ] Enable audit logging to a persistent file path
- [ ] Set up log rotation for the audit log

### Logging

- [ ] Set log level to `info` or `warn` for production
- [ ] Set log format to `json` for structured logging and ingestion
- [ ] Monitor for `acl: access denied` and `rate limit exceeded` log entries
