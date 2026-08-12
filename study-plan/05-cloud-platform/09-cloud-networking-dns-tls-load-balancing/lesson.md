# Cloud Networking, DNS, TLS, and Load Balancing from Scratch

Parent subject: `05-cloud-platform`
Study time: 3–4 hours
Target: senior backend / AI platform / MLOps interviews

## 1. FOUNDATIONS

### From packet concepts to a cloud traffic path

Cloud networking constructs a private, programmable topology over provider infrastructure. A virtual network contains address spaces and subnets; route tables select next hops; stateful/stateless filters permit traffic; gateways connect networks; load balancers distribute flows/requests; DNS maps stable names; TLS authenticates and protects endpoints.

The goal is not merely connectivity. It is controlled reachability: the right identity/workload can reach the right service through observable, resilient paths, while public exposure, lateral movement, spoofing, and data exfiltration are constrained. A working architecture should trace both forward and return paths plus name resolution and authentication.

Cloud networks are software-defined, but physical limits and Internet protocols remain. Address overlaps break routing, packets need return routes, DNS caches, TCP retains connections, TLS certificates cover names, and stateful devices track flows. Provider abstractions change control mechanisms, not fundamentals.

### Virtual networks and address planning

An Azure **virtual network (VNet)** or AWS VPC is a logically isolated network with one or more non-overlapping CIDR address spaces. A **subnet** delegates a range to resources/service integrations and often becomes a policy/routing boundary. Plan addresses centrally because overlapping ranges prevent straightforward peering, VPN, or hub connectivity.

RFC 1918 private IPv4 ranges are `10.0.0.0/8`, `172.16.0.0/12`, and `192.168.0.0/16`. Private means not globally routed on the public Internet, not trusted. Every subnet still needs identity and filtering.

Suppose the organization reserves `10.40.0.0/16`. Four `/20` environment ranges provide 4,096 addresses each: `10.40.0.0/20`, `10.40.16.0/20`, `10.40.32.0/20`, `10.40.48.0/20`. Subdivide production into workload, private endpoints, integration, and data subnets with growth. Provider-reserved addresses reduce usable count.

### Routing and return paths

A route contains destination prefix and next hop. Routers choose **longest-prefix match**. A route for `10.40.8.0/24` wins over `10.40.0.0/16` for `10.40.8.12`. A default `0.0.0.0/0` catches everything else.

Traffic must have a valid forward and return path. Stateful firewalls/load balancers may require symmetric routing so both directions traverse the same device. User-defined routes can accidentally send response traffic elsewhere, producing silent drops. Route propagation from VPN/ExpressRoute and peering transit rules are provider-specific.

### Filtering: firewalls, security groups, and ACLs

Cloud network security groups commonly apply stateful allow/deny rules to interfaces/subnets. Stateful means return traffic for an allowed established flow is recognized without an explicit reverse allow, within documented behavior. Stateless ACLs evaluate each direction independently.

Rules match source/destination, protocol, port, direction, and priority. “Allow VNet” defaults can permit broad lateral movement. Prefer least reachability: ingress application gateway to API port; API subnet/identity to database private endpoint 5432; deny unrelated east-west traffic; controlled egress through inspection/NAT where required.

Network controls do not replace service authentication/authorization. Source IP is unstable under proxies/NAT and is not sufficient tenant identity.

### Public and private addressing

A public IP is Internet-routable through provider edge. A private endpoint assigns a private IP in a VNet for a managed service while keeping its standard service DNS name and TLS identity. A service endpoint (Azure-specific) can optimize/restrict access from a subnet while the service retains public addressing; Private Link maps a private endpoint and can disable public access. Know the exact product semantics.

Outbound Internet access commonly uses source NAT. A finite set of public IP/port combinations can suffer **SNAT port exhaustion** when many short-lived connections target the same endpoint. Reuse connections, size NAT, spread addresses, monitor allocation, and avoid connection churn. Adding retries during exhaustion worsens it.

