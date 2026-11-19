<div align="center">
  <h1>🛡️ OrbitalGuard: NEO Risk & Planetary Defense Simulator</h1>
  <p><strong>NASA Space Apps Challenge 2026 Submission</strong><br>
  Real-Time Near-Earth Object (NEO) tracking, orbital risk scoring, and automated planetary defense telemetry generation platform.</p>

  <p>
    <img src="[https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)" alt="Python" />
    <img src="[https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)" alt="Streamlit" />
    <img src="[https://img.shields.io/badge/NASA_CNEOS-API-0B3D91?style=for-the-badge&logo=nasa&logoColor=white](https://img.shields.io/badge/NASA_CNEOS-API-0B3D91?style=for-the-badge&logo=nasa&logoColor=white)" alt="NASA API" />
  </p>
</div>

---

## 🌌 About the Project

**OrbitalGuard** is an advanced web application designed to monitor, analyze, and assess the threat levels of Near-Earth Objects (NEOs) using official **NASA CNEOS** (Center for Near-Earth Object Studies) data.

In the face of potential space hazards, OrbitalGuard bridges raw astronomical data with actionable telemetry, offering scientists, space enthusiasts, and mission planners an intuitive command-center experience.

---

## ✨ Key Features

* **📡 Real-Time NASA Data Integration:** Automatically fetches live asteroid data for specific date ranges via NASA's NeoWs REST API.
* **🧮 Advanced Orbital Risk Scoring Algorithm:** Computes a custom **0–100 risk score** based on:
  * Asteroid diameter and estimated mass (calculated using a spherical model and standard rock density of $2.6\text{ g/cm}^3$).
  * Relative velocity and closest approach distance (in Lunar Distances and Kilometers).
  * Hazardous classification multipliers.
* **🔭 Interactive Drill-Down Detail Pages:** Click on any asteroid in the main list to view dedicated telemetry cards, trajectory simulations, and physical parameters.
* **🚨 NASA PDCO Telemetry Alert Generator:** Automatically packages High-Risk targets ($\text{Risk Score} \ge 70$) into structured **JSON alert formats** ready for transmission to the NASA Planetary Defense Coordination Office (PDCO).
* **🌐 IPv4 Network Optimization:** Built-in network connection handler to prevent hanging or latency issues caused by IPv6 routing bottlenecks during live demonstrations.

---

## 🛠️ Tech Stack

* **Python 3.11+**
* **Streamlit** (Interactive Web Framework)
* **Pandas & NumPy** (Data Processing & Mathematical Modeling)
* **Requests** (NASA API Communication)

---

## 📁 Project Structure

```text
OrbitalGuard/
├── api.py              # NASA API integration, mass calculations, and risk algorithm
├── app.py              # Streamlit user interface, dashboard metrics, and detail views
├── requirements.txt    # Project dependencies
├── .gitignore          # Ignored cache and environment files
└── README.md           # Project documentation
