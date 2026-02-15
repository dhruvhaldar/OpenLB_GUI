/*  Lattice Boltzmann sample, written in C++, using the OpenLB
 *  library
 *
 *  Copyright (C) 2006 - 2012, 2025 Mathias J. Krause, Jonas Fietz,
 *  Jonas Latt, Jonas Kratzke, Yuji (Sam) Shimojima
 *  E-mail contact: info@openlb.net
 *  The most recent release of OpenLB can be downloaded at
 *  <http://www.openlb.net/>
 *
 *  This program is free software; you can redistribute it and/or
 *  modify it under the terms of the GNU General Public License
 *  as published by the Free Software Foundation; either version 2
 *  of the License, or (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public
 *  License along with this program; if not, write to the Free
 *  Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
 *  Boston, MA  02110-1301, USA.
 */

/* cavity2d.cpp:
 * This example illustrates a flow in a cuboid, lid-driven cavity.
 * It also shows how to use the XML parameter files and has an
 * example description file for OpenGPI. This version is for parallel
 * use. A version for sequential use is also available.
 */

#include "olb.h"

using namespace olb;
using namespace olb::names;

// === Step 1: Declarations ===
using MyCase = Case<NavierStokes, Lattice<double, descriptors::D2Q9<>>>;
namespace olb::parameters {

struct RESIDUUM : public descriptors::FIELD_BASE<1> {};                    // Residuum for convergence check
struct PHYS_LOG_ITER_T : public descriptors::FIELD_BASE<1> {};             // physical time interval for loging
struct PHYS_IMAGE_ITER_T : public descriptors::FIELD_BASE<1> {};           // physical time interval for saving images
struct PHYS_GNUPLOT_ITER_T : public descriptors::FIELD_BASE<1> {};         // physical time interval for saving gnuplot
struct TIMER_PRINT_MODE : public descriptors::TYPED_FIELD_BASE<int, 1> {}; // Timer print mode

} // namespace olb::parameters

/// @brief Create a simulation mesh, based on user-specific geometry
/// @return An instance of Mesh, which keeps the relevant information
Mesh<MyCase::value_t, MyCase::d> createMesh(MyCase::ParametersD& parameters)
{
  using T                 = MyCase::value_t;
  const T      physDeltaX = parameters.get<parameters::PHYS_DELTA_X>();
  const T      length = parameters.get<parameters::PHYS_CHAR_LENGTH>(); // length of the cavity in x- and z-direction
  Vector<T, 2> origin((T)0);
  Vector<T, 2> extend(length);
  IndicatorCuboid2D<T> cuboid(extend, origin);

  Mesh<T, MyCase::d> mesh(cuboid, physDeltaX, singleton::mpi().getSize());
  mesh.setOverlap(parameters.get<parameters::OVERLAP>());
  return mesh;
}

/// @brief Set material numbers for different parts of the domain
/// @param myCase The Case instance which keeps the simulation data
/// @note The material numbers will be used to assign physics to lattice nodes
void prepareGeometry(MyCase& myCase)
{
  OstreamManager clout(std::cout, "prepareGeometry");
  clout << "Prepare Geometry ..." << std::endl;
  using T          = MyCase::value_t;
  auto& sGeometry  = myCase.getGeometry();
  auto& parameters = myCase.getParameters();

  sGeometry.rename(0, 2);
  sGeometry.rename(2, 1, {1, 1});
  sGeometry.clean();

  T                    eps = parameters.get<parameters::PHYS_DELTA_X>();
  Vector<T, 2>         extend((T)1 + (T)2 * eps, (T)2 * eps);
  Vector<T, 2>         origin((T)0 - eps, (T)1 - eps);
  IndicatorCuboid2D<T> lid(extend, origin);
  // Set material number for lid
  sGeometry.rename(2, 3, 1, lid);

  // Removes all not needed boundary voxels outside the surface
  sGeometry.clean();
  // Removes all not needed boundary voxels inside the surface
  sGeometry.innerClean();
  sGeometry.checkForErrors();
  sGeometry.getStatistics().print();
  clout << "Prepare Geometry ... OK" << std::endl;
}