### Peering, hub-and-spoke, VPN, and dedicated circuits

VNet peering connects address spaces through provider backbone, generally non-transitive unless routing through an appliance/gateway is designed. Hub-and-spoke centralizes shared DNS, firewall, ingress/egress, and on-prem connectivity, while spokes isolate workloads. The hub can become a blast-radius/throughput/ownership bottleneck.

Site-to-site VPN encrypts over the Internet. Dedicated connectivity such as Azure ExpressRoute provides private provider connectivity with bandwidth/reliability options, but encryption may be separate and provider/control dependencies remain. Redundant circuits must avoid shared physical/provider paths where true diversity is required.

### DNS zones and split-horizon resolution

Public DNS zones answer Internet clients. Private DNS zones answer linked networks/resolvers. **Split-horizon** DNS returns different answers based on resolver/view: the same managed service hostname can resolve publicly outside and to private endpoint IP inside.

For Azure private endpoints, provider-recommended private DNS zones and links map service FQDNs to private IPs. On-premises clients need conditional forwarding through reachable DNS resolver/inbound endpoint. Hardcoding the private IP breaks failover/recreation and TLS/service routing.

DNS is part of availability. Use redundant resolvers, bounded caches, health monitoring, and tested failover. Very low TTL increases authoritative query load and does not close existing connections; very high TTL slows record changes.

### TLS termination and end-to-end protection

TLS may terminate at a global edge, application gateway, ingress controller, sidecar, or backend. **TLS termination** decrypts traffic at that point. If proxy-to-backend uses plaintext, the protected boundary ends there. Regulated systems often re-encrypt and authenticate backend connections, sometimes using mTLS.

The load balancer sends SNI/host to choose certificate/route. Certificates need Subject Alternative Names for hostnames, trusted chains, private-key protection, automated rotation, and expiry monitoring. A wildcard `*.example.com` does not match multi-level `a.b.example.com` and creates broad key scope.

Client IP through proxies is conveyed with headers such as `Forwarded` or `X-Forwarded-For`, but only trust headers inserted/overwritten by known proxies. External clients can forge them otherwise.

### Load balancers, gateways, and health

A Layer 4 load balancer distributes TCP/UDP flows based on connection tuple/hash/algorithm. A Layer 7 gateway parses HTTP, terminates TLS, routes by host/path/header, may provide WAF, and can rewrite/redirect. A global traffic service routes users among regions via anycast/proxy/DNS techniques; a regional balancer distributes within region.

Health has layers:

- **liveness:** process should be restarted if false;
- **readiness:** instance can accept new traffic;
- **startup:** allow slow initialization without liveness kills;
- **deep synthetic:** external user path works, not used as a high-frequency instance probe.

Health probes need timeout, interval, unhealthy/healthy thresholds, expected status/body, host header, and source allowance. If interval is 10 seconds and three failures mark unhealthy, detection takes roughly 20–30+ seconds depending phase and probe duration; recovery has similar delay. Failover is not instantaneous.

### Web application firewalls and DDoS

A WAF inspects HTTP for known attack patterns, request size, bot/rate rules, and managed signatures. It complements secure code; false positives require staged tuning and observability. Network DDoS protection absorbs/filters volumetric attacks at provider edge, while application-layer exhaustion needs caching, admission, rate limits, autoscaling, and dependency protection.

### Zero trust and egress

Zero trust means no implicit trust based on network location. Authenticate users/workloads, authorize every action, encrypt, minimize privilege, inspect device/workload context as appropriate, and continuously observe. Microsegmentation limits lateral movement, but thousands of brittle IP rules can become unmanageable; use workload identity and policy-aware controls where supported.

Egress filtering reduces exfiltration and dependency sprawl. Private endpoints, service tags/FQDN-aware firewalls, proxies, and allow lists help, but dynamic SaaS/CDN endpoints and TLS inspection complicate it. Document required destinations and fail closed where business-safe.

