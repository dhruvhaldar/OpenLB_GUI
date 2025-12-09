# OpenLB Manager Deployment SOP

## 1. Prerequisites
*   **Operating System**: Linux (Ubuntu 20.04+ recommended) or MacOS.
*   **OpenLB**: Installed and available in the system path (or correctly referenced in case Makefiles).
*   **MPI**: OpenMPI or MPICH installed.
*   **Python**: v3.8+
*   **Node.js**: v18+ (for building the frontend)

## 2. Directory Structure
Ensure the following structure exists:

```
/path/to/project/
├── openlb-gui/
│   ├── backend/    # FastAPI server
│   └── frontend/   # React/Vite app
└── my_cases/       # Your OpenLB simulation cases
    ├── Aerospace/
    │   └── ...
    └── Biomedical/
        └── ...
```

## 3. Installation

### Backend
1.  Navigate to `openlb-gui/backend`.
2.  Create a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  Install dependencies:
    ```bash
    pip install fastapi uvicorn
    ```

### Frontend
1.  Navigate to `openlb-gui/frontend`.
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Build the frontend:
    ```bash
    npm run build
    ```
    This creates a `dist/` directory with static files.

## 4. Running the Application

### Option A: Development Mode (Two Terminals)
1.  **Backend**:
    ```bash
    cd openlb-gui/backend
    uvicorn main:app --reload --port 8000
    ```
2.  **Frontend**:
    ```bash
    cd openlb-gui/frontend
    npm run dev
    ```
    Open browser at `http://localhost:5173`.

### Option B: Production (Served by FastAPI)
To serve the frontend via the backend, update `main.py` to mount the `dist` folder:

1.  Add to `main.py`:
    ```python
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")
    ```
2.  Run the backend:
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000
    ```
3.  Open browser at `http://localhost:8000`.

## 5. Adding New Cases
1.  Create a new directory under `my_cases/<Domain>/<CaseName>`.
2.  Ensure it contains a valid `Makefile` with:
    *   `all`: Compiles the simulation.
    *   `run`: Executes the simulation.
3.  (Optional) Add `config.xml` for parameter editing.

## 6. Troubleshooting
*   **Build Fails**: Check the `Makefile` in the case directory manually.
*   **MPI Errors**: Ensure `mpirun` is in your PATH.
*   **Frontend Connection**: Check if the backend is running on port 8000.
