# 🛰️ OrbitalGuard: NEO Risk & Planetary Defense Simulator

> **NASA Space Apps Challenge 2026 Submission**  
> Real-time Near-Earth Object (NEO) tracking, orbital risk scoring, and automated planetary defense telemetry generation platform.

---

## 🌟 About the Project

**OrbitalGuard** is an advanced web application designed to monitor, analyze, and assess the threat levels of Near-Earth Objects (NEOs) using official **NASA CNEOS (Center for Near Earth Object Studies)** data. 

In the face of potential space hazards, OrbitalGuard bridges raw astronomical data with actionable telemetry, offering scientists, space enthusiasts, and mission planners an intuitive command-center experience.

---

## 🚀 Key Features

* **Real-Time NASA Data Integration:** Automatically fetches live asteroid data for specific date ranges via NASA's REST API.
* **Advanced Orbital Risk Scoring Algorithm:** Computes a custom 0–100 risk score based on:
  * Asteroid diameter and estimated mass (calculated using a spherical model and standard rock density of $2.6\text{ g/cm}^3$).
  * Relative velocity and closest approach distance (in Lunar Distances and Kilometers).
  * Hazardous classification multiplier.
* **Interactive Drill-Down Detail Pages:** Click on any asteroid in the main list to view dedicated telemetry cards, trajectory simulations, and physical parameters.
* **NASA PDCO Telemetry Alert Generator:** Automatically packages high-risk targets (Risk Score $\ge 70$) into structured JSON alert formats ready for transmission to the **NASA Planetary Defense Coordination Office (PDCO)**.
* **IPv4 Network Optimization:** Built-in network connection handler to prevent hanging or latency issues caused by IPv6 routing bottlenecks during live demonstrations.

---

## 🛠️ Tech Stack

* **Python 3.11+**
* **Streamlit** (Interactive Web Framework)
* **Pandas & NumPy** (Data Processing & Mathematical Modeling)
* **Requests** (NASA API Communication)

---

## ⚙️ Installation & Local Setup

Follow these steps to run OrbitalGuard locally on your machine:

1. **Clone the repository:**
   ```bash
   ## 📂 Project Structure

```text
OrbitalGuard/
│
├── api.py          # NASA API integration, mass calculations, and risk algorithms
├── app.py          # Streamlit user interface, dashboard metrics, and detail views
└── README.md       # Project documentation

👥 Team
Developed with passion for the NASA Space Apps Challenge 2026.

Burak Doğan
Burak Erşahin


git clone [https://github.com/burakdgn000-max/OrbitalGurad.git](https://github.com/burakdgn000-max/OrbitalGurad.git)
cd OrbitalGurad
