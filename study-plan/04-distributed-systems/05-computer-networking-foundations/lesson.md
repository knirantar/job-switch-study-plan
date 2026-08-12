# Computer Networking from Scratch

Parent subject: `04-distributed-systems`
Study time: 3–4 hours
Target: senior backend / AI platform / MLOps interviews

## 1. FOUNDATIONS

### Why networks exist and why they fail differently

A computer network lets independent machines exchange data over links. This makes shared services, remote databases, cloud platforms, and distributed computation possible. It also replaces simple function-call assumptions with delay, loss, duplication, reordering, corruption detection, congestion, incompatible endpoints, and independent failure.

The Internet grew from packet-switching research and ARPANET. Instead of reserving a dedicated circuit for one conversation, **packet switching** divides data into bounded units that share links and are forwarded independently. This uses capacity efficiently and routes around some failures, but delivery time and success are no longer guaranteed by the network layer.

A backend call that looks like `paymentClient.authorize()` may perform name resolution, routing, connection establishment, TLS authentication, HTTP serialization, server queueing, application work, and response transfer. Each stage has distinct errors and time. Senior engineers decompose this path rather than describing “the network” as a single black box.

### Layers and encapsulation

Layering gives each protocol a bounded responsibility. The common five-layer teaching model is:

1. **Application:** HTTP, DNS, PostgreSQL protocol, Kafka protocol.
2. **Transport:** TCP or UDP between processes/ports.
3. **Network:** IP addressing and routing between hosts/networks.
4. **Link:** frames on a local link, such as Ethernet or Wi-Fi.
5. **Physical:** signals over copper, fiber, or radio.

The OSI seven-layer model is useful vocabulary but Internet implementations do not map perfectly. **Encapsulation** wraps application bytes in transport segments/datagrams, IP packets, and link frames; receivers remove headers in reverse. Each layer can identify, validate, fragment/segment, route, retransmit, or multiplex according to its contract.

### Addresses, ports, sockets, and routes

An **IP address** identifies an interface/location for network-layer routing. IPv4 has 32 bits; IPv6 has 128. A **prefix** such as `10.20.0.0/16` fixes the first 16 IPv4 bits, leaving 16 host bits and 65,536 total addresses (platforms reserve some). A **subnet** is an address range associated with routing/policy.

A **port** is a 16-bit transport endpoint number. Servers conventionally listen on known ports: HTTP 80, HTTPS 443, PostgreSQL 5432, DNS 53. A **socket** is an operating-system communication endpoint. A TCP flow is identified by protocol plus source/destination IP and port. Thousands of clients can reach one server port because their source tuples differ.

A **router** forwards packets using a routing table and the most specific matching prefix. A default route covers destinations without a more specific route. **NAT** rewrites addresses/ports, commonly letting private clients share public egress. NAT is not a firewall policy, although stateful gateways often combine both.

### DNS

The Domain Name System maps hierarchical names to records. A client resolver may consult local cache, recursive resolver, and authoritative name servers. `A` maps to IPv4; `AAAA` to IPv6; `CNAME` aliases one name; `MX` describes mail exchange; `TXT` carries text policies; `SRV` can describe service endpoints.

DNS records have a **TTL** suggesting cache duration. A 300-second TTL does not mean every client changes exactly five minutes after an update: caches may have old records, applications may cache independently, connections outlive DNS, and negative answers have caching. DNS gives eventual name-to-record propagation, not instant traffic migration.

### TCP and UDP

TCP provides an ordered reliable byte stream between endpoints. A three-way handshake exchanges SYN, SYN-ACK, and ACK to establish sequence state. TCP detects loss and retransmits, controls receiver flow, and responds to congestion. It does not preserve application message boundaries: two writes may be read together or partially. Protocols need framing, such as content length or length prefixes.

UDP sends independent datagrams without connection setup or built-in delivery/order guarantees. It has lower protocol machinery and preserves datagram boundaries. Applications such as DNS and modern transports like QUIC build needed behavior above it. “UDP is faster” is incomplete; workload, loss, handshake, congestion, implementation, and reliability requirements decide.

