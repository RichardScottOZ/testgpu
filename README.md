# testgpu

This repository contains GPU-INSCY, a GPU-accelerated density-based subspace clustering algorithm, refactored to work on Windows 11.

## GPU-INSCY

GPU-INSCY is located in the `GPU_INSCY/` directory. This is a Windows 11-compatible version of the implementation from the article "GPU-INSCY: A GPU-Parallel Algorithm and Tree Structure for Efficient Density-based Subspace Clustering".

**Original Repository**: https://github.com/jakobrj/GPU_INSCY

### Quick Start

For Windows 11 users:
1. See [GPU_INSCY/QUICKSTART_WINDOWS.md](GPU_INSCY/QUICKSTART_WINDOWS.md) for step-by-step installation
2. See [GPU_INSCY/README_WINDOWS.md](GPU_INSCY/README_WINDOWS.md) for detailed documentation
3. See [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) for details on what was changed

### Key Changes for Windows 11

- ✅ Cross-platform path handling using `os.path.join()`
- ✅ Replaced `os.system()` with `subprocess` for better compatibility
- ✅ Added Windows-specific documentation and examples
- ✅ Automated setup checker for Windows environments
- ✅ Comprehensive troubleshooting guides

See the [refactoring summary](REFACTORING_SUMMARY.md) for complete details.