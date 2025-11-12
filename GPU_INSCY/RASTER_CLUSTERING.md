# GPU_INSCY Raster Clustering Guide

This guide explains how to use GPU_INSCY for geospatial raster clustering.

## Overview

The `raster_clustering.py` script adapts GPU_INSCY for geospatial raster data, enabling density-based subspace clustering on multi-band imagery. Unlike traditional clustering methods, GPU_INSCY identifies clusters that exist in subspaces (subsets of bands/dimensions), making it ideal for hyperspectral or multi-temporal data where different phenomena appear in different spectral regions.

## Key Differences from GPU_PROCLUS

| Feature | GPU_PROCLUS | GPU_INSCY |
|---------|-------------|-----------|
| Method | Projected clustering (medoids) | Density-based subspace clustering |
| Output | Single clustering | Multiple clusterings (one per subspace) |
| Parameters | k, l (fixed dimensions) | neighborhood_size, min_size (density-based) |
| GPU Support | Stays on GPU | CPU tensors → GPU (managed internally) |
| Subspaces | Fixed l dimensions per cluster | Automatically discovered per cluster |

**Important**: GPU_INSCY expects **CPU tensors** and handles GPU transfer internally. Do not pre-move tensors to CUDA!

## Installation

### Prerequisites

```bash
# Ensure CUDA is installed (see SETUP.md)
cd GPU_INSCY
pip install -r requirements.txt

# Additional dependency for raster processing
pip install rasterio
```

### Verify Installation

```bash
python verify_installation.py
python test_compilation.py
```

## Usage

### Basic Example

```bash
python raster_clustering.py \
  --root_dir /path/to/rasters \
  --output_tif /path/to/output_labels.tif \
  --inscy_dir /home/runner/work/testgpu/testgpu/GPU_INSCY \
  --variant GPU_INSCY_memory \
  --neighborhood_size 0.01 \
  --F 1.0 \
  --num_obj 8 \
  --rectangular \
  --standardize
```

### Full Example with Artifacts

```bash
python raster_clustering.py \
  --root_dir /data/imagery/my_scene \
  --include_dirs_regex "B[0-9]+" \
  --output_tif /output/clusters.tif \
  --artifacts_dir /output/artifacts \
  --inscy_dir /home/runner/work/testgpu/testgpu/GPU_INSCY \
  --variant GPU_INSCY_memory \
  --neighborhood_size 0.01 \
  --F 1.0 \
  --num_obj 8 \
  --min_size 1000 \
  --r 1.0 \
  --number_of_cells 4 \
  --rectangular \
  --output_subspace_idx 0 \
  --standardize \
  --compress LZW \
  --tile_rows 512 \
  --save_band_list /output/bands.txt
```

## Parameters

### Required Parameters

- `--root_dir`: Directory containing GeoTIFF rasters (each file = one band)
- `--output_tif`: Output path for cluster labels GeoTIFF
- `--inscy_dir`: Path to GPU_INSCY directory (containing inscy.py)

### GPU_INSCY Algorithm Parameters

- `--variant`: Algorithm variant (default: GPU_INSCY_memory)
  - `GPU_INSCY`: Basic GPU implementation
  - `GPU_INSCY_star`: Optimized GPU version
  - `GPU_INSCY_memory`: Memory-optimized GPU version (recommended)
  - `INSCY`: CPU-only version (slower)

- `--neighborhood_size`: Neighborhood radius for density estimation (default: 0.01)
  - Similar to epsilon in DBSCAN
  - Smaller values = stricter clustering
  - Should be adjusted based on standardized data scale
  - **Important**: Use smaller values (0.001-0.01) for small datasets, larger values (0.01-0.05) for large datasets
  - Too large values may cause algorithm failure

- `--F`: Dimension selection threshold (default: 1.0)
  - Controls how dimensions are selected for subspaces
  - Higher values = more selective

- `--num_obj`: Number of objects parameter (default: 8)
  - Minimum objects in neighborhood

- `--min_size`: Minimum cluster size in pixels (default: 5% of N)
  - Absolute count, not percentage
  - Clusters smaller than this are discarded
  - **Important**: Should be significantly smaller than total data size
  - Recommended: 0.5% - 10% of valid pixels for best results

- `--r`: R parameter (default: 1.0)
  - Radius parameter for clustering

- `--number_of_cells`: Spatial indexing cells (default: 4)
  - For spatial data structure
  - Higher values = more memory, potentially faster

- `--rectangular`: Use rectangular neighborhoods (flag)
  - **Recommended**: All working GPU_INSCY examples use this flag
  - vs spherical neighborhoods (default, but less stable)
  - Significantly improves algorithm stability

### Output Control

- `--output_subspace_idx`: Which subspace to output (default: 0)
  - `0`: Largest subspace clustering (by labeled pixels)
  - `1, 2, ...`: Specific subspace index
  - `-1`: Combine all subspaces (cluster IDs offset to avoid conflicts)

### Data Processing