TCP reliability can increase latency. If a packet is lost, later bytes wait for retransmission in that connection's ordered stream—**head-of-line blocking**. Multiple HTTP/2 streams share one TCP connection and can be affected by transport loss. QUIC implements streams over UDP so loss in one stream need not block delivery in another, while retaining congestion control and security.

### TLS

TLS protects application data in transit with confidentiality, integrity, and peer authentication based on configured trust. During a handshake, parties negotiate parameters, authenticate the server with a certificate chain (and optionally client identity), establish shared secrets, and derive symmetric session keys. Symmetric encryption handles bulk data efficiently after asymmetric/key-exchange operations establish trust.

A certificate binds names to a public key under a certificate authority chain and validity period. A client must verify the chain, hostname, time validity, and revocation/status according to its stack/policy. Encryption without identity verification is vulnerable to an active intermediary. TLS does not protect compromised endpoints or data after decryption.

### HTTP

HTTP is an application request/response protocol. A request has method, target, headers, and optional body. A response has status, headers, and optional body. Common method semantics:

- GET retrieves a representation and should be safe/idempotent.
- POST submits processing and is not inherently idempotent.
- PUT replaces a target representation and is idempotent by intent.
- PATCH applies a partial change; idempotency depends on patch semantics.
- DELETE requests removal and is idempotent in desired-state semantics, though responses/audits can differ.

Status classes: 2xx success, 3xx redirection, 4xx client/request issue, 5xx server failure. `429 Too Many Requests` signals rate limiting; `503 Service Unavailable` often indicates temporary inability. Retry behavior cannot be inferred solely from class: method safety, idempotency key, `Retry-After`, deadlines, and failure point matter.

HTTP/1.1 supports persistent connections but has ordering/pipelining limits. HTTP/2 multiplexes streams on one connection and compresses headers. HTTP/3 maps HTTP over QUIC. Protocol version does not fix slow application/database work.

### Proxies and load balancers

A **forward proxy** represents clients to servers. A **reverse proxy** represents servers to clients, handling routing, TLS, authentication, compression, and policy. A **load balancer** distributes traffic across targets using algorithms such as round robin, least connections, hashing, or measured load and excludes unhealthy targets.

Layer 4 load balancing routes transport flows without understanding HTTP semantics. Layer 7 routing can use host, path, headers, or methods but performs more protocol work and terminates or proxies connections. Health checks must represent ability to serve safely; a process-alive check can route traffic to an instance whose database pool is exhausted.

### Latency, bandwidth, throughput, and queueing

**Latency** is time for an operation. **Round-trip time** (RTT) is time for a message to travel to a peer and response/acknowledgment return. **Bandwidth** is link capacity, e.g. 1 Gbit/s. **Throughput** is useful work achieved per time and is limited by bottlenecks and overhead. A 100 MB payload is 800 megabits; at an ideal 1 Gbit/s serialization alone is 0.8 seconds, before headers, contention, disk, and processing.

Distance imposes a floor. Light in fiber travels roughly 200,000 km/s. A 10,000 km one-way path has a theoretical propagation time near 50 ms, so physical RTT floor is near 100 ms before routing/equipment. No code optimization removes geography.

Little's Law in a stable system states concurrency `L = arrival rate λ × average time W`. At 2,000 requests/s and 100 ms average, about 200 requests are in flight. At the same arrival rate and 500 ms latency, 1,000 are in flight, pressuring connections, memory, and queues.

## 2. CORE MECHANICS

### 2.1 Calculate CIDR ranges

For `10.20.32.0/20`, the mask has 20 fixed bits and 12 host bits: 4,096 total addresses. In the third octet, a /20 block spans 16 values, so range is `10.20.32.0` through `10.20.47.255`. Cloud providers reserve addresses, so usable count is platform-specific and below 4,096.

