# Cybersecurity Report: MQTT Broker Deployment
## TNE20003 – Internet and Cybersecurity for Engineering Applications
### High Distinction Extension: Internet Exposure Risk Analysis

---

## 1. Executive Summary

This report identifies and analyses the cybersecurity vulnerabilities present in the
client's current MQTT (Mosquitto) broker deployment at 192.168.12.100. While the broker
is restricted to the internal organisation network, several significant security weaknesses
exist that could expose sensitive IoT data and allow unauthorised access or manipulation
of connected devices.

This High Distinction extension also evaluates the additional risks that would arise if the
broker were exposed to the public internet — a scenario increasingly common as organisations
adopt cloud-hosted IoT infrastructure. The analysis demonstrates how the existing weaknesses
would be catastrophically amplified in an internet-facing deployment and identifies the
additional controls required.

---

## 2. Current Deployment Overview

The client is operating a Mosquitto MQTT message broker on a private internal network
(192.168.12.100, port 1883). The broker serves as the communication hub for multiple
IoT projects across the organisation. Key characteristics of the current deployment:

- Protocol: MQTT version 3.1.1
- Transport: Plain TCP on port 1883 (no encryption)
- Authentication: Username and password per project account
- Access Control: Topic-level restrictions based on username prefix
- Network Access: Restricted to the internal lab network only (no external access)
- Shared Infrastructure: A single broker instance is shared across all projects

---

## 3. Security Issues Identified (Internal Network)

### 3.1 No Transport Layer Encryption (Critical)

**Issue:** The broker operates on port 1883 using plain, unencrypted TCP. All messages
transmitted between clients and the broker — including login credentials, sensor data,
and device commands — are sent in plaintext.

**Risk:** Any user on the same internal network can use packet capture tools (such as
Wireshark) to intercept and read all MQTT traffic in real time. This is known as a
man-in-the-middle (MITM) attack or passive eavesdropping. Since the organisation's
network is shared across multiple projects and staff, this represents a realistic and
serious threat.