/// @brief Set lattice dynamics
/// @param myCase The Case instance which keeps the simulation data
void prepareLattice(MyCase& myCase)
{
  OstreamManager clout(std::cout, "prepareLattice");
  clout << "Prepare Lattice ..." << std::endl;
  using T          = MyCase::value_t;
  auto& sGeometry  = myCase.getGeometry();
  auto& sLattice   = myCase.getLattice(NavierStokes {});
  auto& parameters = myCase.getParameters();
  clout << "Prepare Lattice ..." << std::endl;
  {
    using namespace olb::parameters;
    sLattice.setUnitConverter<UnitConverterFromResolutionAndRelaxationTime<T, MyCase::descriptor_t_of<NavierStokes>>>(
        parameters.get<RESOLUTION>(), // resolution: number of voxels per charPhysL
        parameters
            .get<LATTICE_RELAXATION_TIME>(), // latticeRelaxationTime: relaxation time, have to be greater than 0.5!
        parameters.get<PHYS_CHAR_LENGTH>(),  // charPhysLength: reference length of simulation geometry
        parameters.get<
            PHYS_CHAR_VELOCITY>(), // charPhysVelocity: maximal/highest expected velocity during simulation in __m / s__
        parameters.get<PHYS_CHAR_VISCOSITY>(), // physViscosity: physical kinematic viscosity in __m^2 / s__
        parameters.get<PHYS_CHAR_DENSITY>()    // physDensity: physical density in __kg / m^3__
    );
  }
  // Prints the converter log as console output
  sLattice.getUnitConverter().print();
  // Writes the converter log in a file
  sLattice.getUnitConverter().write("cavity3d");

  // Material=1 -->bulk dynamics
  dynamics::set<ConstRhoBGKdynamics>(sLattice, sGeometry.getMaterialIndicator(1));

  // Material=2,3 -->bulk dynamics, velocity boundary
  boundary::set<boundary::InterpolatedVelocity>(sLattice, sGeometry, 2);
  boundary::set<boundary::InterpolatedVelocity>(sLattice, sGeometry, 3);
  clout << "Prepare Lattice ... OK" << std::endl;
}

/// Set initial condition for primal variables (velocity and density)
/// @param myCase The Case instance which keeps the simulation data
/// @note Be careful: initial values have to be set using lattice units
void setInitialValues(MyCase& myCase)
{
  OstreamManager clout(std::cout, "Initialization");
  clout << "lattice initialization ..." << std::endl;

  using T = MyCase::value_t;
  auto& sLattice = myCase.getLattice(NavierStokes {});
  auto& sGeometry = myCase.getGeometry();

  AnalyticalConst2D<T, T> uTop(sLattice.getUnitConverter().getCharPhysVelocity(), 0);
  momenta::setVelocity(sLattice, sGeometry.getMaterialIndicator(3), uTop);

  const T omega = sLattice.getUnitConverter().getLatticeRelaxationFrequency();
  sLattice.setParameter<descriptors::OMEGA>(omega);

  // Make the lattice ready for simulation
  sLattice.initialize();
  clout << "Initialization ... OK" << std::endl;
}

/// Update boundary values at times (and external fields, if they exist)
/// @param myCase The Case instance which keeps the simulation data
/// @param iT The time step
/// @note Be careful: boundary values have to be set using lattice units
void setTemporalValues(MyCase& myCase, std::size_t iT) {}

