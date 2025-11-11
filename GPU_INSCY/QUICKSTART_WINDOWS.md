# Quick Start Guide for Windows 11

This guide will help you get GPU-INSCY running on Windows 11 in just a few steps.

## Prerequisites Checklist

Before starting, make sure you have:

- [ ] NVIDIA GPU with CUDA support (GTX 10-series or newer recommended)
- [ ] Windows 11 (also works on Windows 10)
- [ ] At least 8GB RAM
- [ ] 5GB free disk space

## Step-by-Step Installation

### 1. Install CUDA Toolkit

1. Download CUDA Toolkit from: https://developer.nvidia.com/cuda-downloads
2. Select Windows → x86_64 → your Windows version → exe (network)
3. Run the installer and follow the prompts
4. Default installation path: `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.x`

**Verify installation:**
```cmd
nvcc --version
```

### 2. Install Visual Studio with C++ Support

1. Download Visual Studio 2022 Community (free) from: https://visualstudio.microsoft.com/
2. During installation, select "Desktop development with C++"
3. Required components (automatically selected):
   - MSVC v143 or later
   - Windows 10/11 SDK
   - C++ CMake tools

**Note**: Installation takes ~10GB and may take 30-60 minutes.

### 3. Install Python

1. Download Python 3.9 or later from: https://www.python.org/downloads/
2. During installation, check "Add Python to PATH"
3. Select "Install Now"

**Verify installation:**
```cmd
python --version
pip --version
```

### 4. Install PyTorch with CUDA

Open Command Prompt or PowerShell and run:

```cmd
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

This installs PyTorch with CUDA 11.8 support. For other CUDA versions, visit: https://pytorch.org/get-started/locally/

### 5. Install GPU-INSCY Dependencies

Navigate to the GPU_INSCY directory:
```cmd
cd path\to\testgpu\GPU_INSCY
```

Install required packages:
```cmd
pip install -r requirements.txt
```

### 6. Verify Your Setup

Run the setup checker:
```cmd
python check_windows_setup.py
```

This will check all requirements and tell you if anything is missing.

## Running Your First Example

### Option 1: Windows-Specific Example (Recommended)

```cmd
python run_example_windows.py
```

This script:
- Checks your CUDA setup
- Compiles the C++/CUDA code (1-2 minutes on first run)
- Runs benchmarks on two datasets
- Creates a performance comparison plot

**Expected output:**
- Compilation takes 1-2 minutes on first run
- Benchmark takes 3-5 minutes total
- Creates `example_windows.png` with results

### Option 2: Original Example

```cmd
python run_example.py
```

**Note**: This may fail on Windows if it tries to use the Linux-only `cluster_generator` binary.

### Option 3: Simple Test

Create a file `my_test.py`:

```python
from inscy import *
import torch

# Check CUDA
print(f"CUDA available: {torch.cuda.is_available()}")

# Load dataset
print("Loading data...")
X = load_glass()
print(f"Dataset shape: {X.shape}")

# Run GPU-INSCY
print("Running GPU-INSCY...")
results = GPU_INSCY_memory(X, 
                          neighborhood_size=0.01,
                          F=1.0,
                          num_obj=8,
                          min_size=int(X.shape[0] * 0.05),
                          r=1.0,
                          number_of_cells=4,
                          rectangular=True)

print(f"Found {len(results[0])} clusters")
print("Success!")
```

Run it:
```cmd
python my_test.py
```

## Troubleshooting

### Compilation Fails

**Error: "CUDA not found"**
- Solution: Add CUDA to PATH:
  ```cmd
  set PATH=%PATH%;C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin
  ```

**Error: "Microsoft Visual C++ 14.0 or greater is required"**
- Solution: Install Visual Studio with C++ tools (see Step 2)

**Error: "ninja: build stopped"**
- Solution 1: Clear cache and retry:
  ```cmd
  rmdir /s /q %USERPROFILE%\.cache\torch_extensions
  ```
- Solution 2: Install specific ninja version:
  ```cmd
  pip install ninja==1.10.2
  ```

### CUDA Not Available in PyTorch

**Issue**: `torch.cuda.is_available()` returns False

Solutions:
1. Check GPU drivers: Update to latest NVIDIA drivers
2. Reinstall PyTorch with CUDA:
   ```cmd
   pip uninstall torch torchvision torchaudio
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```
3. Verify NVIDIA GPU is detected:
   ```cmd
   nvidia-smi
   ```

### Import Errors

**Error: "No module named 'inscy'"**
- Solution: Make sure you're in the GPU_INSCY directory:
  ```cmd
  cd path\to\testgpu\GPU_INSCY
  python run_example_windows.py
  ```

### Slow Performance

**Issue**: GPU algorithms are slower than expected

Possible causes:
1. First run always slow (compiling code)
2. GPU memory insufficient - close other GPU applications
3. Using integrated GPU instead of discrete GPU
4. Thermal throttling - check GPU temperature with `nvidia-smi`

## Data Generation on Windows

The Linux `cluster_generator` binary does not work on Windows.

**Instead, use the pure Python alternative:**

```python
from inscy import *

# Don't use this (requires cluster_generator):
# X = load_synt(d=15, n=8000, cl=2, re=0)

# Use this instead (pure Python, works on Windows):
X = load_synt_gauss(d=15, n=8000, cl=2, std=0.5, re=0)
```

Both generate similar synthetic data, but `load_synt_gauss()` is cross-platform.

## Performance Tips

1. **First Run**: The first execution compiles C++/CUDA code (1-2 minutes)
2. **Subsequent Runs**: Use cached compiled code (much faster)
3. **GPU Memory**: Close other applications using GPU (browsers, games)
4. **Dataset Size**: Start with smaller datasets (vowel, glass) before trying large ones
5. **Monitor GPU**: Use `nvidia-smi` in another terminal to monitor GPU usage

## Next Steps

- Read [README_WINDOWS.md](README_WINDOWS.md) for detailed information
- Experiment with different datasets
- Try different parameters (neighborhood_size, F, num_obj)
- Use `load_synt_gauss()` to generate custom synthetic datasets

## Getting Help

1. Run diagnostics: `python check_windows_setup.py`
2. Check [README_WINDOWS.md](README_WINDOWS.md) for detailed troubleshooting
3. Original implementation questions: jakobrj@cs.au.dk
4. Windows-specific issues: Open an issue in the repository

## Common Commands Reference

```cmd
# Check setup
python check_windows_setup.py

# Run Windows example
python run_example_windows.py

# Run original example
python run_example.py

# Check CUDA in Python
python -c "import torch; print(torch.cuda.is_available())"

# Monitor GPU
nvidia-smi

# Clear compilation cache
rmdir /s /q %USERPROFILE%\.cache\torch_extensions
```

Happy clustering! 🚀
