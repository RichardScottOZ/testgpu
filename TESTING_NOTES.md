# Testing Notes for GPU-INSCY Windows 11 Refactoring

## Testing Environment Requirements

This refactoring was designed for Windows 11 but the actual testing cannot be performed in this Linux environment. Below are comprehensive testing instructions for validation on an actual Windows 11 system.

## Pre-Testing Setup

### Minimum System Requirements
- Windows 11 (or Windows 10 with latest updates)
- NVIDIA GPU with CUDA compute capability 3.5 or higher
- 8GB RAM (16GB recommended)
- 10GB free disk space
- Internet connection for package installation

### Required Software
1. CUDA Toolkit 11.0 or later
2. Visual Studio 2019 or 2022 with "Desktop development with C++" workload
3. Python 3.7-3.11 (64-bit)
4. Latest NVIDIA GPU drivers

## Testing Checklist

### Phase 1: Environment Validation

```powershell
# Navigate to repository
cd path\to\testgpu\GPU_INSCY

# Run setup checker
python check_windows_setup.py
```

**Expected Results:**
- ✓ All critical checks should pass (Python, CUDA, packages, PyTorch CUDA)
- Visual Studio check may show warning (acceptable if cl.exe is in PATH)
- Cluster generator check expected to show "not found" on Windows (this is OK)

**What to Verify:**
- [ ] Python version is 3.7 or later
- [ ] CUDA toolkit is detected (`nvcc --version` works)
- [ ] All Python packages are installed
- [ ] PyTorch reports CUDA is available
- [ ] GPU is detected and named correctly

### Phase 2: Basic Import Test

```python
# test_import.py
from inscy import *
import torch

print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")

print("Import successful!")
```

**Expected Results:**
- First run: Compilation messages (1-2 minutes)
- CUDA should be available
- GPU name should be displayed
- No import errors

**What to Verify:**
- [ ] Compilation completes without errors
- [ ] CUDA is available in PyTorch
- [ ] GPU is properly detected
- [ ] No import errors or warnings

### Phase 3: Data Loading Test

```python
# test_data.py
from inscy import *

# Test data loaders with Windows-compatible paths
print("Testing data loaders...")

try:
    X_glass = load_glass()
    print(f"✓ glass.data loaded: {X_glass.shape}")
except Exception as e:
    print(f"✗ glass.data failed: {e}")

try:
    X_vowel = load_vowel()
    print(f"✓ vowel.dat loaded: {X_vowel.shape}")
except Exception as e:
    print(f"✗ vowel.dat failed: {e}")

try:
    X_pendigits = load_pendigits()
    print(f"✓ pendigits.tra loaded: {X_pendigits.shape}")
except Exception as e:
    print(f"✗ pendigits.tra failed: {e}")

# Test synthetic data generator (Windows-compatible)
try:
    X_synth = load_synt_gauss(d=10, n=1000, cl=2, std=0.5)
    print(f"✓ Synthetic data generated: {X_synth.shape}")
except Exception as e:
    print(f"✗ Synthetic data failed: {e}")

print("Data loading test complete!")
```

**Expected Results:**
- All three real datasets should load successfully
- Synthetic data generation should work
- Correct shapes: glass (214, 9), vowel (990, 10), pendigits (7494, 16)

**What to Verify:**
- [ ] glass.data loads correctly
- [ ] vowel.dat loads correctly
- [ ] pendigits.tra loads correctly
- [ ] load_synt_gauss() works (pure Python, Windows-compatible)
- [ ] No path-related errors

### Phase 4: Algorithm Test (Small Dataset)

```python
# test_algorithm.py
from inscy import *
import time

print("Testing GPU_INSCY_memory on small dataset...")

# Load small dataset
X = load_glass()
print(f"Dataset shape: {X.shape}")

# Set parameters
neighborhood_size = 0.01
F = 1.0
num_obj = 8
min_size = int(X.shape[0] * 0.05)
r = 1.0
number_of_cells = 4

# Run algorithm
print("Running GPU_INSCY_memory...")
t0 = time.time()
results = GPU_INSCY_memory(X, neighborhood_size, F, num_obj, min_size, r, 
                          number_of_cells=number_of_cells, rectangular=True)
elapsed = time.time() - t0

print(f"✓ Completed in {elapsed:.2f} seconds")
print(f"Found {len(results[0])} clusters")
print(f"Subspaces: {results[0]}")
```

**Expected Results:**
- Should complete in 1-5 seconds (after compilation)
- Should find multiple clusters
- No CUDA errors or crashes

**What to Verify:**
- [ ] Algorithm completes without errors
- [ ] Execution time is reasonable
- [ ] Results contain subspaces and clusterings
- [ ] No CUDA out-of-memory errors
- [ ] No segmentation faults

### Phase 5: Full Example (Windows Script)

```powershell
python run_example_windows.py
```

**Expected Results:**
- Compilation on first run (1-2 minutes)
- Runs on glass and vowel datasets
- Tests 4 algorithms: INSCY, GPU-INSCY, GPU-INSCY*, GPU-INSCY-memory
- Total time: 3-5 minutes
- Creates `example_windows.png` plot
- All algorithms complete successfully

**What to Verify:**
- [ ] Compilation succeeds (first run only)
- [ ] INSCY (CPU) completes
- [ ] GPU-INSCY completes
- [ ] GPU-INSCY* completes
- [ ] GPU-INSCY-memory completes
- [ ] Plot is generated
- [ ] No crashes or exceptions
- [ ] Results look reasonable (GPU faster than CPU on larger datasets)

### Phase 6: Original Example (Compatibility Test)

```powershell
python run_example.py
```

**Expected Results:**
- Should work the same as run_example_windows.py
- May show plot instead of saving to file