void getResults(MyCase& myCase, std::size_t iT, util::Timer<MyCase::value_t>& timer)
{
  OstreamManager clout(std::cout, "getResults");
  using T                    = MyCase::value_t;
  auto&       sLattice       = myCase.getLattice(NavierStokes {});
  const auto& converter      = sLattice.getUnitConverter();
  auto&       sGeometry      = myCase.getGeometry();
  auto&       parameters     = myCase.getParameters();
  auto        logT           = parameters.get<parameters::PHYS_LOG_ITER_T>();
  auto        imSave         = parameters.get<parameters::PHYS_IMAGE_ITER_T>();
  auto        vtkSave        = parameters.get<parameters::PHYS_VTK_ITER_T>();
  auto        gnuplotSave    = parameters.get<parameters::PHYS_GNUPLOT_ITER_T>();
  auto        timerPrintMode = parameters.get<parameters::TIMER_PRINT_MODE>();
  const bool converged = parameters.get<parameters::CONVERGED>();

  SuperVTMwriter2D<T> vtmWriter("cavity2dvtk");

  if (iT == 0) {
    // Writes the geometry, cuboid no. and rank no. as vti file for visualization
    SuperLatticeCuboid2D                                                   cuboid(sLattice);
    SuperLatticeRank2D                                                     rank(sLattice);
    SuperLatticeDiscreteNormal2D<T, MyCase::descriptor_t_of<NavierStokes>> discreteNormal(
        sLattice, sGeometry, sGeometry.getMaterialIndicator({2, 3}));
    SuperLatticeDiscreteNormalType2D<T, MyCase::descriptor_t_of<NavierStokes>> discreteNormalType(
        sLattice, sGeometry, sGeometry.getMaterialIndicator({2, 3}));

    vtmWriter.write(cuboid);
    vtmWriter.write(rank);
    vtmWriter.write(discreteNormal);
    vtmWriter.write(discreteNormalType);
    vtmWriter.createMasterFile();
  }

  // Get statistics
  if (iT % converter.getLatticeTime(logT) == 0 || converged) {
    sLattice.getStatistics().print(iT, converter.getPhysTime(iT));
    timer.print(iT, timerPrintMode);
  }

  // Writes the VTK files
  if ((iT % converter.getLatticeTime(vtkSave) == 0 && iT > 0) || converged) {
    sLattice.setProcessingContext(ProcessingContext::Evaluation);

    SuperLatticePhysVelocity2D<T, MyCase::descriptor_t_of<NavierStokes>> velocity(sLattice, converter);
    SuperLatticePhysPressure2D<T, MyCase::descriptor_t_of<NavierStokes>> pressure(sLattice, converter);

    vtmWriter.addFunctor(velocity);
    vtmWriter.addFunctor(pressure);
    vtmWriter.write(iT);
  }

  // Writes the Gif files
  if ((iT % converter.getLatticeTime(imSave) == 0 && iT > 0) || converged) {
    SuperLatticePhysVelocity2D                                  velocity(sLattice, converter);
    SuperEuklidNorm2D<T, MyCase::descriptor_t_of<NavierStokes>> normVel(velocity);
    BlockReduction2D2D<T> planeReduction(normVel, 600, BlockDataSyncMode::ReduceOnly);
    // write output of velocity as JPEG
    heatmap::write(planeReduction, iT);
  }

  // Output for x-velocity along y-position at the last time step
  //if ( iT == converter.getLatticeTime( maxPhysT ) || converged ) {
  if ((iT % converter.getLatticeTime(gnuplotSave) == 0 && iT > 0) || converged) {
    // Gives access to velocity information on lattice
    SuperLatticePhysVelocity2D velocityField(sLattice, converter);
    // Interpolation functor with velocityField information
    AnalyticalFfromSuperF2D<T> interpolation(velocityField, true, 1);

    Vector<T, 17> y_coord({128, 125, 124, 123, 122, 109, 94, 79, 64, 58, 36, 22, 13, 9, 8, 7, 0});
    // Ghia, Ghia and Shin, 1982: "High-Re Solutions for Incompressible Flow Using the Navier-Stokes Equations and a Multigrid Method";  Table 1
    Vector<T, 17> vel_ghia_RE1000({1.0, 0.65928, 0.57492, 0.51117, 0.46604, 0.33304, 0.18719, 0.05702, -0.06080,
                                   -0.10648, -0.27805, -0.38289, -0.29730, -0.22220, -0.20196, -0.18109, 0.0});
    Vector<T, 17> vel_ghia_RE100({1.0, 0.84123, 0.78871, 0.73722, 0.68717, 0.23151, 0.00332, -0.13641, -0.20581,
                                  -0.21090, -0.15662, -0.10150, -0.06434, -0.04775, -0.04192, -0.03717, 0.0});
    Vector<T, 17> vel_simulation;

    // Gnuplot interface to create plots
    Gnuplot<T> gplot("centerVelocityX_iT" + std::to_string(iT));
    // Define comparison values
    Vector<T, 17> comparison = vel_ghia_RE1000;

    for (int nY = 0; nY < 17; ++nY) {
      // 17 data points evenly distributed between 0 and 1 (height)
      T position[2] = {0.5, y_coord[nY] / T(128)};
      T velocity[2] = {T(), T()};
      // Interpolate velocityField at "position" and save it in "velocity"
      interpolation(velocity, position);
      // Save value of velocity (in x-direction) in "vel_simulation" for every position "nY"
      vel_simulation[nY] = velocity[0];
      // Set data for plot output
      gplot.setData(position[1], {vel_simulation[nY], comparison[nY]}, {"simulated", "Ghia"});
    }
    // Create PNG file
    gplot.writePNG();
    // Console output with results
    clout << "absoluteErrorL2(line)=" << norm(vel_simulation - comparison) / 17.
          << "; relativeErrorL2(line)=" << norm(vel_simulation - comparison) / norm(comparison) << std::endl;
  }
}