## 2. CORE MECHANICS

### 2.1 Allocate non-overlapping CIDRs

Need dev/test/prod/DR with up to 2,000 total provider addresses each. A `/21` has 2,048 total, leaving almost no provider reservation/growth; choose `/20` (4,096) per environment if address space allows. From `10.40.0.0/16`, allocate on 16-boundaries in third octet.

Validate every planned range against on-prem, partner, acquired-company, Kubernetes pod/service, and managed integration ranges. Renumbering live state is expensive.

### 2.2 Trace public ingress

User request to `api.example.com`:

1. Public DNS resolves global/regional frontend.
2. Provider DDoS edge accepts/routes.
3. L7 gateway terminates TLS, verifies host/certificate, applies WAF/rate policy.
4. Gateway selects healthy backend pool based on route.
5. Backend TLS is established/verified if re-encrypted.
6. Backend authenticates token/identity and authorizes tenant/action.
7. Response returns through gateway; security headers and correlation are preserved.

Log edge/gateway decision, backend target, status, latency stages, TLS/WAF result, and safe request ID. Never log bearer tokens or sensitive body by default.

### 2.3 Trace private database access

API resolves `db.postgres.database.azure.com`. A private DNS chain maps it to a private endpoint IP, e.g. `10.40.34.7`. Route keeps traffic inside connected VNet. NSG/firewall allows API source to TCP 5432; managed database allows private endpoint and rejects public access. TLS still verifies the service hostname. PostgreSQL authenticates workload identity/credential and applies role privileges.

Failures localize as: wrong DNS → public or NXDOMAIN; no route/peering → timeout; NSG/firewall → drop; TLS wrong name/trust → handshake; DB auth → protocol error; pool/query → application latency.

### 2.4 Security rule review

Bad: inbound `0.0.0.0/0` to 22/3389 and database port. Better: no public management ports; use identity-aware bastion/JIT/private management, restricted admin identity/source, audit, MFA. Database reachable only from required workload boundary, authenticated separately.

Rules should include owner, reason, expiry for exceptions, ticket/evidence, and automated drift checks. Service tags simplify dynamic provider ranges but can be broad; understand exact tag scope.

### 2.5 Health timing

Probe interval 10 s, timeout 2 s, unhealthy threshold 3. If failure begins just after a successful probe, failures occur around 10,20,30 seconds, so removal around 30 seconds plus propagation. If each waits timeout, timing may add depending scheduler. Client retries before removal still hit target. Graceful deployment should mark unready first, wait for LB drain/connection handling, then terminate.

### 2.6 Load and zone arithmetic

Gateway receives 18,000 rps. Three zones have six backends each; safe capacity 1,200 each. Normal capacity 21,600. One zone loss leaves 12×1,200=14,400, below traffic. Need at least 15 surviving, so equal layout needs ceil(15/2)=8 per zone, 24 total, with extra headroom beyond exact mean.

Also verify gateway/WAF TLS connection and rule throughput. Backends are not the only bottleneck.

### 2.7 SNAT estimate

One public IPv4 has roughly 64K ports but platform reservations/reuse/time-wait and per-destination allocation reduce usable concurrency. If 100 instances each open 1,000 simultaneous fresh flows through one NAT IP to one endpoint, demand is 100,000—beyond one 16-bit port space. Reuse HTTP/2/keepalive pools, add NAT IP capacity, reduce churn, and monitor provider metrics. Exact Azure NAT Gateway port allocation differs; use official current limits.

### 2.8 DNS migration

Before cutover: lower TTL well in advance so old cached TTL expires, validate new endpoint/certificate, dual-run, perform canaries, then change record/traffic weight. Observe both endpoints longer than TTL plus connection lifetime and resolver behavior. Retain rollback capacity. Weighted DNS is not per-request exact and clients may pin one answer.

### 2.9 TLS rotation

