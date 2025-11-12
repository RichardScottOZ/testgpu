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

### CUDA Support (Required)
**IMPORTANT:** This implementation requires CUDA to compile and run. All algorithms (including the CPU-based INSCY) are compiled with CUDA.

Requirements:
- NVIDIA GPU with CUDA Compute Capability 3.5 or higher
- CUDA Toolkit 10.1 or newer (tested with 10.1, should work with newer versions)
- cuDNN (recommended)

**Without CUDA installed, the code will not compile.**

## Installation

### 1. Install System Dependencies

```bash
# Update package list
sudo apt-get update

# Install build essentials
sudo apt-get install -y build-essential
```

### 2. Install CUDA Toolkit

**CUDA is required for this project.** Follow these steps to install CUDA on Ubuntu:

#### Option A: Install via apt (Ubuntu 20.04/22.04/24.04)

```bash
# Add NVIDIA package repository (for Ubuntu 20.04/22.04)
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/12.0.0/local_installers/cuda-repo-ubuntu2004-12-0-local_12.0.0-525.60.13-1_amd64.deb
sudo dpkg -i cuda-repo-ubuntu2004-12-0-local_12.0.0-525.60.13-1_amd64.deb
sudo cp /var/cuda-repo-ubuntu2004-12-0-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update
sudo apt-get -y install cuda

# Set CUDA_HOME environment variable
echo 'export CUDA_HOME=/usr/local/cuda' >> ~/.bashrc
echo 'export PATH=$PATH:$CUDA_HOME/bin' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CUDA_HOME/lib64' >> ~/.bashrc
source ~/.bashrc
```

#### Option B: Follow official NVIDIA guide

Visit the official NVIDIA CUDA downloads page for your specific Ubuntu version:
https://developer.nvidia.com/cuda-downloads

Select:
- Operating System: Linux
- Architecture: x86_64
- Distribution: Ubuntu
- Version: Your Ubuntu version
- Installer Type: deb (local) recommended

Follow the installation instructions provided.

#### Verify CUDA Installation

```bash
# Check CUDA compiler
nvcc --version

# Check CUDA_HOME is set
echo $CUDA_HOME

# Verify GPU is detected
nvidia-smi
```

### 3. Install Python Dependencies

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

### 4. Verify Installation

First, run the verification script to check dependencies:

```bash
cd GPU_INSCY
python verify_installation.py
```

This will check:
- All Python packages are installed
- CUDA availability
- Data files are present
- Source files are present

Then test compilation:

```bash
python test_compilation.py
```

This will compile the C++/CUDA code (takes 1-2 minutes on first run) and verify it works.

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

1. **Missing CUDA**: The most common error is `CUDA_HOME environment variable is not set`. This means CUDA is not installed or not properly configured.
   
   Solutions:
   - Install CUDA Toolkit (see installation instructions above)
   - Set CUDA_HOME environment variable:
     ```bash
     export CUDA_HOME=/usr/local/cuda
     export PATH=$PATH:$CUDA_HOME/bin
     export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CUDA_HOME/lib64
     ```
   - Add these to ~/.bashrc to make permanent

2. **GCC Version**: Ensure GCC/G++ is installed and compatible with your CUDA version:
   ```bash
   gcc --version
   g++ --version
   ```
   
   Note: CUDA has specific GCC version requirements. Check CUDA compatibility matrix.

3. **PyTorch CUDA Version**: Check PyTorch CUDA compatibility:
   ```python
   import torch
   print(torch.cuda.is_available())
   print(torch.version.cuda)
   ```

4. **Cannot run without CUDA**: This implementation requires CUDA to compile. There is no CPU-only mode available because all source files include CUDA code.

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
