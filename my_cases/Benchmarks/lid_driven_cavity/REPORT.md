# Lid Driven Cavity Simulation (2D)

## Description
This simulation models a standard 2D Lid Driven Cavity flow using the OpenLB Lattice Boltzmann Method (LBM) solver. The flow is driven by the top wall (lid) moving at a constant velocity, creating a primary vortex in the center of the cavity.

## Model Details
- **Lattice**: D2Q9 (2 Dimensions, 9 Discrete Velocities)
- **Dynamics**: BGK (Bhatnagar-Gross-Krook) Collision Model
- **Boundary Conditions**:
  - Top Wall: Velocity Boundary (Moving Lid)
  - Other Walls: No-Slip (Bounce Back)
- **Reynolds Number**: ~1000 (Controlled by Viscosity and Velocity)

## Parameters
- **Resolution**: 128x128 lattice nodes
- **Max Physical Time**: 10.0 seconds
- **Output Directory**: `tmp/`

## Results
The simulation generates:
1. **VTK Files** (`cavity2dvtk_*.vti`): For visualization in ParaView.
2. **Velocity Images** (`cavity2dimage_*.ppm`): Snapshots of the velocity magnitude field.
3. **Gnuplot Data** (`centerVelocityX_*.dat`): Velocity profiles for comparison with benchmark data (Ghia et al., 1982).

### Velocity Field (Snapshot)
![Velocity Field](tmp/cavity2dimage_iT12800.ppm)
*(Note: You may need to convert the PPM file to PNG or view it with an image viewer that supports PPM)*

## Running the Simulation
1. Compile the code:
   ```bash
   make
   ```
2. Run the simulation:
   ```bash
   make run
   ```
3. View the results in the `tmp/` directory.
