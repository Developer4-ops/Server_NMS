# 🛰️ Network Management System (NMS) - FastAPI

This project is a **Network Management System (NMS)** built with **FastAPI**, **PostgreSQL**, and **SQLAlchemy (async)**.  
It allows monitoring and management of **Linux and Windows servers** using various protocols such as **SSH**, **SNMP**, **WMI**, **WinRM**, and **Prometheus**.  

The system collects analytics like CPU, Memory, Disk, and Network statistics from devices and stores them in the database for visualization, alerting, and reporting.

---

## ⚙️ Tech Stack

- **Backend Framework:** FastAPI (Python)
- **Database:** PostgreSQL (with asyncpg)
- **ORM:** SQLAlchemy Async
- **Protocols Supported:** SSH, SNMP, WMI, WinRM, Prometheus
- **Libraries Used:**  
  - `paramiko` → For SSH-based Linux monitoring  
  - `psutil` → For system resource analytics  
  - `asyncpg` → Async PostgreSQL driver  
  - `pydantic` → Schema validation  
  - `logging` → Error and system log management  

---

## 🧩 Features

- ✅ Add and manage devices (Linux/Windows servers)
- 🧠 Multi-protocol monitoring support
- 📊 Collect metrics:
  - CPU usage, load averages, and core count  
  - Memory usage and swap info  
  - Disk usage and partitions  
  - Network interfaces (bytes, packets, errors)
- ⚡ Async background monitoring jobs
- 🔔 Alert rules and event generation
- 🔐 Extensible design for future integrations (Prometheus, SNMP, Cloud APIs)

---

## 📂 Project Structure

