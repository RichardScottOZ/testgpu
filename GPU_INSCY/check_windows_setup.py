"""
Windows 11 Setup Checker for GPU-INSCY
This script checks if your Windows environment is properly configured for GPU-INSCY
"""

import sys
import os
import subprocess
import platform

def check_python():
    """Check Python version"""
    print("\n=== Python Check ===")
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7 or later is required")
        return False
    
    print("✓ Python version is compatible")
    return True

def check_platform():
    """Check if running on Windows"""
    print("\n=== Platform Check ===")
    print(f"Platform: {platform.system()}")
    print(f"Platform version: {platform.version()}")
    
    if platform.system() != "Windows":
        print("⚠️  This script is designed for Windows. You may not need the Windows-specific changes.")
    else:
        print("✓ Running on Windows")
    return True

def check_cuda():
    """Check CUDA installation"""
    print("\n=== CUDA Check ===")
    try:
        result = subprocess.run(['nvcc', '--version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            print("✓ CUDA (nvcc) is installed")
            print(result.stdout.strip())
            return True
        else:
            print("❌ CUDA (nvcc) command failed")
            return False
    except FileNotFoundError:
        print("❌ CUDA (nvcc) not found in PATH")
        print("Please install NVIDIA CUDA Toolkit from:")
        print("https://developer.nvidia.com/cuda-downloads")
        return False
    except subprocess.TimeoutExpired:
        print("❌ CUDA check timed out")
        return False

def check_visual_studio():
    """Check for Visual Studio C++ compiler"""
    print("\n=== Visual Studio C++ Check ===")
    
    # Common paths for Visual Studio
    common_paths = [
        r"C:\Program Files\Microsoft Visual Studio\2022",
        r"C:\Program Files\Microsoft Visual Studio\2019",
        r"C:\Program Files (x86)\Microsoft Visual Studio\2019",
        r"C:\Program Files (x86)\Microsoft Visual Studio\2017",
    ]
    
    vs_found = False
    for path in common_paths:
        if os.path.exists(path):
            print(f"✓ Found Visual Studio at: {path}")
            vs_found = True
            break
    
    if not vs_found:
        print("❌ Visual Studio not found in common locations")
        print("Please install Visual Studio with C++ build tools")
        return False
    
    # Try to find cl.exe (C++ compiler)
    try:
        result = subprocess.run(['cl.exe'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5,
                              shell=True)
        if 'Microsoft' in result.stderr or 'Microsoft' in result.stdout:
            print("✓ Microsoft C++ compiler (cl.exe) is available")
            return True
    except:
        pass
    
    print("⚠️  Could not verify cl.exe availability")
    print("You may need to run this from 'Developer Command Prompt for VS'")
    return True  # Don't fail, as it might still work

def check_packages():
    """Check required Python packages"""
    print("\n=== Python Packages Check ===")
    
    required_packages = {
        'torch': 'PyTorch',
        'numpy': 'NumPy',
        'ninja': 'Ninja build system',
        'pandas': 'Pandas',
        'matplotlib': 'Matplotlib',
        'sklearn': 'scikit-learn'
    }
    
    all_installed = True
    for package, name in required_packages.items():
        try:
            __import__(package)
            print(f"✓ {name} is installed")
        except ImportError:
            print(f"❌ {name} is NOT installed")
            all_installed = False
    
    if not all_installed:
        print("\nInstall missing packages with:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def check_torch_cuda():
    """Check if PyTorch has CUDA support"""
    print("\n=== PyTorch CUDA Check ===")
    try:
        import torch
        print(f"PyTorch version: {torch.__version__}")
        
        if torch.cuda.is_available():
            print(f"✓ CUDA is available in PyTorch")
            print(f"CUDA version: {torch.version.cuda}")
            print(f"Number of GPUs: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
            return True
        else:
            print("❌ CUDA is NOT available in PyTorch")
            print("You may need to install PyTorch with CUDA support:")
            print("pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
            return False
    except ImportError:
        print("❌ PyTorch is not installed")
        return False

def check_cluster_generator():
    """Check cluster_generator availability"""
    print("\n=== Cluster Generator Check ===")
    
    gen_path = os.path.join('data', 'cluster_generator')
    gen_path_exe = gen_path + '.exe'
    
    if os.path.exists(gen_path_exe):
        print(f"✓ Found cluster_generator.exe")
        return True
    elif os.path.exists(gen_path):
        print(f"⚠️  Found cluster_generator but it's not a .exe file")
        print("This is likely the Linux binary and won't work on Windows")
        print("Use load_synt_gauss() instead of load_synt() for data generation")
        return False
    else:
        print("ℹ️  cluster_generator not found (this is expected on Windows)")
        print("Use load_synt_gauss() instead of load_synt() for data generation")
        return True  # Not a failure condition

def main():
    """Run all checks"""
    print("=" * 60)
    print("GPU-INSCY Windows 11 Setup Checker")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python),
        ("Platform", check_platform),
        ("CUDA Toolkit", check_cuda),
        ("Visual Studio", check_visual_studio),
        ("Python Packages", check_packages),
        ("PyTorch CUDA", check_torch_cuda),
        ("Cluster Generator", check_cluster_generator),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"❌ Error during {name} check: {e}")
            results[name] = False
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    critical_checks = ["Python Version", "CUDA Toolkit", "Python Packages", "PyTorch CUDA"]
    all_critical_passed = all(results.get(check, False) for check in critical_checks)
    
    for name, result in results.items():
        status = "✓" if result else "❌"
        critical = " (CRITICAL)" if name in critical_checks else ""
        print(f"{status} {name}{critical}")
    
    print("\n" + "=" * 60)
    if all_critical_passed:
        print("✓ All critical checks passed! You should be able to run GPU-INSCY.")
    else:
        print("❌ Some critical checks failed. Please fix the issues above.")
    print("=" * 60)

if __name__ == "__main__":
    main()