To check containment, mask both address and network to prefix bits. Overlapping CIDRs break unambiguous private routing and complicate peering/VPN connectivity.

### 2.2 Trace a request

For `https://api.example.com/claims`:

1. Parse scheme HTTPS, host, default port 443, path.
2. Resolve host through DNS unless cached.
3. Choose an address and route/source interface.
4. Establish transport (TCP handshake for HTTP/1.1 or 2; QUIC for HTTP/3).
5. Complete TLS handshake or resume a session.
6. Send HTTP request bytes.
7. Reverse proxy/load balancer accepts and selects a healthy backend.
8. Backend queues, authenticates, performs work, returns response.
9. Client reads framed response and may reuse connection.

Each stage consumes deadline. “Connection timeout” should cover establishment; “read timeout” is not a complete end-to-end deadline and may reset per read in some APIs.

### 2.3 DNS failure analysis

Test layers separately: is the name syntactically correct; what resolver is configured; does lookup return A/AAAA/CNAME; is the answer authoritative/cached; can the resolved IP/port be reached; does TLS certificate match the requested hostname? Using a raw IP can bypass DNS but then fail TLS name verification and virtual hosting, so it is a diagnostic, not a production fix.

### 2.4 TCP behavior and framing

Suppose sender writes a four-byte length `00000100` followed by 256 payload bytes. Receiver must loop until it has read four length bytes, validate length against a maximum, then loop until 256 bytes arrive. A single `read` is allowed to return fewer bytes. Without maximum validation, a malicious length can force huge allocation.

TCP's orderly close uses FIN; reset signals abrupt termination. A timeout is ambiguous: the server may have completed work but the response was lost. This is why retries of writes need idempotency.

### 2.5 TLS diagnosis

Differentiate:

- unknown CA: trust chain missing/untrusted;
- hostname mismatch: certificate names do not include requested host;
- expired/not-yet-valid: clock/certificate lifecycle issue;
- protocol/cipher mismatch: incompatible security settings;
- client-certificate failure: mTLS identity not supplied/accepted.

Never “fix” production by disabling verification. Correct names, trust bundles, rotation, clock, and endpoint configuration.

### 2.6 HTTP contracts

Example request:

```http
POST /v1/payments HTTP/1.1
Host: payments.example
Content-Type: application/json
Idempotency-Key: 4b10cc4e-5fa2-4f42-a274-7e1d24aaf982

{"accountId":"A-19","amountPaise":129900,"currency":"INR"}
```

If processing succeeds but the response is lost, retrying with the same key should return/derive the same logical outcome rather than create a second payment. The server must atomically associate the key with request identity and outcome; a header alone does nothing.

### 2.7 Load-balancing arithmetic

At 12,000 requests/s across 12 equally capable healthy instances, mean is 1,000 requests/s each. Losing three increases mean to 1,333/s, a 33.3% increase. If safe instance capacity is 1,150/s, the service overloads during failure despite appearing 75% utilized before it. Capacity planning must include failure headroom.

Round robin assumes comparable cost. GPU inference requests with varying token lengths may need queue-aware or least-loaded routing, admission control, and per-tenant fairness.

### 2.8 Deadlines and latency budgets

For a 500 ms API SLO, reserve perhaps 40 ms ingress/auth, 60 ms application compute, 250 ms downstream/database, 50 ms network variance, and 100 ms safety/response. These are illustrative and must be based on traces. A downstream timeout of 2 seconds violates the caller budget. Propagate an absolute deadline or remaining budget and leave time to handle failure.

### 2.9 Bandwidth-delay product

On a 1 Gbit/s path with 100 ms RTT, bandwidth-delay product is `1e9 bits/s × 0.1s = 100 million bits = 12.5 MB`. Roughly that much unacknowledged data may be needed to fill the path. Small windows or application stop-and-wait behavior cannot use full bandwidth on a high-latency link.

### 2.10 Practical diagnostic sequence

Start from the failing client environment:

