# Cybersecurity Report: MQTT Broker Deployment
## TNE20003 – Internet and Cybersecurity for Engineering Applications

---

## 1. Executive Summary

This report identifies and analyses the cybersecurity vulnerabilities present in the
client's current MQTT (Mosquitto) broker deployment at 192.168.12.100. While the broker
is restricted to the internal organisation network, several significant security weaknesses
exist that could expose sensitive IoT data and allow unauthorised access or manipulation
of connected devices. These issues must be addressed to ensure the integrity,
confidentiality, and availability of the IoT system.

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

## 3. Security Issues Identified

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
denial-of-service), disrupting all other projects subscribed to public topics. There is
also no validation that published data is legitimate sensor data.

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
high rate, or triggering broker-level errors. This is a resource exhaustion or
denial-of-service risk.

**Impact:** Critical IoT systems relying on this broker for real-time data could
experience delays or failures due to another project's activity. In an industrial
environment, this could have safety implications.

---

### 3.5 No Message Integrity or Authentication (Medium)

**Issue:** MQTT messages contain no cryptographic signature or integrity check. Any
authenticated client can publish any content to any topic they have access to.

**Risk:** There is no way for a subscribing device to verify that a message it received
was actually sent by the legitimate publisher and has not been tampered with in transit.
A compromised account or a MITM attacker (possible given Issue 3.1) could inject false
messages — for example, sending a fake sensor reading or a falsified device command.

**Impact:** Devices acting on forged commands could enter dangerous or unintended states
(e.g., a false temperature spike triggering emergency cooling). Data integrity cannot be
guaranteed.

---

### 3.6 Perimeter-Only Security Model (Medium)

**Issue:** The only security control preventing external access is network-level
restriction — the broker's IP address is not routable from outside the organisation
network. There are no application-layer defences against threats from inside the network.

**Risk:** This is a "castle and moat" security model. Once an attacker is inside the
network — whether through a compromised internal machine, an unauthorised physical
connection, or a rogue employee — there are no further barriers to accessing the broker
and all its connected devices. This is also known as the insider threat problem.

**Impact:** A single internal compromise gives an attacker full access to all IoT data
and control over all connected devices on the broker.

---

### 3.7 No Audit Logging or Intrusion Detection (Low–Medium)

**Issue:** There is no indication that the broker is configured to log connection
attempts, message activity, or failed authentication events in a way that would alert
administrators to suspicious behaviour.

**Risk:** Without audit logs, it is impossible to detect unauthorised access after the
fact, investigate incidents, or identify patterns of abuse. An attacker could
authenticate, subscribe to all available topics, and disconnect without any trace.

**Impact:** Security incidents would go undetected. There is no accountability for
actions taken on the broker.

---

## 4. Risk Summary Table

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

## 5. Recommendations

### 5.1 Enable TLS Encryption (Addresses Issue 3.1)
Configure Mosquitto to use TLS on port 8883 instead of plain TCP on port 1883.
All clients should be required to connect using TLS, ensuring all data in transit is
encrypted. Self-signed certificates are acceptable for internal use; a proper CA-signed
certificate is recommended for production.

### 5.2 Enforce Strong Password Policy (Addresses Issue 3.2)
Immediately change all account passwords to strong, randomly generated values. Passwords
should be stored as hashed values in the Mosquitto password file using the
`mosquitto_passwd` tool. Consider integrating with an organisational identity provider
(e.g., LDAP/Active Directory) for centralised credential management.

### 5.3 Implement Granular Access Control Lists (Addresses Issue 3.3)
Define strict ACL rules in Mosquitto's configuration to limit what each user can publish
and subscribe to. Rate-limiting should be applied to the `public` topic to prevent
flooding. Consider separating the public topic into moderated sub-channels.

### 5.4 Isolate Projects onto Separate Broker Instances or Use Virtual Hosts
(Addresses Issue 3.4)
Where feasible, deploy dedicated broker instances per project or use resource quotas and
connection limits per client to prevent one project from impacting others.

### 5.5 Implement Application-Level Message Signing (Addresses Issue 3.5)
Have publishing devices sign messages using HMAC or a lightweight digital signature
scheme. Subscribing devices should verify the signature before acting on any received
message. This ensures authenticity and integrity independent of transport security.

### 5.6 Adopt Defence-in-Depth (Addresses Issue 3.6)
Do not rely solely on network perimeter controls. Implement authentication at the
application layer (already partially done), enforce least-privilege access control, and
consider network segmentation to isolate the IoT broker from general-purpose workstations.

### 5.7 Enable Audit Logging and Monitoring (Addresses Issue 3.7)
Enable Mosquitto's logging features to record all connection attempts, authentication
failures, and message activity. Forward logs to a centralised SIEM (Security Information
and Event Management) system and configure alerts for suspicious patterns (e.g., repeated
failed logins, unusually high message rates).

---

## 6. Conclusion

The current MQTT broker deployment provides basic topic-level access control and internal
network isolation, but lacks fundamental security controls expected in any production IoT
environment. The most critical issues — plaintext communication and weak credentials —
can be exploited trivially by any user with access to the internal network. Implementing
TLS encryption and a strong password policy should be treated as immediate priorities,
followed by improved access control, message integrity verification, and audit logging.
These measures will significantly reduce the attack surface of the IoT infrastructure
and protect the confidentiality, integrity, and availability of connected devices and
their data.

---

*Report prepared as part of TNE20003 Portfolio Task – Project*
*Swinburne University of Technology*
