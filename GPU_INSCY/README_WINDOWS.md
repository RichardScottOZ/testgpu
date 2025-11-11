# GPU-INSCY for Windows 11

This is a Windows 11-compatible version of GPU-INSCY from the article "GPU-INSCY: A GPU-Parallel Algorithm and Tree Structure for Efficient Density-based Subspace Clustering".

## Original Repository

This code is based on https://github.com/jakobrj/GPU_INSCY

## Windows 11 Requirements

### Prerequisites

1. **CUDA Toolkit**: Install NVIDIA CUDA Toolkit 11.0 or later
   - Download from: https://developer.nvidia.com/cuda-downloads
   - Ensure `nvcc` is in your PATH

2. **Visual Studio**: Install Visual Studio 2019 or later with C++ build tools
   - Required components: "Desktop development with C++" workload
   - MSVC v142 or later
   - Windows 10 SDK

3. **Python**: Python 3.7 or later (64-bit)
   - Download from: https://www.python.org/downloads/

### Python Package Installation

Install required packages:

```bash
pip install -r requirements.txt
```

The important packages are:
- torch (with CUDA support)
- numpy
- ninja
- pandas
- matplotlib
- scikit-learn

### Installing PyTorch with CUDA Support

For Windows with CUDA 11.8:
```bash
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

For other CUDA versions, check: https://pytorch.org/get-started/locally/

## Differences from Original Implementation

### Path Handling
- All file paths now use `os.path.join()` for cross-platform compatibility
- Supports both forward slashes (/) and backslashes (\)

### System Command Execution
- Changed from `os.system()` to `subprocess.run()` for better Windows compatibility
- Better error handling and status checking

### Cluster Generator Binary
The `cluster_generator` binary from the original repository is a Linux ELF executable and **will not work on Windows**.

**Workarounds:**
1. **Recommended**: Use the `load_synt_gauss()` function instead of `load_synt()` - it's pure Python and cross-platform
2. Build `cluster_generator` from source for Windows (if source is available)
3. Generate data on a Linux system and copy the .dat files to Windows

Example using the pure Python alternative:
```python
from inscy import *

# Instead of load_synt():
# X = load_synt(d=15, n=8000, cl=2, re=0)

# Use load_synt_gauss():
X = load_synt_gauss(d=15, n=8000, cl=2, std=0.5, re=0)
```

## Running Examples

### Basic Test
```bash
python test.py
```

### Run Example (Note: Skips cluster_generator-dependent data)
```bash
python run_example.py
```

This will run INSCY, GPU-INSCY, GPU-INSCY*, and GPU-INSCY-memory on the vowel and glass datasets. Running time is approximately 5 minutes.

## Compilation

The C++/CUDA code is compiled automatically on first import using PyTorch's JIT compilation system. This typically takes 1-2 minutes.

### Compilation Requirements on Windows
- CUDA Toolkit must be installed and `nvcc` must be in PATH
- Visual Studio C++ compiler must be available
- The `ninja` build system (installed via pip)

### Troubleshooting Compilation Issues

**Issue**: "CUDA not found" or "nvcc not found"
- Verify CUDA installation: `nvcc --version`
- Add CUDA to PATH: `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.x\bin`

**Issue**: "Microsoft Visual C++ 14.0 or greater is required"
- Install Visual Studio with C++ build tools
- Restart your terminal after installation

**Issue**: Compilation errors about C++ standard
- Ensure you have Visual Studio 2019 or later
- PyTorch requires MSVC v142 or later

**Issue**: "ninja: build stopped" errors
- Try installing a specific ninja version: `pip install ninja==1.10.2`
- Clear PyTorch's cache: Delete `%USERPROFILE%\.cache\torch_extensions`

## Testing GPU Availability

Check if CUDA is available:
```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
```

## Performance Notes

- First run will be slower due to JIT compilation (1-2 minutes)
- Subsequent runs use cached compiled code
- GPU algorithms require a CUDA-capable NVIDIA GPU
- Performance depends on GPU memory and compute capability

## Datasets

The implementation includes three real-world datasets:
- `vowel.dat` - Vowel recognition data
- `glass.data` - Glass identification data  
- `pendigits.tra` - Pen-based handwritten digit recognition data

All datasets are cross-platform compatible.

## Known Limitations on Windows

1. The `cluster_generator` binary does not work on Windows (use `load_synt_gauss()` instead)
2. Compilation time may be longer on Windows compared to Linux
3. Some CUDA features may behave differently depending on driver version

## Contact

For issues with the original implementation: jakobrj@cs.au.dk

For Windows-specific issues with this refactored version, please open an issue in the repository.
