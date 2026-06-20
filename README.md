# BestApp: Enterprise IoT Management Dashboard

BestApp is a full-stack web application built with Python and Flask. It acts as a central control hub for a network of IoT edge devices, providing a unified dashboard for inventory and facility management within a factory environment[cite: 2, 3]. The application aggregates real-time telemetry from Security, Humidity, and Forklift Safety sensors.

## Key Features

*   **Real-Time IoT Integration:** Utilises a HiveMQ MQTT cluster for synchronous, bidirectional communication with remote Raspberry Pi Pico microcontrollers monitoring the factory floor.
*   **Role-Based Access Control (RBAC):** Features strict authorisation tiers based on employee departments[cite: 2].
    *   **Managers:** Full access to employee records, RFID card assignment, stock adjustment, and safety logs.
    *   **Security Personnel:** Exclusive access to monitor and audit RFID entrance logs and denied access attempts.
    *   **Stock Control:** Access to dynamically update and track raw material inventory.
*   **Secure Communication:** Enforces TLS encrypted connections via the `isrgrootx1.pem` certificate between the Flask backend and the MQTT broker to protect sensitive access data[cite: 3, 4].
*   **Persistent Data Storage:** Leverages an SQLite database (`data.db`) to reliably log high-frequency data, including access timestamps, stock changes, and proximity safety alerts.

## Technology Stack

*   **Backend:** Python 3, Flask
*   **IoT Protocol:** MQTT (HiveMQ cluster)[cite: 3]
*   **Database:** SQLite[cite: 2]
*   **Frontend:** HTML5, CSS3, Jinja2 Templating[cite: 4]
*   **Security:** TLS Encryption, RBAC[cite: 2, 3]

## Repository Structure

```text
BESTAPP1/
├── service/               # Backend business logic and MQTT handlers
├── static/                # CSS, JavaScript, and image assets
├── templates/             # Jinja2 HTML templates for the dashboard UI
├── .gitignore             # Environment and security exclusions
├── data.db                # SQLite relational database
├── db.py                  # Database connection and querying logic
├── isrgrootx1.pem         # Root CA certificate for secure TLS MQTT connection
└── main.py                # Main Flask application entry point