**What to Verify:**
- [ ] Script runs without modification
- [ ] Results match run_example_windows.py
- [ ] Backward compatibility maintained

## Common Issues and Expected Behaviors

### Expected Warnings (OK to ignore):
1. PyTorch compilation warnings about deprecated features
2. CUDA warnings about architecture
3. Ninja build system version warnings

### Expected First-Run Behaviors:
1. **Slow first compilation**: 1-2 minutes is normal
2. **Multiple compilation messages**: CUDA compiles each .cu file
3. **High CPU usage during compilation**: Normal for C++ compilation
4. **Temporary files created**: In `%USERPROFILE%\.cache\torch_extensions\`

### Indicators of Success:
1. ✓ No import errors
2. ✓ CUDA reports as available
3. ✓ GPU is properly named
4. ✓ Data loads without path errors
5. ✓ Algorithms complete without crashes
6. ✓ Results are generated
7. ✓ Plot files are created

### Indicators of Problems:
1. ❌ Import errors → Check package installation
2. ❌ CUDA not available → Check PyTorch installation
3. ❌ Path errors → Check path separators, should use os.path.join()
4. ❌ Compilation errors → Check Visual Studio and CUDA installation
5. ❌ CUDA out of memory → Try smaller datasets or close other GPU apps
6. ❌ Segmentation fault → May indicate GPU driver issue

## Performance Benchmarks

Expected relative performance on glass dataset (214 samples):

- INSCY (CPU): ~0.5-2 seconds
- GPU-INSCY: ~0.1-0.5 seconds
- GPU-INSCY*: ~0.1-0.5 seconds
- GPU-INSCY-memory: ~0.1-0.5 seconds

On vowel dataset (990 samples):

- INSCY (CPU): ~5-20 seconds
- GPU-INSCY: ~0.5-2 seconds
- GPU-INSCY*: ~0.5-2 seconds
- GPU-INSCY-memory: ~0.5-2 seconds

*Actual times vary based on GPU model and CPU*

## Validation Criteria

### Critical (Must Pass):
- [x] Repository structure is correct
- [ ] check_windows_setup.py runs and reports status
- [ ] Basic imports work (from inscy import *)
- [ ] PyTorch detects CUDA
- [ ] Data loading with os.path.join() works
- [ ] At least one algorithm completes successfully

### Important (Should Pass):
- [ ] All data loaders work
- [ ] All four algorithms complete
- [ ] run_example_windows.py completes
- [ ] Plots are generated
- [ ] No path separator issues

### Nice to Have (May Pass):
- [ ] Performance matches expectations
- [ ] Original run_example.py works unmodified
- [ ] Compilation cache works (fast subsequent runs)

## Testing on Different Windows Versions

### Windows 11 (Primary Target)
- Full testing recommended
- All features should work

### Windows 10 (Secondary Target)
- Should work identically to Windows 11
- CUDA and Visual Studio versions are the key factors

### Windows Server
- Not tested but should work
- May need GUI libraries for matplotlib

## Post-Testing Validation

After successful testing, verify:

1. **Files Created**:
   - [ ] `%USERPROFILE%\.cache\torch_extensions\` contains compiled code
   - [ ] `example_windows.png` (if ran Windows example)
   - [ ] No temporary files in repository directory

2. **Git Status**:
   - [ ] No untracked build artifacts in git status
   - [ ] .gitignore properly excludes generated files

3. **Reproducibility**:
   - [ ] Second run is much faster (uses cached compilation)
   - [ ] Results are consistent across runs

## Debugging Failed Tests

If tests fail, collect this information:

```powershell
# System info
python --version
nvcc --version
nvidia-smi

# PyTorch info
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda}')"

# Setup check
python check_windows_setup.py > setup_output.txt

# Detailed error
python run_example_windows.py > test_output.txt 2>&1
```

## Automated Testing Script

```python
# full_test.py
import sys
import traceback

def run_test(name, test_func):
    print(f"\n{'='*60}")
    print(f"Test: {name}")
    print('='*60)
    try:
        test_func()
        print(f"✓ {name} PASSED")
        return True
    except Exception as e:
        print(f"✗ {name} FAILED")
        print(f"Error: {e}")
        traceback.print_exc()
        return False

def test_import():
    from inscy import *
    import torch
    assert torch.cuda.is_available(), "CUDA not available"

def test_data():
    from inscy import load_glass, load_vowel
    X1 = load_glass()
    assert X1.shape[0] > 0, "Glass data empty"
    X2 = load_vowel()
    assert X2.shape[0] > 0, "Vowel data empty"

def test_algorithm():
    from inscy import load_glass, GPU_INSCY_memory
    X = load_glass()
    results = GPU_INSCY_memory(X, 0.01, 1.0, 8, 10, 1.0, 4, True)
    assert len(results) == 2, "Invalid results structure"

# Run all tests
tests = [
    ("Import", test_import),
    ("Data Loading", test_data),
    ("Algorithm", test_algorithm),
]

results = [run_test(name, func) for name, func in tests]

print(f"\n{'='*60}")
print(f"Summary: {sum(results)}/{len(results)} tests passed")
print('='*60)

sys.exit(0 if all(results) else 1)
```

Save as `full_test.py` and run: `python full_test.py`

## Conclusion

This refactoring has been validated for correctness of:
- [x] Code changes (minimal, focused on Windows compatibility)
- [x] Path handling (uses os.path.join throughout)
- [x] Subprocess usage (proper Windows compatibility)
- [x] Documentation (comprehensive guides for Windows)
- [x] Error handling (informative messages)
- [x] Git ignore (excludes Windows artifacts)

Actual execution testing on Windows 11 with CUDA is required for final validation.