Issue new certificate before expiry, deploy it alongside/replace atomically, confirm chain/SAN/key/algorithm across clients, monitor handshake errors, and keep rollback while old remains valid. Rotate private key after exposure. Automate renewal but alert on renewal, deployment, and remaining lifetime; “auto-renewed in vault” does not prove gateway loaded it.

### 2.10 Multi-region entry point

Global gateway/DNS routes to region A/B. Decide active-active or active-passive per data semantics. Health should test region readiness, not only edge. DNS-based failover inherits TTL/client caching; proxy/anycast can steer faster but is a dependency. Database authority and write conflict strategy determine whether the second region can safely accept writes.

Run failover drills measuring detection, traffic shift, error rate, capacity, data point, DNS/TLS, and failback. A diagram is not recovery evidence.

## 3. WORKED PROBLEMS

### Problem 1 — Longest prefix (easy)

Routes `10.0.0.0/8→A`, `10.40.0.0/16→B`, `10.40.8.0/24→C`. Destination `10.40.8.7`?

**Solution.** C, the /24 most-specific match.

**Trap:** first configured route rather than longest prefix (unless product adds priority semantics after match).

### Problem 2 — Subnet count (easy)

How many `/24` networks fit in `/20`?

**Solution.** Difference 4 prefix bits: `2^4=16` subnets, each 256 total addresses.

**Trap:** dividing prefix numbers.

### Problem 3 — Private is trusted? (easy)

Is traffic from RFC1918 address authenticated?

**Solution.** No. Private address only describes routing scope; compromised workloads, NAT, spoofing boundaries, and shared networks exist. Authenticate and authorize application/workload identity.

**Trap:** IP allow list as sole tenant authorization.

### Problem 4 — Private endpoint TLS (medium)

Why connect using service FQDN rather than private IP?

**Solution.** DNS maps stable service identity to private address; certificate/SNI covers hostname; IP can change and may not be valid SAN. This composes private routing with TLS identity.

**Trap:** disabling hostname verification to use IP.

### Problem 5 — Probe detection (medium)

Interval 5 s, unhealthy threshold 4. Approximate worst phase detection ignoring timeout?

**Solution.** Failure just after a probe requires failures at ~5,10,15,20 seconds: near 20 seconds plus control propagation. Best phase near 15 seconds. Include timeouts/provider specifics.

**Trap:** saying 4×5 always exact or five seconds.

### Problem 6 — Return path (medium)

Request traverses firewall but response follows default route directly. Result?

**Solution.** Stateful firewall may drop/lose state because asymmetric return bypasses it; source NAT/session expectations can fail. Fix route symmetry or use supported asymmetric architecture.

**Trap:** checking only forward reachability.

### Problem 7 — Zone capacity (hard)

24 backends across 3 zones, each safe 700 rps, peak 12,000. Survive zone loss?

**Solution.** Eight/zone; after loss 16×700=11,200, insufficient. Need ceil(12,000/700)=18 survivors; equal layout needs 9/zone=27 total just for exact peak, plus headroom.

**Trap:** using total 16,800 normal capacity.

### Problem 8 — SNAT exhaustion (hard)

Symptoms are intermittent outbound connect timeouts under scale-out, while existing connections work. Hypothesis?

**Solution.** SNAT/ephemeral port exhaustion is plausible. Check NAT metrics, flows per destination, connection reuse/TIME_WAIT, pool configuration, public IP allocation. Mitigate with keepalive/multiplexing and sized NAT, not retries alone.

**Trap:** adding aggressive connection retries, increasing churn.

### Problem 9 — WAF false positive (hard)

FHIR search containing encoded syntax is blocked after managed-rule update. Response?

**Solution.** Correlate WAF rule/request safely, validate legitimacy, create narrow documented exclusion/tuning for endpoint/parameter if justified, keep other protections, test regression, monitor, and review vendor rule. Do not disable WAF globally.

**Trap:** choosing security off versus application broken as only options.

## 4. REAL-WORLD / APPLIED CONTEXT

