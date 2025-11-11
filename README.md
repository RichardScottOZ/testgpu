# testgpu

This repository contains an integration of the GPU_INSCY algorithm for Ubuntu systems.

## Contents

- **GPU_INSCY/**: Complete GPU_INSCY implementation cloned from https://github.com/jakobrj/GPU_INSCY
  - GPU-accelerated density-based subspace clustering algorithm
  - Supports INSCY, GPU-INSCY, GPU-INSCY*, and GPU-INSCY-memory variants
  - Includes example datasets and test scripts

## Quick Start

See [SETUP.md](SETUP.md) for detailed installation and usage instructions.

### Basic Installation

```bash
cd GPU_INSCY
pip install -r requirements.txt
```

### Run Example

```bash
cd GPU_INSCY
python run_example.py
```

## Requirements

- Ubuntu 20.04 LTS or newer
- Python 3.7+
- GCC/G++ compiler
- Optional: NVIDIA GPU with CUDA support for GPU acceleration

## Documentation

- [Setup Guide](SETUP.md) - Comprehensive setup instructions for Ubuntu
- [GPU_INSCY README](GPU_INSCY/README.md) - Original project documentation

## About GPU_INSCY

GPU_INSCY is an implementation from the article "GPU-INSCY: A GPU-Parallel Algorithm and Tree Structure for Efficient Density-based Subspace Clustering". It provides efficient GPU-accelerated clustering algorithms for high-dimensional data.