**Impact:** Confidential sensor data can be read. Device commands (e.g., "turn off
alarm", "unlock door") can be observed. Login credentials are exposed in every
connection attempt.

---

### 3.2 Weak Authentication Credentials (High)

**Issue:** Each project account is assigned a password that is identical to the username
(i.e., the student ID). This is an extremely weak credential policy.

**Risk:** An attacker who knows or guesses a student ID (which may be derivable from
public university records or social engineering) can immediately authenticate as that
user. Since usernames follow a predictable numeric pattern, brute-force or enumeration
attacks are trivial.

**Impact:** An attacker could authenticate as another project's account, subscribe to
their private topics, intercept their sensor data, and publish false or malicious
commands to their devices.

---

### 3.3 Insufficient Access Control (High)

**Issue:** Access control is implemented only at the top-level topic prefix level. Each
user can publish and subscribe to any sub-topic beneath their username, and all users
share access to the `public` topic hierarchy without restriction.

**Risk:** There is no restriction on the type, volume, or content of messages that can
be published. A user could flood the `public` topic with garbage data (a form of
denial-of-service), disrupting all other projects subscribed to public topics.

**Impact:** Malicious or accidental abuse of the `public` topic could disrupt all
connected projects simultaneously. No mechanism prevents a user from publishing
misleading data to shared topics.

---

### 3.4 Shared Broker Infrastructure (Medium)

**Issue:** A single Mosquitto broker instance is shared among all student projects. The
broker's resources (CPU, memory, network bandwidth, connection limits) are pooled across
all users.

**Risk:** One misbehaving or compromised client could degrade performance for all other
projects — for example, by opening many simultaneous connections, publishing at a very
high rate, or triggering broker-level errors.

**Impact:** Critical IoT systems relying on this broker for real-time data could
experience delays or failures due to another project's activity.

---

### 3.5 No Message Integrity or Authentication (Medium)

**Issue:** MQTT messages contain no cryptographic signature or integrity check. Any
authenticated client can publish any content to any topic they have access to.

**Risk:** There is no way for a subscribing device to verify that a message it received
was actually sent by the legitimate publisher and has not been tampered with in transit.
A compromised account or a MITM attacker could inject false messages.

**Impact:** Devices acting on forged commands could enter dangerous or unintended states
(e.g., a false temperature spike triggering emergency cooling). Data integrity cannot be
guaranteed.

---

### 3.6 Perimeter-Only Security Model (Medium)

**Issue:** The only security control preventing external access is network-level
restriction. There are no application-layer defences against threats from inside the
network (insider threat problem).

**Risk:** Once an attacker is inside the network — through a compromised internal
machine, an unauthorised physical connection, or a rogue employee — there are no further
barriers to accessing the broker and all its connected devices.

**Impact:** A single internal compromise gives an attacker full access to all IoT data
and control over all connected devices on the broker.

---

### 3.7 No Audit Logging or Intrusion Detection (Low–Medium)

**Issue:** There is no indication that the broker is configured to log connection
attempts, message activity, or failed authentication events in a way that would alert
administrators to suspicious behaviour.

**Risk:** Without audit logs, it is impossible to detect unauthorised access after the
fact, investigate incidents, or identify patterns of abuse.

**Impact:** Security incidents would go undetected. There is no accountability for
actions taken on the broker.

---

## 4. Risk Summary Table (Internal Network)

| # | Issue                            | Severity | Likelihood | Impact   |
|---|----------------------------------|----------|------------|----------|
| 1 | No TLS encryption (plaintext)    | Critical | High       | High     |
| 2 | Weak credentials (ID = password) | High     | High       | High     |
| 3 | Insufficient access control      | High     | Medium     | High     |
| 4 | Shared broker infrastructure     | Medium   | Medium     | Medium   |
| 5 | No message integrity checks      | Medium   | Medium     | High     |
| 6 | Perimeter-only security model    | Medium   | Medium     | High     |
| 7 | No audit logging / IDS           | Medium   | High       | Medium   |

---

## 5. High Distinction Extension: Internet Exposure Risk Analysis

### 5.1 Scenario

Many real-world IoT deployments expose MQTT brokers to the public internet to allow
remote monitoring, cloud integration, or mobile access. This section analyses what would
happen if the current broker at 192.168.12.100 were made internet-accessible — for
example, by assigning it a public IP address or forwarding port 1883 through a
firewall. This scenario reveals the catastrophic amplification of every existing weakness.

---

### 5.2 Automated Scanning and Exploitation (Critical)

**Issue:** Internet-connected MQTT brokers on the default port 1883 are actively
scanned by automated tools. Platforms such as Shodan index thousands of exposed MQTT
brokers within hours of them going online. Many of these brokers are already
compromised.

**Risk:** Within minutes of internet exposure, automated scanners would discover the
broker. Combined with Issue 3.2 (credentials equal to the username), automated
credential-stuffing tools could authenticate successfully without human intervention.

**Real-world reference:** Security researchers have demonstrated that IoT devices
on default credentials are compromised within seconds on the public internet (Mirai
botnet, 2016; Shodan MQTT surveys, 2020–2024).

**Impact:** The broker would be compromised without any targeted effort. Attackers
could subscribe to all topics, read all sensor data, inject malicious commands into
industrial devices, and use the broker as a pivot point for broader network attacks.

---

### 5.3 Unauthenticated Mass Subscription (Critical)

**Issue:** Because Topic 1 (`public/STUDENT_ID/alerts/temperature`) is accessible to
all authenticated users, and authentication is trivially bypassed (Issue 3.2), any
internet user who discovers the broker can subscribe to and monitor all public topic
traffic.

**Risk:** Surveillance of industrial sensor data from anywhere in the world. Attackers
could build a full picture of the facility's operational patterns — peak production
times, equipment stress periods, system downtime — and use this for targeted physical
or cyber attacks.

**Impact:** Confidential operational data (production rates, equipment health,
temperature thresholds) becomes publicly visible intelligence, enabling competitor
espionage or targeted sabotage.

---

### 5.4 Command Injection from the Internet (Critical)

**Issue:** Combining plaintext transport (Issue 3.1), weak credentials (Issue 3.2),
and no message integrity checks (Issue 3.5), a remote attacker can publish arbitrary
commands to device command topics (`STUDENT_ID/commands/device1`).

**Risk:** An attacker anywhere in the world could send `EMERGENCY_COOLING` or a
custom malicious payload to Device 1. Without message signing, the device has no way
to distinguish a legitimate command from an injected one.

**Impact:** In an industrial context, injected commands could trigger physical
consequences: activating or deactivating cooling systems, locking safety mechanisms,
or generating false sensor readings that cause automated responses. This bridges the
gap between a cyber attack and physical harm.

---

### 5.5 Denial-of-Service from the Internet (High)

**Issue:** Mosquitto has configurable but finite connection and message rate limits.
Without rate limiting and with the broker exposed to the internet, any actor can open
thousands of connections or flood topics with high-frequency messages.

**Risk:** Distributed Denial-of-Service (DDoS) attacks could render the broker
unavailable to legitimate devices. Unlike internal DoS (Issue 3.3), internet-scale DoS
involves far greater traffic volumes and is much harder to mitigate without upstream
filtering.

**Impact:** All real-time IoT data collection and device control would fail. Safety-
critical monitoring systems would be unable to detect or respond to genuine alarms.

---

### 5.6 Credential Harvesting via Plaintext Interception (High)

**Issue:** On the public internet, network traffic traverses multiple untrusted hops.
Without TLS (Issue 3.1), credentials transmitted in the CONNECT packet are readable at
any point along the network path, not just within the local network.

**Risk:** ISP-level passive surveillance, malicious exit nodes, BGP hijacking, and
ARP spoofing all become viable credential interception vectors. Captured credentials
can be reused to access other university systems where the same password is used.

**Impact:** Credential reuse across university systems (email, student portals, lab
access) could result in a breach that extends far beyond the IoT project.

---

### 5.7 Regulatory and Legal Liability (Medium)

**Issue:** In Australia, the Privacy Act 1988 (as amended) and the Security of Critical
Infrastructure Act 2018 impose obligations on organisations that hold or process
personal or sensitive data. If student IDs, device data, or operational information are
exposed via an insecure internet-facing IoT deployment, the organisation may face
regulatory sanctions.

**Risk:** Exposing a poorly secured broker to the internet without proper controls
would likely constitute a data breach notifiable under the Notifiable Data Breaches
(NDB) scheme if personal information is involved.

**Impact:** Legal liability, reputational damage, and potential fines for the
institution operating the broker.

---

## 6. Internet Exposure Risk Summary Table

| # | Additional Risk (Internet Exposure)       | Severity | Likelihood | Impact   |
|---|-------------------------------------------|----------|------------|----------|
| 8 | Automated scanning and credential stuffing | Critical | Very High  | Critical |
| 9 | Unauthenticated mass subscription          | Critical | High       | High     |
|10 | Remote command injection                   | Critical | High       | Critical |
|11 | Internet-scale DDoS                        | High     | Medium     | High     |
|12 | Credential harvesting in transit           | High     | Medium     | High     |
|13 | Regulatory and legal liability             | Medium   | High       | High     |

---

## 7. Recommendations

### 7.1 Enable TLS on Port 8883 (Addresses Issues 3.1, 5.6)
Configure Mosquitto to use TLS. All clients must connect via port 8883 with certificate
validation. For internet exposure, use CA-signed certificates (e.g., Let's Encrypt).
Self-signed certificates are acceptable for internal use only.

### 7.2 Enforce Strong, Unique Passwords (Addresses Issues 3.2, 5.2, 5.6)
Change all passwords immediately to randomly generated values. Use `mosquitto_passwd`
to store bcrypt-hashed credentials. Consider integrating with an organisation identity
provider (LDAP/Active Directory/OAuth2) and enforcing multi-factor authentication.

### 7.3 Implement Granular ACLs with Rate Limiting (Addresses Issues 3.3, 5.3, 5.5)
Define strict ACL rules limiting publish/subscribe rights per user. Apply per-client
connection and message rate limits. For internet exposure, add IP-based allowlists and
use a TLS client certificate requirement.

### 7.4 Isolate Infrastructure and Apply Resource Quotas (Addresses Issue 3.4, 5.5)
Deploy dedicated broker instances per project or use resource quotas per client.
For internet-facing deployments, place the broker behind a reverse proxy or API gateway
that can absorb DDoS traffic.

### 7.5 Implement Application-Level Message Signing (Addresses Issue 3.5, 5.4)
Sign all published messages using HMAC-SHA256 or JWT. Subscribing devices must verify
the signature before acting on any command. This ensures authenticity independent of
transport security and prevents injection attacks even if credentials are compromised.

### 7.6 Adopt Defence-in-Depth (Addresses Issues 3.6, 5.2–5.5)
Layer multiple controls: TLS, strong authentication, ACL, rate limiting, message
signing, network segmentation, and intrusion detection. No single control should be
the sole barrier. For internet deployment, add a Web Application Firewall (WAF) and
real-time threat intelligence feeds.

### 7.7 Enable Comprehensive Audit Logging and SIEM Integration (Addresses Issue 3.7)
Enable Mosquitto logging for all connection attempts, authentication failures, and
message activity. Forward logs to a centralised SIEM. Configure alerts for indicators
of compromise (repeated failed logins, unusual subscription patterns, high message
rates from a single client).

### 7.8 Implement AI-Based Anomaly Detection (Addresses Issue 5.2–5.4)
Deploy machine learning anomaly detection (such as Isolation Forest) on the message
stream to identify statistically unusual sensor readings or command patterns. Anomalous
messages — likely indicators of injection attacks or compromised devices — can be
flagged for human review or automatically quarantined before devices act on them. This
project demonstrates this capability via the High Distinction UI client.

### 7.9 Never Expose Port 1883 to the Internet (Fundamental Control)
If internet access is required, use a VPN gateway or SSH tunnel to reach the internal
broker rather than exposing the broker directly. If a cloud broker is needed, use a
managed service (AWS IoT Core, Azure IoT Hub, HiveMQ Cloud) that enforces TLS and
modern authentication by default.

---

## 8. Conclusion

The current internal deployment has significant weaknesses, but they are bounded by the
network perimeter. Internet exposure would remove that boundary entirely, transforming
every internal weakness into a globally accessible attack surface. Automated scanning,
credential stuffing, remote command injection, and DDoS are not theoretical risks for
internet-exposed IoT systems — they are routine occurrences documented in global
incident data.

The most critical immediate actions are: enforce TLS, rotate all credentials, and
implement message signing. For any internet exposure scenario, these three controls must
be in place before the broker is reachable from outside the organisation network.

AI-based anomaly detection, as demonstrated in this project, adds a further layer of
defence by detecting statistically abnormal messages that may indicate ongoing attacks —
bridging the disciplines of cybersecurity and machine learning in a practical IoT
context.

---

*Report prepared as part of TNE20003 Portfolio Task – Project (High Distinction)*
*Swinburne University of Technology*
