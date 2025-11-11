#!/usr/bin/env python3
"""
Example: Create synthetic raster data and run GPU_INSCY clustering.

This demonstrates the raster_clustering.py workflow with synthetic multi-band data.
"""
import os
import tempfile
import numpy as np
import rasterio as rio
from rasterio.transform import from_bounds
from pathlib import Path


def create_synthetic_rasters(output_dir: Path, H=256, W=256, n_bands=6):
    """
    Create synthetic multi-band raster data for testing.
    
    Generates n_bands GeoTIFF files with synthetic spatial patterns:
    - Bands 0-2: Gradient patterns (simulate RGB)
    - Bands 3-5: Clustered patterns (simulate NIR/SWIR)
    """
    print(f"Creating synthetic rasters in {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Simple geographic transform (1 degree per pixel)
    transform = from_bounds(0, 0, W, H, W, H)
    
    # Create coordinate grids
    x = np.linspace(0, 1, W)
    y = np.linspace(0, 1, H)
    X, Y = np.meshgrid(x, y)
    
    paths = []
    
    for band_idx in range(n_bands):
        # Create different patterns for different bands
        if band_idx < 3:
            # Gradient patterns
            data = (X * 0.5 + Y * 0.5 + np.sin(X * 4 * np.pi) * 0.1 +
                   band_idx * 0.3)
        else:
            # Clustered patterns - create 3-4 distinct regions
            angle = band_idx * np.pi / 3
            cx, cy = 0.5 + 0.2 * np.cos(angle), 0.5 + 0.2 * np.sin(angle)
            dist = np.sqrt((X - cx)**2 + (Y - cy)**2)
            data = np.exp(-dist * 10) * (1 + 0.3 * np.random.randn(H, W))
        
        # Add some noise
        data = data + 0.05 * np.random.randn(H, W)
        
        # Normalize to 0-1 range
        data = (data - data.min()) / (data.max() - data.min())
        
        # Convert to uint16 for realistic GeoTIFF
        data_uint = (data * 10000).astype(np.uint16)
        
        # Write GeoTIFF
        filepath = output_dir / f"band_{band_idx:02d}.tif"
        meta = {
            'driver': 'GTiff',
            'height': H,
            'width': W,
            'count': 1,
            'dtype': 'uint16',
            'crs': 'EPSG:4326',
            'transform': transform,
            'nodata': 0
        }
        
        with rio.open(filepath, 'w', **meta) as dst:
            dst.write(data_uint, 1)
        
        paths.append(filepath)
        print(f"  Created {filepath.name}")
    
    return paths


def run_example():
    """Run complete example of raster clustering."""
    print("=" * 70)
    print("GPU_INSCY Raster Clustering Example")
    print("=" * 70)
    
    # Setup paths
    script_dir = Path(__file__).parent
    temp_dir = Path(tempfile.mkdtemp(prefix="inscy_example_"))
    
    print(f"\nWorking directory: {temp_dir}")
    
    # Create synthetic data
    raster_dir = temp_dir / "rasters"
    output_dir = temp_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    paths = create_synthetic_rasters(raster_dir, H=256, W=256, n_bands=6)
    
    # Build command
    output_tif = output_dir / "clusters.tif"
    artifacts_dir = output_dir / "artifacts"
    
    cmd = [
        "python", str(script_dir / "raster_clustering.py"),
        "--root_dir", str(raster_dir),
        "--output_tif", str(output_tif),
        "--artifacts_dir", str(artifacts_dir),
        "--inscy_dir", str(script_dir),
        "--variant", "GPU_INSCY_memory",
        "--neighborhood_size", "0.01",
        "--F", "1.0",
        "--num_obj", "8",
        "--min_size", "500",
        "--standardize",
        "--output_subspace_idx", "0"
    ]
    
    print("\n" + "=" * 70)
    print("Running GPU_INSCY clustering...")
    print("=" * 70)
    print("\nCommand:")
    print(" ".join(cmd))
    print()
    
    # Run clustering
    import subprocess
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode == 0:
        print("\n" + "=" * 70)
        print("SUCCESS!")
        print("=" * 70)
        print(f"\nOutput files:")
        print(f"  Labels GeoTIFF: {output_tif}")
        print(f"  Artifacts JSON: {artifacts_dir / 'inscy_artifacts.json'}")
        print(f"\nTo visualize results, open {output_tif} in QGIS or similar GIS software.")
    else:
        print("\n" + "=" * 70)
        print("FAILED")
        print("=" * 70)
        print(f"Return code: {result.returncode}")
    
    return temp_dir


if __name__ == "__main__":
    try:
        import rasterio
    except ImportError:
        print("Error: rasterio not installed. Install with: pip install rasterio")
        exit(1)
    
    temp_dir = run_example()
    print(f"\nTemporary files in: {temp_dir}")
    print("(These will be cleaned up when temp directory is deleted)")
