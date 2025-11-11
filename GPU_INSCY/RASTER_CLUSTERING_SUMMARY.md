# GPU_INSCY Raster Clustering - Quick Summary

## What is it?

A production-ready Python script that applies GPU_INSCY density-based subspace clustering to geospatial raster data (multi-band GeoTIFF imagery).

## When to use it?

- Multi-band satellite/aerial imagery (Landsat, Sentinel, etc.)
- Hyperspectral data (100+ bands)
- Multi-temporal analysis (time series of images)
- Any geospatial data where clusters exist in subsets of bands

## Quick Start

```bash
# Basic usage
python raster_clustering.py \
  --root_dir /data/my_imagery \
  --output_tif /output/clusters.tif \
  --inscy_dir /path/to/GPU_INSCY \
  --standardize

# With full options
python raster_clustering.py \
  --root_dir /data/imagery \
  --output_tif /output/clusters.tif \
  --artifacts_dir /output/artifacts \
  --inscy_dir /path/to/GPU_INSCY \
  --variant GPU_INSCY_memory \
  --neighborhood_size 0.01 \
  --num_obj 8 \
  --min_size 1000 \
  --standardize \
  --compress LZW
```

## Key Parameters

| Parameter | Description | Typical Values |
|-----------|-------------|----------------|
| `--neighborhood_size` | Density radius (like DBSCAN epsilon) | 0.01 - 0.05 |
| `--num_obj` | Min objects in neighborhood | 8 - 15 |
| `--min_size` | Min cluster size (pixels) | 100 - 5000 |
| `--variant` | Algorithm version | GPU_INSCY_memory |
| `--standardize` | Z-score per band | Always use |

## How it works

1. **Discovers** all GeoTIFF files in directory (each file = one band)
2. **Reads** data by tiles (memory efficient)
3. **Standardizes** each band (z-score normalization)
4. **Transfers** to GPU as torch.cuda tensor
5. **Clusters** using GPU_INSCY (stays on GPU)
6. **Outputs** cluster labels as GeoTIFF + JSON artifacts

## What makes it different?

### vs GPU_PROCLUS
- **Method**: Density-based (DBSCAN-like) vs medoid-based (k-means-like)
- **Subspaces**: Auto-discovered vs fixed l dimensions
- **Output**: Multiple clusterings (one per subspace) vs single clustering
- **Parameters**: neighborhood_size, min_size vs k, l

### vs Regular Clustering
- **Subspace awareness**: Finds clusters in different band combinations
- **Density-based**: No need to specify number of clusters
- **GPU-accelerated**: 10-100x faster than CPU
- **Scales**: Handles millions of pixels × dozens of bands

## Output

### GeoTIFF Labels
- int32 raster with cluster IDs
- -1 = NODATA or unclustered
- 0, 1, 2, ... = cluster IDs
- Preserves georeference from input

### JSON Artifacts (optional)
```json
{
  "variant": "GPU_INSCY_memory",
  "params": {...},
  "subspaces": [[0,1,2], [3,4,5]],
  "label_summary": {
    "labeled_pixels": 950000,
    "non_empty_clusters": 15,
    "top_clusters": [...]
  }
}
```

## Understanding Results

GPU_INSCY finds **multiple clusterings**, each in a different subspace:
- Subspace 1: bands [0,2,5] → 8 clusters
- Subspace 2: bands [1,3,4,7] → 5 clusters
- Subspace 3: bands [6,8,9] → 3 clusters

Use `--output_subspace_idx` to select:
- `0` = largest subspace (default)
- `1,2,...` = specific subspace
- `-1` = combine all

## Example Workflows

### Land Cover Classification
```bash
python raster_clustering.py \
  --root_dir /data/landsat_scene \
  --output_tif /output/landcover.tif \
  --inscy_dir ./GPU_INSCY \
  --neighborhood_size 0.015 \
  --min_size 500 \
  --standardize
```

### Hyperspectral Analysis
```bash
python raster_clustering.py \
  --root_dir /data/hyperspectral \
  --output_tif /output/materials.tif \
  --inscy_dir ./GPU_INSCY \
  --neighborhood_size 0.01 \
  --F 1.5 \
  --output_subspace_idx -1 \
  --standardize
```

### Change Detection
```bash
python raster_clustering.py \
  --root_dir /data/timeseries \
  --output_tif /output/changes.tif \
  --inscy_dir ./GPU_INSCY \
  --neighborhood_size 0.02 \
  --min_size 2000 \
  --standardize
```

## Requirements

- Python 3.7+
- PyTorch with CUDA
- Rasterio
- CUDA-capable GPU

```bash
pip install -r requirements.txt
pip install rasterio
```

## Files

- **raster_clustering.py** - Main script (16KB)
- **RASTER_CLUSTERING.md** - Full documentation (10KB)
- **example_raster_clustering.py** - Demo with synthetic data (5KB)

## Performance

- **First run**: 1-2 min for JIT compilation (cached after)
- **Memory**: ~4 bytes × pixels × bands on GPU
- **Speed**: GPU_INSCY_memory fastest for large datasets
- **Example**: 10k×10k pixels × 10 bands = 4GB GPU memory

## Troubleshooting

| Issue | Solution |
|-------|----------|
| CUDA out of memory | Reduce image size or bands |
| No clusters found | Increase neighborhood_size |
| Too many clusters | Increase min_size |
| CUDA not available | Install CUDA (see SETUP.md) |

## Documentation

- [RASTER_CLUSTERING.md](RASTER_CLUSTERING.md) - Complete guide
- [SETUP.md](../SETUP.md) - Installation
- [QUICKSTART.md](../QUICKSTART.md) - GPU_INSCY basics

## Origin

Adapted from user's GPU_PROCLUS raster clustering API, maintaining the same interface pattern while leveraging GPU_INSCY's density-based subspace clustering capabilities.
