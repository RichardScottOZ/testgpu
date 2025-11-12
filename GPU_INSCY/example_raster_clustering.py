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
    
    Note: All pixels have valid data (values 1-10000) with nodata=0 to ensure
    no invalid pixels that could cause clustering algorithm issues.
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
    
    # Create Gaussian clusters in 2D space (like load_synt_gauss in test.py)
    num_clusters = 4
    cluster_centers = [(0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)]
    cluster_std = 0.12  # Similar to std=0.5 in test.py normalized
    
    # Assign each pixel to closest cluster
    cluster_assignments = np.zeros((H, W), dtype=int)
    for i in range(H):
        for j in range(W):
            x_coord, y_coord = X[i, j], Y[i, j]
            dists = [np.sqrt((x_coord - cx)**2 + (y_coord - cy)**2) for cx, cy in cluster_centers]
            cluster_assignments[i, j] = np.argmin(dists)
    
    for band_idx in range(n_bands):
        # Create Gaussian cluster data for this band (like load_synt_gauss)
        # Each cluster has different mean values per band
        data = np.zeros((H, W), dtype=np.float32)
        
        for cluster_id in range(num_clusters):
            mask = cluster_assignments == cluster_id
            # Each cluster-band combination has its own Gaussian-distributed mean
            cluster_mean = 0.25 + (cluster_id * 0.18) + (band_idx * 0.03)
            # Add Gaussian noise (like test.py std parameter)
            data[mask] = cluster_mean + cluster_std * np.random.randn(mask.sum())
        
        # Clip to valid range [0, 1]
        data = np.clip(data, 0, 1)
        
        # Convert to uint16 for realistic GeoTIFF
        # Scale to 1-10000 range to avoid 0 values (which is nodata)
        data_uint = (data * 9999 + 1).astype(np.uint16)
        
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
            'nodata': 0  # No pixel should have value 0 now
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
        "--rectangular",  # Critical: all working examples use rectangular=True
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

    print(result)
    
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