void simulate(MyCase& myCase)
{
  OstreamManager clout(std::cout, "Time marching");
  using T = MyCase::value_t;

  auto& sLattice   = myCase.getLattice(NavierStokes {});
  auto& parameters = myCase.getParameters();
  auto  maxPhysT   = parameters.get<parameters::MAX_PHYS_T>();

  auto maxLatticeT = sLattice.getUnitConverter().getLatticeTime(maxPhysT);

  util::ValueTracer<T> converge(sLattice.getUnitConverter().getLatticeTime(parameters.get<parameters::CONV_ITER>()),
                                parameters.get<parameters::RESIDUUM>());

  util::Timer<T> timer(maxLatticeT, myCase.getGeometry().getStatistics().getNvoxel());

  clout << "starting simulation..." << std::endl;
  timer.start();
  for (std::size_t iT = 0; iT <= maxLatticeT; ++iT) {
    if (converge.hasConverged()) {
      parameters.set<parameters::CONVERGED>(true);
      clout << "Simulation converged." << std::endl;
      getResults(myCase, iT, timer);

      break;
    }

    setTemporalValues(myCase, iT);

    sLattice.collideAndStream();

    getResults(myCase, iT, timer);

    converge.takeValue(sLattice.getStatistics().getAverageEnergy(), true);
  }
  sLattice.setProcessingContext(ProcessingContext::Evaluation);
  timer.stop();
  timer.printSummary();
}

int main(int argc, char* argv[])
{

  initialize(&argc, &argv);
  OstreamManager clout(std::cout, "main");

  std::string fName("config.xml");
  XMLreader   config(fName);
  std::string olbdir, outputdir;
  config["Application"]["OlbDir"].read(olbdir);
  config["Output"]["OutputDir"].read(outputdir);
  singleton::directories().setOlbDir(olbdir);
  singleton::directories().setOutputDir(outputdir);
  /// === Step 2: Set Parameters ===
  MyCase::ParametersD myCaseParameters;
  {
    using namespace olb::parameters;
    using T = MyCase::value_t;
    myCaseParameters.set<RESOLUTION>(config["Application"]["Discretization"]["Resolution"].get<int>());
    myCaseParameters.set<LATTICE_RELAXATION_TIME>(
        config["Application"]["Discretization"]["LatticeRelaxationTime"].get<T>());
    myCaseParameters.set<PHYS_CHAR_LENGTH>(config["Application"]["PhysParameters"]["CharPhysLength"].get<T>());
    myCaseParameters.set<PHYS_CHAR_VELOCITY>(config["Application"]["PhysParameters"]["CharPhysVelocity"].get<T>());
    myCaseParameters.set<PHYS_CHAR_VISCOSITY>(config["Application"]["PhysParameters"]["PhysViscosity"].get<T>());
    myCaseParameters.set<PHYS_CHAR_DENSITY>(config["Application"]["PhysParameters"]["PhysDensity"].get<T>());
    myCaseParameters.set<MAX_PHYS_T>(config["Application"]["PhysParameters"]["PhysMaxTime"].get<T>());
    myCaseParameters.set<CONV_ITER>(config["Application"]["ConvergenceCheck"]["Interval"].get<T>());
    myCaseParameters.set<RESIDUUM>(config["Application"]["ConvergenceCheck"]["Residuum"].get<T>());
    myCaseParameters.set<PHYS_DELTA_X>([&] {
      return myCaseParameters.get<PHYS_CHAR_LENGTH>() / myCaseParameters.get<RESOLUTION>();
    });
    T vtkIter, logIter, imageIter, gnuplotIter;
    int timerPrintMode;
    config["Output"]["VisualizationVTK"]["SaveTime"].read<T>(vtkIter);
    config["Output"]["Log"]["SaveTime"].read<T>(logIter);
    config["Output"]["VisualizationImages"]["SaveTime"].read<T>(imageIter);
    config["Output"]["VisualizationGnuplot"]["SaveTime"].read<T>(gnuplotIter);
    config["Output"]["Timer"]["PrintMode"].read<int>(timerPrintMode);

    myCaseParameters.set<PHYS_VTK_ITER_T>(vtkIter);
    myCaseParameters.set<PHYS_LOG_ITER_T>(logIter);
    myCaseParameters.set<PHYS_IMAGE_ITER_T>(imageIter);
    myCaseParameters.set<PHYS_GNUPLOT_ITER_T>(gnuplotIter);
    myCaseParameters.set<TIMER_PRINT_MODE>(timerPrintMode);
  }

  myCaseParameters.fromCLI(argc, argv);
  /// === Step 3: Create Mesh ===
  Mesh<MyCase::value_t, MyCase::d> mesh = createMesh(myCaseParameters);
  /// === Step 4: Create Case ===
  MyCase myCase(myCaseParameters, mesh);

  /// === Step 5: Prepare Geometry ===
  prepareGeometry(myCase);
  /// === Step 6: Prepare Lattice ===
  prepareLattice(myCase);

  /// === Step 7: Definition of Initial, Boundary Values, and Fields ===
  setInitialValues(myCase);

  /// === Step 8: Simulate ===
  simulate(myCase);

  return 0;
}
