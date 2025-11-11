# GPU_INSCY Setup Guide for Ubuntu

This guide explains how to set up and run the GPU_INSCY implementation on Ubuntu.

## Overview

GPU_INSCY is a GPU-accelerated implementation of the INSCY algorithm for density-based subspace clustering. The original implementation was developed and tested on Ubuntu 20.04 LTS with CUDA 10.1.

## Prerequisites

### System Requirements
- Ubuntu 20.04 LTS or newer (tested on Ubuntu 24.04 LTS)
- NVIDIA GPU with CUDA support (optional but recommended for GPU features)
- GCC/G++ compiler
- Python 3.7 or newer

### CUDA Support (Optional)
If you want to use GPU acceleration:
- NVIDIA GPU with CUDA Compute Capability 3.5 or higher
- CUDA Toolkit 10.1 or newer
- cuDNN (recommended)

Note: The code can compile and run without CUDA, but GPU-accelerated functions will not be available.

## Installation

### 1. Install System Dependencies

```bash
# Update package list
sudo apt-get update

# Install build essentials
sudo apt-get install -y build-essential

# Optional: Install CUDA (if not already installed)
# Follow NVIDIA's official CUDA installation guide for your Ubuntu version
# https://developer.nvidia.com/cuda-downloads
```

### 2. Install Python Dependencies

Navigate to the GPU_INSCY directory and install required packages:

```bash
cd GPU_INSCY
pip install -r requirements.txt
```

The required packages are:
- torch (PyTorch) - Handles CUDA compilation via JIT
- numpy
- ninja - Fast build system
- pandas
- matplotlib
- scikit-learn

### 3. Verify Installation

Run the test script to verify the installation:

```bash
python test.py
```

## Running Examples

### Quick Example

Run a small example with different INSCY variants:

```bash
cd GPU_INSCY
python run_example.py
```

This will:
1. Compile the C++/CUDA code (takes 1-2 minutes on first run)
2. Run INSCY, GPU-INSCY, GPU-INSCY*, and GPU-INSCY-memory on vowel and glass datasets
3. Display a plot comparing average running times

Expected runtime: ~5 minutes

### Available Datasets

The implementation includes three real-world datasets:
- **vowel**: Small dataset for quick testing
- **glass**: Small dataset for quick testing
- **pendigits**: Larger dataset (not included in quick example, ~8 hours for INSCY)

## Troubleshooting

### Compilation Issues

If you encounter compilation errors:

1. **Missing CUDA**: If you don't have an NVIDIA GPU or CUDA installed, the GPU functions will not work. Ensure PyTorch is installed with appropriate CUDA support or CPU-only version.

2. **GCC Version**: Ensure GCC/G++ is installed:
   ```bash
   gcc --version
   g++ --version
   ```

3. **PyTorch CUDA Version**: Check PyTorch CUDA compatibility:
   ```python
   import torch
   print(torch.cuda.is_available())
   print(torch.version.cuda)
   ```

### Runtime Issues

1. **Out of Memory**: Reduce dataset size or adjust parameters
2. **GPU Not Found**: Install CUDA-enabled PyTorch version
3. **Slow Performance**: Ensure GPU drivers are properly installed

## Usage in Python

```python
from GPU_INSCY.inscy import *

# Load data
X = load_vowel()  # or load_glass(), load_pendigits()

# Parameters
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

## Additional Information

For more details, see:
- Original README: `GPU_INSCY/README.md`
- Paper: "GPU-INSCY: A GPU-Parallel Algorithm and Tree Structure for Efficient Density-based Subspace Clustering"
- Contact: jakobrj@cs.au.dk

## Notes

- First run will take 1-2 minutes for JIT compilation
- Subsequent runs will be faster as compiled code is cached
- GPU features require CUDA-capable hardware and proper CUDA installation
- The implementation uses PyTorch's JIT compilation system for C++/CUDA code
