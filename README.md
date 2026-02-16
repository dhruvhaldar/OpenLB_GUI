# OpenLB Manager GUI

[![GitHub license](https://img.shields.io/github/license/dhruvhaldar/OpenLB_GUI)](https://github.com/dhruvhaldar/OpenLB_GUI/blob/main/LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/dhruvhaldar/OpenLB_GUI)](https://github.com/dhruvhaldar/OpenLB_GUI/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/dhruvhaldar/OpenLB_GUI)](https://github.com/dhruvhaldar/OpenLB_GUI/commits/main)
[![bun](https://img.shields.io/badge/bun-1.3.9-black?style=flat&logo=bun&logoColor=white)](https://bun.sh)
[![fastapi](https://img.shields.io/badge/fastapi-0.129.0-purple?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![python](https://img.shields.io/badge/python-3.8+-blue?style=flat&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![tailwind](https://img.shields.io/badge/tailwind-3.3.0-blue?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![pytest](https://img.shields.io/badge/pytest-9.0.2-orange?style=flat&logo=pytest&logoColor=white)](https://pytest.org/)
[![docker](https://img.shields.io/badge/docker-27.1.1-blue?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)

OpenLB Manager is a lightweight, full-stack graphical user interface for the OpenLB C++ library. It allows users to scan, configure, compile, and run simulation cases without interacting directly with the terminal.

## Features

*   **Case Scanner**: Automatically detects simulation cases (based on `Makefile` presence) in the `my_cases` directory.
*   **GUI Wrapper**: A modern web interface (React + Tailwind CSS) to interact with the build system.
*   **One-Click Build & Run**: Compile and execute simulations directly from the browser.
*   **Configuration Editor**: Edit `config.xml` parameters for each case on the fly.
*   **Real-time Output**: View build and simulation logs in the integrated terminal window.
*   **Modular Architecture**: clearly separated Backend (Python/FastAPI) and Frontend (TypeScript/React).

## 🏗 Architecture

The project is organized into the following structure:

```
.
├── openlb-gui/
│   ├── backend/    # FastAPI server (Python)
│   │   ├── main.py
│   │   └── ...
│   └── frontend/   # React application (Vite + Tailwind)
│       ├── src/
│       └── ...
└── my_cases/       # Simulation cases directory
    ├── Aerospace/
    │   └── cyl_flow/
    └── Biomedical/
        └── aorta_sim/
```

*   **Backend**: A Python FastAPI server that handles file system operations, executes build commands via Docker, and serves the API.
*   **Frontend**: A React application built with Vite and styled with Tailwind CSS, communicating with the backend via REST API.

## 📋 Prerequisites

*   **Docker Desktop**: Required for building and running OpenLB simulations.
*   **Python**: v3.8 or higher.
*   **Bun**: v1.0 or higher (for building the frontend).

## 🛠 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/dhruvhaldar/OpenLB_GUI.git
cd OpenLB_GUI
```

### 2. Build the OpenLB Docker Image
```bash
docker build -t openlb-gui:latest .
```

### 3. Backend Setup
Navigate to the backend directory and set up a virtual environment:

```bash
cd openlb-gui/backend
python3 -m venv venv
```

For Linux/Unix:
```bash
source venv/bin/activate
pip install fastapi uvicorn
```

For Windows:
```powershell
.\venv\Scripts\Activate.ps1
pip install fastapi uvicorn
```

### 4. Frontend Setup
Install bun 
for your platform:

For Linux/Unix:
```bash
curl -fsSL https://bun.sh/install | bash
```

For Windows:
```powershell
powershell -c "irm bun.sh/install.ps1 | iex"
```


Navigate to the frontend directory and install dependencies:

```bash
cd openlb-gui/frontend/
bun install
bun run build
```

## ▶️ Usage

### Option A: Development Mode
Run the backend and frontend in separate terminals for hot-reloading.

**Terminal 1 (Backend):**
```bash
cd openlb-gui/backend
source venv/bin/activate
uvicorn main:app --reload --port 3001
```

**Terminal 2 (Frontend):**
```bash
cd openlb-gui/frontend
bun run dev
```
Open your browser at `http://localhost:5173`.

### Option B: Production Mode
Serve the built frontend static files directly from the backend. (Note: Requires configuring `StaticFiles` in `main.py` pointing to `frontend/dist`).

## 📂 Adding New Cases

To add a new simulation case:

1.  Create a new directory under `my_cases/` (e.g., `my_cases/Energy/wind_turbine`).
2.  Add a **Makefile** in that directory. It must support:
    *   `make all`: To compile the code.
    *   `make run`: To execute the binary.
3.  (Optional) Add a `config.xml` file to enable parameter editing in the GUI.

Example structure:
```
my_cases/
└── Energy/
    └── wind_turbine/
        ├── Makefile
        ├── config.xml
        └── main.cpp
```

## ❓ Troubleshooting

*   **"Case path not found"**: Ensure your `my_cases` directory is in the project root.
*   **Build Failures**: Check the `Makefile` in the specific case directory by running `make` manually in the terminal.
*   **MPI Errors**: Ensure `mpirun` is available in your system path.
*   **Frontend Connection Refused**: Make sure the backend is running on port 3001.