1. Confirm exact endpoint/config and time.
2. Resolve DNS.
3. Confirm routing/firewall/port reachability.
4. Inspect TCP connect latency/resets.
5. Validate TLS chain/name/version.
6. Send minimal protocol request with safe credentials.
7. Correlate load-balancer and server logs/traces by request ID.
8. Measure stage durations and compare healthy baseline.

Tools include `dig`/`nslookup`, `ip route`/`route`, `ss`/`netstat`, `curl -v`, `openssl s_client`, packet capture when authorized, cloud flow logs, and distributed traces. Avoid exposing tokens in commands or captures.

## 3. WORKED PROBLEMS

### Problem 1 — CIDR capacity (easy)

How many total IPv4 addresses are in `/24` and `/20`?

**Solution.** `/24` leaves 8 bits: `2^8=256`. `/20` leaves 12: `2^12=4096`. Usable cloud addresses are lower due to provider reservation.

**Trap:** subtracting two universally; cloud reservation rules vary.

### Problem 2 — Port tuple (easy)

How can 10,000 clients connect to server `203.0.113.7:443`?

**Solution.** Flows differ by source IP and ephemeral source port (and protocol). Destination port need not be unique per client.

**Trap:** assuming one listener permits one connection.

### Problem 3 — Transfer floor (easy)

Ideal serialization time for 250 MB over 500 Mbit/s?

**Solution.** 250 MB is about 2,000 megabits using decimal units; divided by 500 Mbit/s = 4 seconds, before overhead/competition/storage.

**Trap:** dividing bytes by bits without multiplying by eight.

### Problem 4 — DNS migration (medium)

TTL is 300 seconds. Can old server be terminated exactly five minutes after record update?

**Solution.** Not safely. Existing cache ages differ, application caches and persistent connections may outlive TTL, negative caching/resolver behavior varies, and propagation/update timing matters. Run both targets during a measured drain window and observe traffic.

**Trap:** interpreting TTL as a guaranteed global cutover timer.

### Problem 5 — Lost response (medium)

A POST payment times out after server commit. Should client blindly retry?

**Solution.** Outcome is unknown. Retry only under an end-to-end idempotency contract using the same key/request fingerprint, or query status. Blind retry risks duplicate payment.

**Trap:** treating timeout as proof no server work occurred.

### Problem 6 — Load balancer health (medium)

Process `/health` returns 200 while its DB pool is exhausted. What is wrong?

**Solution.** Liveness only proves process loop. Readiness should reflect whether the instance can safely accept traffic, using bounded dependency/overload signals without causing a health-check storm. Also use admission control; removing every instance during a shared DB incident can worsen outage.

**Trap:** one endpoint used identically for liveness and readiness.

### Problem 7 — Little's Law (hard)

At 5,000 requests/s and 240 ms average end-to-end time, estimate in-flight requests.

**Solution.** `L=5000×0.240=1200`. If latency doubles under saturation with unchanged arrival rate, in-flight work doubles, a feedback warning.

**Trap:** using milliseconds as seconds and getting 1,200,000.

### Problem 8 — Failure capacity (hard)

20 instances carry 16,000 rps; each safely handles 1,000. Can five fail safely?

**Solution.** Normal 800 each. After five fail, 16,000/15≈1,066.7, exceeding safe capacity. Need at least 16 healthy just for mean load, plus imbalance/headroom; five-failure tolerance requires higher per-instance capacity or more instances/admission.

**Trap:** claiming 20% normal headroom covers 25% instance loss.

### Problem 9 — TLS “fix” (hard)

Hostname verification fails after switching to an IP address. What should happen?

**Solution.** Use the intended DNS name whose certificate SAN matches, correct DNS/routing, or issue a certificate appropriate to the authenticated name. Preserve SNI and verification. Do not disable checks or trust all certificates.

**Trap:** prioritizing connectivity over endpoint identity.

## 4. REAL-WORLD / APPLIED CONTEXT

### Kubernetes service networking

