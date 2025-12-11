# OpenLB Manager GUI

OpenLB Manager is a lightweight, full-stack graphical user interface for the OpenLB C++ library. It allows users to scan, configure, compile, and run simulation cases without interacting directly with the terminal.

## 🚀 Features

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

*   **Backend**: A Python FastAPI server that handles file system operations, executes shell commands (`make`, `make run`), and serves the API.
*   **Frontend**: A React application built with Vite and styled with Tailwind CSS, communicating with the backend via REST API.

## 📋 Prerequisites

*   **Operating System**: Linux (Ubuntu 20.04+ recommended) or MacOS.
*   **OpenLB**: v1.6 or higher (installed and referenced in your Makefiles).
*   **MPI**: OpenMPI or MPICH (for parallel simulations).
*   **Python**: v3.8 or higher.
*   **Node.js**: v18 or higher (for building the frontend).
*   **uvicorn**: a python package for running fastapi servers.

## 🛠 Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd <repository-folder>
```

### 2. Backend Setup
Navigate to the backend directory and set up a virtual environment:

```bash
cd openlb-gui/backend
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn
```

### 3. Frontend Setup
Navigate to the frontend directory and install dependencies:

```bash
cd openlb-gui/frontend/
npm install
npm run build
```

## ▶️ Usage

### Option A: Development Mode
Run the backend and frontend in separate terminals for hot-reloading.

**Terminal 1 (Backend):**
```bash
cd openlb-gui/backend
source venv/bin/activate
uvicorn main:app --reload --port 8080
```

**Terminal 2 (Frontend):**
```bash
cd openlb-gui/frontend
npm run dev
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
*   **Frontend Connection Refused**: Make sure the backend is running on port 8000.
