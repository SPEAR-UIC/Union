# Union
Workload Manager for Integration of Conceptual as An Online Workload for CODES


# Installation

### Installing Conceptual (mandatory)

Download Conceptual at https://ccsweb.lanl.gov/~pakin/software/conceptual/download.html (version 1.5.1 or greater)

```bash
tar xvf conceptual-1.5.1.tar.gz
cd conceptual-1.5.1
./configure --prefix=/path/to/conceptual/install
make
make install
cd ../
```

### Installing Boost-Python (currently mandatory, we may remove this soon)

Download boost at http://www.boost.org/users/download/ (version 1.68 or greater)

```bash
tar xvf boost_1_68_0.tar.gz
cd boost_1_68_0 
./bootstrap.sh --prefix=/path/to/boost/install  --with-libraries=python
./b2 install
cd ../
```

### Installing Union    
```bash
cd union
./prepare.sh
./configure --with-boost=/path/to/boost/install --with-conceptual=/path/to/conceptual/install --prefix=/path/to/union/install CC=mpicc CXX=mpicxx CFLAGS='-g -O0' CXXFLAGS='-g -O0'
make
make install
```