### Azure hub-and-spoke

Azure architectures commonly place Firewall, VPN/ExpressRoute gateway, Bastion, DNS Private Resolver, and shared ingress in a hub, with workload VNets as spokes. Peering is non-transitive by default; route tables/gateway transit/appliances must be explicit. Centralization simplifies control but requires zone redundancy, scale, ownership, and blast-radius planning.

### Azure Private Link and Private DNS

Private Link assigns a private endpoint network interface for services such as Storage or PostgreSQL. Recommended private DNS zones override resolution inside linked networks. On-prem resolution often conditionally forwards Azure private zones through a Private Resolver. Public network access can then be disabled after all paths are verified.

### Application Gateway / Front Door / Load Balancer

Azure Load Balancer is regional Layer 4. Application Gateway is regional Layer 7 with TLS/WAF capabilities. Front Door is global HTTP(S) edge routing/acceleration/WAF. Designs can combine them, but each adds health, certificate, timeout, header, logging, and cost configuration.

## 5. COMPARISON TABLE

| Component | Scope/layer | Uses | Main caveat |
|---|---|---|---|
| NSG/security group | Interface/subnet L3/L4 | Distributed allow/deny | Rule sprawl/broad defaults |
| Network firewall | Central L3–L7 depending product | Egress/ingress inspection | Route symmetry, scale, cost |
| L4 load balancer | Regional transport | TCP/UDP distribution | No HTTP path/WAF semantics |
| L7 gateway | Regional HTTP | TLS, path routing, WAF | More configuration/latency |
| Global edge | Cross-region HTTP/DNS/anycast | Regional failover/acceleration | Shared dependency/data authority |
| Service endpoint | Service public endpoint with VNet context | Restricted managed service access | Not a private IP; product-specific |
| Private endpoint | Private IP to managed service | Private reachability | DNS, IP consumption, per-resource policy |
| VPN | Encrypted Internet tunnel | Hybrid/site connectivity | Internet path/jitter/throughput |
| Dedicated circuit | Private provider connectivity | Predictable hybrid bandwidth | Cost, diversity, encryption may be separate |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Private IP means secure/trusted.** Identity and least privilege remain.
2. **NAT is firewall.** Address translation is not authorization.
3. **Forward route proves connectivity.** Return route/state matters.
4. **Peering is always transitive.** Cloud peering typically is not by default.
5. **Private endpoint removes DNS need.** Correct private DNS is central.
6. **Connect by private IP and disable TLS checks.** This breaks authenticated service identity.
7. **One load balancer makes multi-zone.** Backend placement and dependencies determine resilience.
8. **Liveness and readiness are the same.** Restart decision differs from traffic admission.
9. **DNS TTL equals failover time.** Client caches/connections and health/control propagation differ.
10. **WAF replaces secure coding.** It is compensating/detection control with false positives.
11. **More retries fix connect timeouts.** They can amplify SNAT/overload.
12. **Multi-region ingress makes data active-active.** Database consistency/authority decides writes.

## 7. CHEAT SHEET — REVIEW ONLY

Review only; not a substitute for the lesson.

- Plan non-overlapping VNet/VPC, on-prem, partner, pod/service CIDRs.
- Longest prefix wins; trace forward and return routes.
- Stateful rule allows established return according to product; verify exact semantics.
- Private network location is not identity.
- Private endpoint = private IP; keep service FQDN for DNS/TLS.
- Peering often non-transitive; hub routing is explicit.
- L4 routes flows; L7 parses HTTP/TLS and may provide WAF.
- Liveness restarts; readiness admits traffic; startup protects initialization.
- Probe failover takes intervals × thresholds + propagation.
- SNAT ports are finite; reuse connections and size egress.
- Rotate certificates before expiry and verify deployment, not only issuance.
- Multi-region traffic requires matching data/failure semantics.

## 8. PRACTICE SET FOR SELF-TEST

