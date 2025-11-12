# GPU_INSCY Quick Start Guide

This is a quick reference for getting GPU_INSCY running on Ubuntu. For detailed instructions, see [SETUP.md](SETUP.md).

## Prerequisites Check

```bash
# Check Ubuntu version
lsb_release -a

# Check if CUDA is installed
nvcc --version
nvidia-smi

# Check Python version (need 3.7+)
python3 --version
```

## Installation (5 Steps)

### 1. Install CUDA (if not installed)

```bash
# Visit: https://developer.nvidia.com/cuda-downloads
# Select: Linux → x86_64 → Ubuntu → Your Version → deb (local)
# Follow the installation commands provided

# Set environment variables
export CUDA_HOME=/usr/local/cuda
export PATH=$PATH:$CUDA_HOME/bin
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CUDA_HOME/lib64

# Make permanent
echo 'export CUDA_HOME=/usr/local/cuda' >> ~/.bashrc
echo 'export PATH=$PATH:$CUDA_HOME/bin' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CUDA_HOME/lib64' >> ~/.bashrc
```

### 2. Install Python Dependencies

```bash
cd GPU_INSCY
pip install -r requirements.txt
```

### 3. Verify Setup

```bash
# Check all dependencies
python verify_installation.py

# Test compilation (takes 1-2 minutes first time)
python test_compilation.py
```

### 4. Run Example

```bash
# Run small example (~5 minutes)
python run_example.py
```

### 5. Use in Your Code

```python
from GPU_INSCY.inscy import *

# Load data
X = load_vowel()  # or your own data

# Set parameters
neighborhood_size = 0.01
F = 1.0
num_obj = 8
min_size = int(X.shape[0] * 0.05)
r = 1.0
number_of_cells = 4

# Run algorithm
clusters = GPU_INSCY(X, neighborhood_size, F, num_obj, min_size, r,
                     number_of_cells=number_of_cells, rectangular=True)
```

## Common Issues

### Error: "CUDA_HOME environment variable is not set"
**Solution:** Install CUDA and set CUDA_HOME:
```bash
export CUDA_HOME=/usr/local/cuda
```

### Error: "nvcc: command not found"
**Solution:** Add CUDA to PATH:
```bash
export PATH=$PATH:/usr/local/cuda/bin
```

### Error: "ImportError: cannot import name 'load'"
**Solution:** Install PyTorch:
```bash
pip install torch
```

### CUDA not available
**Solution:** Install CUDA-enabled PyTorch:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

## Algorithms Available

1. **INSCY**: Original CPU-based algorithm
2. **GPU_INSCY**: Basic GPU-accelerated version
3. **GPU_INSCY_star**: Optimized GPU version
4. **GPU_INSCY_memory**: Memory-optimized GPU version

All use the same interface, just replace the function name:

```python
# CPU version
clusters = INSCY(X, neighborhood_size, F, num_obj, min_size, r)

# GPU versions
clusters = GPU_INSCY(X, neighborhood_size, F, num_obj, min_size, r)
clusters = GPU_INSCY_star(X, neighborhood_size, F, num_obj, min_size, r)
clusters = GPU_INSCY_memory(X, neighborhood_size, F, num_obj, min_size, r)
```

## Datasets Included

- **vowel.dat**: 990 points, 10 dimensions - Quick testing
- **glass.data**: 214 points, 11 dimensions - Quick testing  
- **pendigits.tra**: 7494 points, 16 dimensions - Larger dataset

## Performance Notes

- First run takes 1-2 minutes (JIT compilation)
- Subsequent runs are fast (compiled code is cached)
- GPU versions significantly faster than CPU (see example.png)
- Larger datasets benefit more from GPU acceleration

## Documentation

- **README.md**: Project overview
- **SETUP.md**: Detailed installation guide
- **INSTALLATION_STATUS.md**: Integration status and technical details
- **GPU_INSCY/README.md**: Original project documentation

## Support

- Original repository: https://github.com/jakobrj/GPU_INSCY
- Contact: jakobrj@cs.au.dk
- Paper: "GPU-INSCY: A GPU-Parallel Algorithm and Tree Structure for Efficient Density-based Subspace Clustering"