- `--standardize`: Apply z-score normalization per band (recommended flag)
  - **Important**: Data is automatically normalized to [0,1] range per band after loading (required by GPU_INSCY)
  - The standardize flag applies z-score normalization first, then min-max normalization to [0,1]
- `--tile_rows`: Rows per tile for reading (default: 512)
- `--compress`: GeoTIFF compression (default: LZW)
  - Options: LZW, ZSTD, DEFLATE, NONE

### Directory Filtering

- `--include_dirs_regex`: Regex to include subdirectories
- `--exclude_dirs_regex`: Regex to exclude subdirectories

### Optional Outputs

- `--artifacts_dir`: Save JSON artifacts with detailed results
- `--save_band_list`: Save list of discovered bands to text file

## Dataset Size Limitations

**⚠️ CRITICAL**: GPU_INSCY has been tested with datasets up to **~10,000 samples × 20 dimensions**.

### Tested Dataset Sizes

| Dataset | Samples | Dimensions | Status |
|---------|---------|------------|--------|
| vowel | 989 | 10 | ✅ Works |
| glass | 214 | 11 | ✅ Works |
| pendigits | 7,494 | 17 | ✅ Works |
| test.py synthetic | 8,000 | 15 | ✅ Works |
| **Large raster data** | **1M+** | **50+** | ⚠️ **May crash** |

### If Your Dataset is Too Large

**Symptoms**: Instant segmentation fault, CUDA errors, no output

**Solutions**:

1. **Spatial Downsampling**
   ```bash
   # Example: downsample to 10% of pixels
   python raster_clustering.py ... --downsample 10
   ```
   Or manually subsample your raster before processing

2. **Band Selection**
   ```bash
   # Select only 15-20 most informative bands
   # Use PCA, variance analysis, or domain knowledge
   ```

3. **Tile-Based Processing**
   ```bash
   # Process spatial tiles separately
   # Merge results with post-processing
   ```

4. **Memory-Efficient Variant**
   ```bash
   # Use GPU_INSCY_memory (most memory-efficient)
   --variant GPU_INSCY_memory
   ```

### Safe Guidelines

- **Samples**: Keep under 50,000 for reliability, under 10,000 for tested stability
- **Dimensions**: Keep under 30 dimensions, ideally 15-20
- **Memory**: Monitor GPU memory usage (<2GB recommended)

### Error Message

If the script detects an oversized dataset, you'll see:
```
[WARNING] Dataset size (6,480,000 × 84) exceeds GPU_INSCY tested limits!
[WARNING] Tested max: 10,000 samples × 20 dimensions
[ERROR] Please downsample your data before running.
```

## Input Data Format

### Requirements

- **Format**: GeoTIFF files (*.tif, *.tiff)
- **Structure**: One file per band/feature
- **Consistency**: All files must have:
  - Same height and width
  - Same coordinate reference system (CRS)
  - Same geotransform
  - Compatible nodata values

### Example Directory Structure

```
/data/scene_001/
├── band_01_blue.tif
├── band_02_green.tif
├── band_03_red.tif
├── band_04_nir.tif
├── band_05_swir1.tif
└── band_06_swir2.tif
```

## Output Format

### Cluster Labels GeoTIFF

- **Data type**: int32
- **Nodata value**: -1
- **Values**: 
  - `-1`: No data or not clustered
  - `0, 1, 2, ...`: Cluster IDs
- **Georeferencing**: Preserved from input
- **Compression**: Configurable (default: LZW)

### Artifacts JSON (optional)

When `--artifacts_dir` is specified, creates `inscy_artifacts.json` with:

```json
{
  "variant": "GPU_INSCY_memory",
  "params": {
    "neighborhood_size": 0.01,
    "F": 1.0,
    "num_obj": 8,
    "min_size": 1000,
    ...
  },
  "bands": ["path/to/band1.tif", ...],
  "grid": {"H": 1024, "W": 1024, "N": 1048576, "B": 6},
  "subspaces": [[0, 1, 2], [3, 4, 5]],
  "output_subspace": "[0, 1, 2]",
  "label_summary": {
    "total_pixels": 1048576,
    "labeled_pixels": 950000,
    "nodata_pixels": 98576,
    "non_empty_clusters": 15,
    "top_clusters": [
      {"cluster_id": 0, "count": 125000},
      {"cluster_id": 1, "count": 98500},
      ...
    ]
  }
}
```

## Understanding GPU_INSCY Results

### Subspace Clustering

GPU_INSCY finds clusters in subspaces (dimension subsets). For example, with 10 bands:
- Subspace 1: bands [0, 2, 5] → 8 clusters
- Subspace 2: bands [1, 3, 4, 7] → 5 clusters
- Subspace 3: bands [6, 8, 9] → 3 clusters

Each subspace represents a different "view" where clusters are evident.

### Choosing Output Subspace

- **Default (idx=0)**: Usually the largest/most significant subspace
- **Combined (idx=-1)**: Merge all subspaces (cluster IDs are offset)
- **Specific (idx=1,2,...)**: Focus on particular subspace

## Performance Considerations

### Memory

