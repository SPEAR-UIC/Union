# Union
Workload Manager for Integration of Conceptual as an Online Workload for CODES


# Installation

### Installing Conceptual (mandatory)

Download Conceptual at https://ccsweb.lanl.gov/~pakin/software/conceptual/download.html (version 1.5.1 or greater)

```bash
tar xvf conceptual-1.5.1.tar.gz
cd conceptual-1.5.1
./configure --prefix=/path/to/conceptual/install
make
make install
```

### Installing Union    
```bash
cd union
./prepare.sh
./configure --with-conceptual=/path/to/conceptual/install --with-conceptual-src=/path/to/conceptual --prefix=/path/to/union/install CC=mpicc CXX=mpicxx
make
make install
```

#### Build Process

During the build process (`make`), all `.ncptl` benchmark files located in the `translator/` directory are automatically translated into `.c` files using the `translate.py` script.

These translated benchmark files are then compiled and linked into the Union library.

You do not need to manually translate or include the benchmarks, as this process is automatically handled during the build.


## CODES Installation

### Installing Boost-Python

```bash
curl -L https://archives.boost.io/release/1.87.0/source/boost_1_87_0.tar.gz -o boost_1_87_0.tar.gz
tar xvf boost_1_87_0.tar.gz
cd boost_1_87_0 
./bootstrap.sh --prefix=/path/to/boost/install  --with-libraries=python
./b2 install
```

### Installing ROSS

```bash
git clone https://github.com/ross-org/ross --depth=20 --branch=at_gvt_arbitrary_function
cd ross
mkdir build
cd build
cmake .. -DROSS_BUILD_MODELS=ON -DCMAKE_INSTALL_PREFIX=path/to/ross/install -DCMAKE_C_COMPILER=mpicc -DCMAKE_CXX_COMPILER=mpicxx -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_FLAGS="-g -Wall"
make
make install
```

### Installing Argobots

```bash
git clone https://github.com/pmodels/argobots --depth=1
cd argobots
./autogen.sh
./configure --prefix=/path/to/argobots/install
make
make install
```

### Installing SWM workloads

```bash
git clone https://github.com/codes-org/SWM-workloads.git
cd SWM-workloads/swm
./prepare.sh
./configure --with-boost=/path/to/boost/install --prefix=/path/to/swm/install CC=mpicc CXX=mpicxx
make
make install
```

### Installing CODES (kronos-union branch)

```bash
git clone https://github.com/codes-org/codes --branch=kronos-union
cd codes
./prepare.sh
mkdir build
cd build
../configure --with-online=true --with-boost=/path/to/boost/install PKG_CONFIG_PATH=/home/path/to/argobots/install/lib/pkgconfig:/path/to/ross/install/lib/pkgconfig:/path/to/union/install/lib/pkgconfig:/path/to/swm/install/lib/pkgconfig --with-union=true --prefix=/path/to/codes/install CC=mpicc CXX=mpicxx 
make
make install
```


# Run Test Simulations with CODES

The `test` directory contains all the necessary configuration files to run the test simulation.

All benchmarks located in `union/src/benchmarks/` are compatible with the CODES online framework and can be simulated through it.

To simulate a specific benchmark, set the `--workload_name` parameter using the format `conceptual-[benchmark_name]`.

In `/path/to/union/install/share`, you can modify the `conceptual.json` file to configure parameters for the benchmarks.

### Running the simulation in sequential mode

```bash
cd union/test/
/path/to/codes/install/bin/model-net-mpi-replay --sync=1 --workload_type=conc-online --lp-io-use-suffix=1 --workload_name=conceptual-jacobi3d --num_net_traces=64 --alloc_file=node_alloc.conf  --lp-io-dir=outputdir -- df1d-72-adp.conf 
```

### Running the simulation in optimistic mode

```bash
cd union/test/
mpirun -np 2 /path/to/codes/install/bin/model-net-mpi-replay --sync=1 --workload_type=conc-online --lp-io-use-suffix=1 --workload_name=conceptual-jacobi3d --num_net_traces=64 --alloc_file=node_alloc.conf  --lp-io-dir=outputdir -- df1d-72-adp.conf 
```

