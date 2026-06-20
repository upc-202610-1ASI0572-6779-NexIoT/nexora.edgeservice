# Technical Stories — Nexora Edge Service (Sprint 2)

## Overview

This document details the Technical Stories for the **Nexora Edge Service** corresponding to Sprint 2. This service operates as a perimetral IoT Gateway responsible for unattended reception of device (ESP32) telemetry to validate it, persist it locally in SQLite (Offline Mode), and update the property assets states.

The design aligns with the Domain-Driven Design (DDD) approach implemented in the project, encompassing the Monitoring and IAM Bounded Contexts.

---

### TS-EDGE-01 — Local Ingestion REST API for IoT Devices
As an IoT device firmware developer, I want to interact with a local HTTP ingestion endpoint on the Gateway to transmit telemetry payloads securely and unattended.

**Acceptance Criteria:**

* **Scenario: Successful Telemetry Ingestion**
  * **Given** an IoT device submits a `POST` request to `/api/v1/monitoring/telemetry`
  * **And** the request includes the `device_id` and sensor readings in the JSON body
  * **And** the `X-API-Key` header is included with a valid key
  * **When** the service processes and validates the telemetry structure
  * **Then** the Gateway returns a status code `200 OK`
  * **And** returns the immediate control action commands required for the actuator

* **Scenario: Malformed or Incomplete Payload**
  * **Given** a device submits a `POST` request to `/api/v1/monitoring/telemetry`
  * **And** the request payload omits the required `device_id` attribute
  * **When** the application service intercepts and validates the payload structure
  * **Then** the Gateway returns a status code `400 Bad Request`
  * **And** includes a JSON payload indicating `"error": "Incomplete or malformed payload"`

* **Scenario: Unauthorized Device (Missing or Invalid API Key)**
  * **Given** an ingestion request is made to the perimetral API
  * **And** the `X-API-Key` header does not match the registered credentials of the device
  * **When** the IAM authentication module evaluates the request
  * **Then** the Gateway denies access with a status code `401 Unauthorized`

---

### TS-EDGE-02 — Perimetral Data Persistence in Contingency (Offline Mode)
As an IoT infrastructure developer for Nexora, I want the Gateway to store received telemetry locally in an SQLite database so that data is not lost during network dropouts or cloud backend downtime.

**Acceptance Criteria:**

* **Scenario: Local Persistent Storage (SQLite)**
  * **Given** a device's telemetry payload is successfully validated
  * **When** the service delegates persistence to the local repository
  * **Then** the record is physically inserted into the local SQLite database (`TelemetryRecordModel`)
  * **And** it is associated with the corresponding device to guarantee subsequent traceability

* **Scenario: Automatic Storage Initialization (Bootstrap)**
  * **Given** the edge service receives its first HTTP request after startup
  * **When** the `@app.before_request` hook is executed
  * **Then** the local SQLite engine is initialized and the required tables are automatically created if missing
  * **And** a default test device is registered to allow immediate transmissions without prior manual configuration