1. Compute total addresses in `/18` and number of `/22` subnets it contains.
2. Choose route for `172.16.5.8` given `/12`, `/16`, `/24` matches.
3. Explain stateful versus stateless filtering.
4. Trace private endpoint access from on-prem client through DNS and network.
5. With 15-second probe interval and threshold 3, estimate removal window.
6. Calculate surviving capacity for three zones, 5 instances/zone, 900 rps each, one-zone loss.
7. Explain why existing connections may continue after DNS failover.
8. State safe trust handling for `X-Forwarded-For`.
9. Choose Azure L4 regional, L7 regional WAF, or global HTTP routing for three scenarios.
10. List five causes of TLS handshake failure after network reachability succeeds.

## 9. CURATED RESOURCES

- Microsoft Learn, “Azure Virtual Network,” “Virtual network traffic routing,” and “Network security groups” — authoritative Azure address, subnet, route, peering, and stateful rule semantics.
- Microsoft Learn, “What is Azure Private Link?” and “Azure Private Endpoint DNS configuration” — exact private endpoint/service DNS behavior and recommended zones.
- Microsoft Learn, architecture docs for Azure Load Balancer, Application Gateway, Front Door, NAT Gateway, Firewall, VPN Gateway, ExpressRoute, and DNS Private Resolver — current component boundaries, limits, and traffic paths.
- RFC 1918, “Address Allocation for Private Internets,” and RFC 4632, “Classless Inter-domain Routing” — primary private addressing and CIDR foundations.
- RFC 1034/1035 DNS, RFC 8446 TLS 1.3, and RFC 9110 HTTP Semantics — protocol sources below cloud products.
- Microsoft Cloud Adoption Framework, “Azure network topology and connectivity” / landing-zone networking guidance — enterprise hub-spoke, DNS, hybrid, ingress/egress, and governance patterns.
- Evan Gilman and Doug Barth, *Zero Trust Networks*, 2nd ed., Chapters 1–7 — identity-centered network access and policy design beyond perimeter trust.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Computer Networking:** supplies packets, CIDR, routes, DNS, TCP, TLS, HTTP, and latency.
2. **Cloud Computing Foundations:** supplies regions/zones, control planes, service models, and fault domains.
3. **Linux:** supplies sockets, routes, DNS resolver, certificates, and diagnostics.

### After

1. **Containers:** applies namespace/port/egress and image registry networking.
2. **Kubernetes:** adds pod/service/ingress/network-policy layers.
3. **Terraform:** encodes VNets, routes, rules, DNS, gateways, and dependencies.
4. **Cloud Identity and Networking:** deepens Azure workload identity, RBAC, Private Link, NSG, and policy.
5. **SRE:** monitors traffic, probes, TLS/DNS, saturation, zone loss, and failover.

---ANSWER KEY BELOW---

1. `2^14=16,384` total; `2^(22-18)=16` `/22`s.
2. `/24`, the longest/more specific match.
3. Stateful tracks allowed flows and permits matching return; stateless evaluates both directions independently.
4. On-prem conditional forwarder → reachable private resolver/zone → private IP; VPN/ExpressRoute route → NSG/firewall → private endpoint → TLS service FQDN → service auth/role.
5. Roughly 30–45 seconds depending phase, plus timeout/control propagation (three failures spaced 15 seconds).
6. Ten remain ×900=9,000 rps.
7. DNS affects new resolution; TCP/TLS pools pin selected old IP until close/timeout/drain.
8. Edge proxy strips/overwrites inbound spoofed header and app trusts only known proxy hop/standard parsed chain.
9. Azure Load Balancer for generic TCP/UDP; Application Gateway for regional HTTP path/TLS/WAF; Front Door for global HTTP regional steering (subject to exact current features).
10. Untrusted CA, hostname/SAN mismatch, expiry/not-yet-valid/clock, protocol/cipher incompatibility, missing/rejected client cert, SNI mismatch (any five).