A Kubernetes Service gives a stable virtual endpoint while pods change. DNS resolves service names; kube-proxy or dataplane mechanisms route to endpoints; readiness controls eligible endpoints. Application connection pools may keep connections to terminating pods, so graceful termination, draining, readiness changes, and client retry semantics must align.

### Azure private endpoints

Azure Private Link can expose a managed service through a private IP in a virtual network. Correct operation depends on private DNS mapping the public service name to the private endpoint, route reachability, network policy, and TLS continuing to verify the service hostname. Replacing names with IPs breaks this composition.

### gRPC and HTTP/2

gRPC commonly uses HTTP/2 multiplexing and Protocol Buffers. Many logical RPC streams can share a TCP connection, reducing connection overhead, but one unhealthy/saturated connection, load-balancer connection pinning, flow control, or TCP loss can affect traffic distribution. Keepalive and retries require careful policy.

## 5. COMPARISON TABLE

| Mechanism | Setup | Delivery/order | Good for | Main limitation |
|---|---|---|---|---|
| TCP | Handshake | Reliable ordered byte stream | HTTP/1.1, HTTP/2, DB protocols | HOL, no message boundaries |
| UDP | No transport handshake | Best-effort datagrams | DNS, media, custom/QUIC substrate | App supplies reliability/security as needed |
| HTTP/1.1 | Usually TCP+TLS | Request/response; persistent | Universal APIs | Limited multiplexing |
| HTTP/2 | TCP+TLS common | Multiplexed streams | gRPC, many concurrent requests | TCP connection-level HOL on loss |
| HTTP/3 | QUIC over UDP | Multiplexed independent streams | Lossy/mobile modern web | Deployment/tooling maturity varies |
| L4 load balancer | Transport tuple | Flow-based | High-throughput generic TCP/UDP | No HTTP content routing |
| L7 proxy | Parses app protocol | Request/stream-aware | Path/auth/header routing | More CPU/latency/termination complexity |
| Bandwidth | bits per second | Capacity | Bulk transfer | Does not imply low latency |
| Latency | time | Delay | Interactive response | Does not imply high throughput |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Ping works, therefore application works.** ICMP success does not prove DNS, port, TLS, auth, or application health.
2. **TCP sends messages.** It sends an ordered byte stream; applications frame messages.
3. **TCP timeout means server did nothing.** Outcome may be unknown after request delivery.
4. **UDP is simply unreliable TCP.** It is datagram transport used to build different semantics, including QUIC.
5. **DNS TTL guarantees cutover.** Caches and existing connections complicate it.
6. **NAT is a security policy.** It rewrites addressing; explicit filtering/identity is still required.
7. **TLS encryption is enough.** Peer identity verification is essential.
8. **More load-balanced targets guarantee resilience.** Shared dependencies and failure headroom determine it.
9. **Average latency describes users.** Tail percentiles and queueing matter.
10. **1 Gbit/s means 1 GB/s.** One byte is eight bits; ideal is 125 MB/s before overhead.
11. **Readiness should fail whenever any dependency hiccups.** Poor checks can eject all capacity during a shared incident.
12. **Disabling certificate verification is a diagnostic fix suitable for production.** It removes authentication and enables interception.

## 7. CHEAT SHEET — REVIEW ONLY

Review only; not a substitute for the lesson.

- Layers: application → transport → IP → link → physical.
- CIDR `/p` has `2^(32-p)` total IPv4 addresses.
- Flow: protocol + source IP:port + destination IP:port.
- DNS maps names; TTL is cache guidance, not instant cutover.
- TCP: reliable ordered bytes, not messages. UDP: datagrams.
- TLS: confidentiality + integrity + authenticated identity when correctly verified.
- HTTP retries depend on semantics/idempotency, not only status code.
- L4 routes flows; L7 understands application protocol.
- Transfer floor = bits / bits-per-second.
- Little's Law: in flight = rate × time.
- Plan capacity after failures, not only at normal mean.
- Diagnose DNS → route/port → transport → TLS → protocol → application.

