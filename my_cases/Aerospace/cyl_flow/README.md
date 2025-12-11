# Cylinder Flow Test Case

## Overview

This test case simulates laminar flow around a 2D cylinder using the OpenLB library. It demonstrates the use of:
- 2D D2Q9 lattice
- BGK dynamics
- Bouzidi boundary conditions for curved boundaries
- Poiseuille inflow profile

## Directory Structure

- `main.cpp`: The source code for the simulation.
- `Makefile`: Build configuration integrating with OpenLB.
- `config.xml`: Configuration file (optional, used by some setups).
- `tmp/`: Output directory for simulation results (VTK files, logs, images).

## Prerequisites

- OpenLB library (release 1.8.1) located at `../../../olb-release`.
- C++ compiler (g++ 9+).
- MPI (optional, for parallel execution).

## How to Build

Run the following command in this directory:

```bash
make
```

This will compile the `main.cpp` file and link it against the OpenLB library to create the `cyl_flow` executable.

## How to Run

Execute the simulation with:

```bash
make run
```

This command will:
1. Create the `tmp` directory if it doesn't exist.
2. Run the `cyl_flow` executable.

## Expected Output

The simulation will output logs to the console showing the progress of the time steps.
Results (VTK files, images) will be saved in the `tmp/` directory.

Example console output:
```
[main] prepareGeometry ... OK
[main] prepareLattice ... OK
[main] starting simulation...
[Timer] step 100 ...
...
```
