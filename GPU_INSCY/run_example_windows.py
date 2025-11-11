"""
Windows-Compatible Example for GPU-INSCY

This script demonstrates how to use GPU-INSCY on Windows 11.
It avoids the cluster_generator binary (which is Linux-only) and uses
the pure Python data generation functions instead.
"""

from inscy import *

import sys
import os
import time
import numpy as np
import pandas as pd
import torch
import csv
import matplotlib.pyplot as plt


def run(method, X, method_name="Method"):
    """
    Run a clustering method on dataset X and measure time
    """
    c = 4
    num_obj = 8
    F = 1.
    r = 1.
    min_size = 0.05
    N_size = 0.01
    n = X.shape[0]
    
    print(f"\nRunning {method_name} (3 iterations)...")
    times = []
    
    for i in range(3):
        t0 = time.time()
        result = method(X, N_size, F, num_obj, int(n * min_size), r, 
                       number_of_cells=c, rectangular=True)
        t1 = time.time()
        elapsed = t1 - t0
        print(f"  Iteration {i+1}: {elapsed:.4f}s")
        times.append(elapsed)
    
    avg = sum(times) / len(times)
    print(f"  Average: {avg:.4f}s")
    return avg


def runs(method, method_name="Method"):
    """
    Run method on multiple datasets
    """
    print(f"\n{'='*60}")
    print(f"Testing {method_name}")
    print('='*60)
    
    datasets = [
        (load_glass, "glass"),
        (load_vowel, "vowel")
    ]
    
    results = []
    for load_func, name in datasets:
        print(f"\nDataset: {name}")
        X = load_func()
        print(f"  Shape: {X.shape}")
        avg_time = run(method, X, method_name)
        results.append(avg_time)
    
    return results


def main():
    print("="*60)
    print("GPU-INSCY Windows Example")
    print("="*60)
    print("\nThis example runs GPU-INSCY algorithms on vowel and glass datasets.")
    print("Note: Using Python-based data generation (Windows-compatible).")
    print("\nFirst run will compile C++/CUDA code (1-2 minutes)...")
    
    # Check if running on Windows
    if sys.platform == 'win32':
        print("\n✓ Running on Windows")
    else:
        print(f"\n⚠️  Running on {sys.platform} (not Windows)")
    
    # Check CUDA availability
    print(f"\nCUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"GPU: {torch.cuda.get_device_name(0)}")
    else:
        print("⚠️  Warning: CUDA not available. GPU algorithms will fail.")
        print("Make sure you have:")
        print("  1. NVIDIA GPU with CUDA support")
        print("  2. CUDA Toolkit installed")
        print("  3. PyTorch with CUDA support")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Exiting...")
            return
    
    # Load a test dataset to trigger compilation
    print("\nLoading test dataset...")
    X = load_vowel()
    
    c = 4
    num_obj = 8
    F = 1.
    r = 1.
    min_size = 0.05
    N_size = 0.01
    n = X.shape[0]
    
    # Do one run to initialize GPU and compile code
    print("\nInitializing GPU and compiling code (this may take 1-2 minutes)...")
    try:
        GPU_INSCY(X, N_size, F, num_obj, int(n * min_size), r, 
                 number_of_cells=c, rectangular=True)
        print("✓ Compilation successful!")
    except Exception as e:
        print(f"❌ Error during compilation: {e}")
        print("\nPlease check:")
        print("  1. CUDA Toolkit is installed")
        print("  2. Visual Studio with C++ tools is installed")
        print("  3. Run 'python check_windows_setup.py' for detailed diagnostics")
        return
    
    # Run benchmarks
    labels = ["glass", "vowel"]
    
    print("\n" + "="*60)
    print("Running Benchmarks")
    print("="*60)
    
    try:
        results_inscy = runs(INSCY, "INSCY (CPU)")
    except Exception as e:
        print(f"❌ INSCY failed: {e}")
        results_inscy = [0, 0]
    
    try:
        results_gpu_inscy = runs(GPU_INSCY, "GPU-INSCY")
    except Exception as e:
        print(f"❌ GPU-INSCY failed: {e}")
        results_gpu_inscy = [0, 0]
    
    try:
        results_gpu_inscy_star = runs(GPU_INSCY_star, "GPU-INSCY*")
    except Exception as e:
        print(f"❌ GPU-INSCY* failed: {e}")
        results_gpu_inscy_star = [0, 0]
    
    try:
        results_gpu_inscy_memory = runs(GPU_INSCY_memory, "GPU-INSCY-memory")
    except Exception as e:
        print(f"❌ GPU-INSCY-memory failed: {e}")
        results_gpu_inscy_memory = [0, 0]
    
    # Plot results
    print("\n" + "="*60)
    print("Creating visualization...")
    print("="*60)
    
    try:
        ra = np.arange(len(labels))
        fig, ax = plt.subplots(figsize=(8, 5))
        width = 0.20
        
        rects1 = ax.bar(ra - 3*width/2, results_inscy, width=width, label="INSCY")
        rects2 = ax.bar(ra - width/2, results_gpu_inscy, width=width, label="GPU-INSCY")
        rects3 = ax.bar(ra + width/2, results_gpu_inscy_star, width=width, label="GPU-INSCY*")
        rects4 = ax.bar(ra + 3*width/2, results_gpu_inscy_memory, width=width, 
                       label="GPU-INSCY-memory")
        
        ax.set_xticks(ra)
        ax.set_xticklabels(labels)
        
        def autolabel(rects):
            """Attach a text label above each bar displaying its height."""
            for rect in rects:
                height = round(rect.get_height(), 3)
                if height > 0:  # Only label non-zero bars
                    ax.annotate('{}'.format(height),
                               xy=(rect.get_x() + rect.get_width() / 2, height),
                               xytext=(0, 1),
                               textcoords="offset points",
                               ha='center', va='bottom', fontsize=9)
        
        autolabel(rects1)
        autolabel(rects2)
        autolabel(rects3)
        autolabel(rects4)
        
        plt.ylabel('time in seconds')
        plt.title('GPU-INSCY Performance Comparison (Windows)')
        ax.legend()
        plt.rc('font', size=11)
        plt.yscale("log")
        fig.tight_layout()
        
        # Save plot
        output_file = "example_windows.png"
        plt.savefig(output_file)
        print(f"✓ Plot saved to: {output_file}")
        
        # Show plot
        plt.show()
        
    except Exception as e:
        print(f"❌ Plotting failed: {e}")
    
    print("\n" + "="*60)
    print("Example completed!")
    print("="*60)


if __name__ == "__main__":
    main()