## 8. PRACTICE SET FOR SELF-TEST

1. Compute total addresses in `192.168.16.0/22`.
2. Name the layers involved in sending an HTTPS request over Ethernet.
3. Explain why one TCP `read` may return half an application message.
4. Calculate ideal transfer time for 1 GB over 200 Mbit/s.
5. At 800 rps and 75 ms average, estimate concurrent in-flight work.
6. Ten instances serve 7,000 rps at safe capacity 900 each. Can two fail?
7. Distinguish DNS failure from TLS hostname failure.
8. Give a safe retry requirement for a timed-out payment POST.
9. Explain why replacing a private service hostname with its private IP can break TLS.
10. Allocate a 400 ms deadline across two downstream calls that cannot run concurrently, leaving 80 ms local/safety budget.

## 9. CURATED RESOURCES

- James Kurose and Keith Ross, *Computer Networking: A Top-Down Approach*, 8th ed., Chapters 1–3 and 5 — application, transport, network, link, delay, loss, throughput, DNS, HTTP, TCP, and routing.
- W. Richard Stevens, *TCP/IP Illustrated, Volume 1*, 2nd ed., Chapters 1–3, 10–18 — packet-level IP, UDP, TCP establishment, retransmission, flow, and congestion behavior.
- RFC 8200, “Internet Protocol, Version 6 (IPv6) Specification” — authoritative IPv6 packet and addressing foundations.
- RFC 9293, “Transmission Control Protocol (TCP)” — current TCP specification and exact stream/connection semantics.
- RFC 8446, “The Transport Layer Security (TLS) Protocol Version 1.3” — primary TLS 1.3 handshake, keys, records, and security properties.
- RFC 9110, “HTTP Semantics,” and RFC 9112/9113/9114 — authoritative methods, status, HTTP/1.1, HTTP/2, and HTTP/3 semantics.
- RFC 1034 and RFC 1035, “Domain Names” — canonical DNS concepts and implementation.
- Brendan Gregg, *Systems Performance*, 2nd ed., Chapter 10 “Network” — production measurement, tools, latency, throughput, errors, and diagnosis.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Programming Logic and Debugging:** provides layered hypothesis testing and numerical boundaries.
2. **Discrete Math and Bits:** provides binary addressing, masks, powers, and probability.
3. **Linux/Shell Foundations:** exposes processes, sockets, routes, DNS configuration, and diagnostic tools; learn in parallel.

### After

1. **Client–Server, APIs, RPC, and Messaging:** builds application communication contracts on these transports.
2. **Distributed Systems Foundations:** explains partial failure and coordination across networked nodes.
3. **Failure Semantics:** derives deadlines, retries, backoff, and circuit breaking.
4. **Cloud Identity and Networking:** applies CIDR, DNS, routing, TLS, and policy to Azure/private networks.
5. **SRE Observability:** measures network stage latency, errors, saturation, and dependencies.

---ANSWER KEY BELOW---

1. `2^(32-22)=1024` total.
2. HTTP, TLS, TCP (or QUIC/UDP for HTTP/3), IP, Ethernet, physical signals.
3. TCP exposes available ordered bytes, not sender write boundaries; receiver must frame and loop.
4. 1 GB≈8,000 megabits / 200 = 40 seconds ideal.
5. `800×0.075=60`.
6. Eight remain; mean 875 each, under 900 but with only 25 rps margin, so mathematically yes at perfect balance but operationally unsafe without variance/headroom.
7. DNS fails to produce an address/name record; TLS can reach an endpoint but rejects certificate identity for requested name.
8. Stable idempotency key plus atomic server-side request fingerprint/outcome handling, bounded deadline/backoff, or status reconciliation.
9. Certificate SAN normally covers the service DNS name, not raw private IP; SNI/virtual-host routing also uses the name.
10. Only 320 ms remains; e.g. first 140 ms, second 180 ms, with absolute remaining deadline and no retries that exceed it; actual allocation must use dependency latency evidence.