GPU_INSCY loads entire feature matrix (N×B) to GPU:
- N = H × W (valid pixels)
- B = number of bands
- Memory ≈ N × B × 4 bytes (float32)

Example: 10,000 × 10,000 pixels × 10 bands = 4 GB

### Speed

- First run: 1-2 minutes for JIT compilation
- Subsequent runs: Fast (compiled code cached)
- GPU_INSCY_memory recommended for large datasets
- Processing time scales with N and neighborhood_size

### Recommendations

1. **Start small**: Test on subset or downsampled data
2. **Standardize**: Always use `--standardize` for multi-band data
3. **Tune neighborhood_size**: Start with 0.01, adjust based on results
4. **Monitor memory**: Use `nvidia-smi` to check GPU usage

## Comparison with Original Script

### GPU_PROCLUS Script Features Preserved

✅ Directory-based raster discovery  
✅ Regex filtering for subdirectories  
✅ Tile-based reading (memory efficient)  
✅ Z-score standardization  
✅ NODATA handling  
✅ Stays on GPU during clustering  
✅ GeoTIFF output with compression  
✅ JSON artifacts  
✅ Cluster size summaries  

### Adapted for GPU_INSCY

✅ **Subspace clustering** instead of projected clustering  
✅ **Density-based parameters** (neighborhood_size, min_size) instead of medoid-based (k, l)  
✅ **Multiple subspace outputs** with selection options  
✅ **Automatic dimension discovery** per cluster  
✅ Four algorithm variants (GPU_INSCY, GPU_INSCY_star, GPU_INSCY_memory, INSCY)  

## Examples

### Example 1: Land Cover Classification

```bash
# 6 Landsat bands, find land cover clusters
python raster_clustering.py \
  --root_dir /data/landsat/scene_001 \
  --output_tif /output/landcover_clusters.tif \
  --inscy_dir ./GPU_INSCY \
  --variant GPU_INSCY_memory \
  --neighborhood_size 0.015 \
  --num_obj 10 \
  --min_size 500 \
  --rectangular \
  --standardize \
  --artifacts_dir /output/artifacts
```

### Example 2: Hyperspectral Analysis

```bash
# 100+ hyperspectral bands, find material clusters
python raster_clustering.py \
  --root_dir /data/hyperspectral/flight_01 \
  --include_dirs_regex "band_[0-9]+" \
  --output_tif /output/materials.tif \
  --inscy_dir ./GPU_INSCY \
  --variant GPU_INSCY_memory \
  --neighborhood_size 0.01 \
  --F 1.5 \
  --num_obj 8 \
  --min_size 1000 \
  --output_subspace_idx -1 \
  --standardize \
  --rectangular
```

### Example 3: Time Series Analysis

```bash
# Multi-temporal data, find change patterns
python raster_clustering.py \
  --root_dir /data/timeseries/monthly \
  --output_tif /output/temporal_clusters.tif \
  --inscy_dir ./GPU_INSCY \
  --variant GPU_INSCY_memory \
  --neighborhood_size 0.02 \
  --num_obj 12 \
  --min_size 2000 \
  --rectangular \
  --standardize \
  --compress ZSTD
```

## Troubleshooting

### Error: "CUDA_HOME environment variable is not set"

**Solution**: Install CUDA and set environment variables (see SETUP.md)

```bash
export CUDA_HOME=/usr/local/cuda
export PATH=$PATH:$CUDA_HOME/bin
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CUDA_HOME/lib64
```

### Error: "CUDA out of memory"

**Solution**: Reduce data size or use tiling
- Downsample rasters
- Process smaller spatial extent
- Use fewer bands
- Reduce number_of_cells

### No clusters found

**Solution**: Adjust parameters
- Increase neighborhood_size (less strict)
- Decrease min_size (allow smaller clusters)
- Check data standardization
- Verify valid pixel count

### Too many small clusters

**Solution**: 
- Increase min_size
- Decrease neighborhood_size (stricter)
- Adjust F parameter

### Segmentation fault / Program crash

**Solution**: Parameter mismatch or data size issues
- **Reduce neighborhood_size**: Try values like 0.001, 0.005, 0.01 first
- **Increase min_size**: Should be at least 0.5-1% of valid pixels
- **Increase data size**: Very small datasets (<10k pixels) may be unstable
- **Check dataset size**: Ensure you have sufficient valid pixels (>10,000 recommended)
- **Try different variant**: GPU_INSCY_memory is most stable
- **Ensure data is standardized**: Use `--standardize` flag

## References

- **GPU_INSCY Paper**: "GPU-INSCY: A GPU-Parallel Algorithm and Tree Structure for Efficient Density-based Subspace Clustering"
- **Original Repository**: https://github.com/jakobrj/GPU_INSCY
- **Contact**: jakobrj@cs.au.dk

## See Also

- [SETUP.md](SETUP.md) - GPU_INSCY installation
- [QUICKSTART.md](QUICKSTART.md) - Quick setup guide
- [README.md](README.md) - GPU_INSCY overview
