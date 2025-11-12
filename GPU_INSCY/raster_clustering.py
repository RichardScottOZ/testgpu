#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Directory-based raster clustering using GPU_INSCY (density-based subspace clustering).

Pattern:
  discover rasters (each file = one band, same H×W/transform/CRS)
  -> read by tiles with rasterio
  -> optional z-score standardize
  -> build dense (N,B) features
  -> move to torch.cuda
  -> run GPU_INSCY (or chosen variant)
  -> write labels GeoTIFF + JSON artifacts

Environment: Ubuntu, Python 3.7+, PyTorch with CUDA, Rasterio, NumPy.

GPU_INSCY performs density-based subspace clustering, finding clusters that exist
in subspaces (subsets of dimensions/bands). Returns multiple clusterings, one per
discovered subspace.
"""
import os
import re
import sys
import json
import argparse
from pathlib import Path

import numpy as np
import rasterio as rio
from rasterio.windows import Window
import torch

from inscy import *


# ---------- CLI ----------
def get_args():
    p = argparse.ArgumentParser(description="GPU_INSCY subspace clustering over rasters in a directory")
    p.add_argument("--root_dir", required=True, help="Root directory to walk for *.tif/*.tiff (each file = one band)")
    p.add_argument("--include_dirs_regex", default="", help="Regex to include subdirs")
    p.add_argument("--exclude_dirs_regex", default="", help="Regex to exclude subdirs")

    p.add_argument("--output_tif", required=True, help="Output GeoTIFF of cluster labels (int32, nodata=-1)")
    p.add_argument("--artifacts_dir", default="", help="Optional: directory to write JSON artifacts")

    # GPU_INSCY params
    p.add_argument("--variant",
                   choices=["GPU_INSCY", "GPU_INSCY_star", "GPU_INSCY_memory", "INSCY"],
                   default="GPU_INSCY_memory",
                   help="Algorithm variant to use (default: GPU_INSCY_memory)")
    p.add_argument("--neighborhood_size", type=float, default=0.01, 
                   help="Neighborhood size (epsilon) for density-based clustering")
    p.add_argument("--F", type=float, default=1.0, 
                   help="F parameter (threshold for dimension selection)")
    p.add_argument("--num_obj", type=int, default=8, 
                   help="Number of objects parameter")
    p.add_argument("--min_size", type=int, default=None, 
                   help="Minimum cluster size (absolute count). If None, uses 5%% of N")
    p.add_argument("--r", type=float, default=1.0, 
                   help="R parameter")
    p.add_argument("--number_of_cells", type=int, default=4, 
                   help="Number of cells for spatial indexing")
    p.add_argument("--rectangular", action="store_true", 
                   help="Use rectangular neighborhoods (recommended - all examples use this)")

    # Subspace selection for output
    p.add_argument("--output_subspace_idx", type=int, default=0,
                   help="Which subspace clustering to output (0 = largest, -1 = all combined)")

    # I/O & performance
    p.add_argument("--tile_rows", type=int, default=512, help="Rows per tile when reading (CPU)")
    p.add_argument("--standardize", action="store_true", help="Z-score per band before clustering (recommended)")
    p.add_argument("--compress", choices=["LZW", "ZSTD", "DEFLATE", "NONE"], default="LZW")
    p.add_argument("--save_band_list", default="", help="Optional: save discovered band list (txt)")

    # Path to GPU_INSCY
    p.add_argument("--inscy_dir", required=True, 
                   help="Path to GPU_INSCY directory (containing inscy.py)")

    return p.parse_args()


# ---------- Discovery ----------
def discover_tifs(root: Path, inc_regex: str, exc_regex: str):
    inc = re.compile(inc_regex) if inc_regex else None
    exc = re.compile(exc_regex) if exc_regex else None
    tifs = []
    for dirpath, _, filenames in os.walk(root):
        dname = Path(dirpath).name
        if inc and not inc.search(dname):
            continue
        if exc and exc.search(dname):
            continue
        for f in filenames:
            if f.lower().endswith((".tif", ".tiff")):
                tifs.append(Path(dirpath) / f)
    tifs = sorted(tifs)
    if not tifs:
        raise FileNotFoundError(f"No GeoTIFFs found under {root}")
    return tifs


# ---------- Read, stats, features (NumPy + Torch) ----------
def read_geometry_meta(first_path: Path):
    with rio.open(first_path) as ds0:
        meta = ds0.meta.copy()
        H, W = ds0.height, ds0.width
    return H, W, meta


def compute_band_stats_cpu(paths, H, W, tile_rows):
    """Return (means, stds) as NumPy float32 vectors of length B. Skips NODATA/NaN."""
    B = len(paths)
    sums = np.zeros(B, dtype=np.float64)
    sumsqs = np.zeros(B, dtype=np.float64)
    counts = np.zeros(B, dtype=np.int64)

    dsets = [rio.open(p) for p in paths]
    try:
        nodatas = [ds.nodata for ds in dsets]
        for r0 in range(0, H, tile_rows):
            h = min(tile_rows, H - r0)
            cols = []
            masks = []
            for j, ds in enumerate(dsets):
                band = ds.read(1, window=Window(0, r0, W, h))
                c = band.reshape(-1)
                cols.append(c)
                nd = nodatas[j]
                if nd is not None and not np.isnan(nd):
                    m = (c == nd)
                else:
                    m = np.isnan(c) if np.issubdtype(c.dtype, np.floating) else np.zeros_like(c, dtype=bool)
                masks.append(m)
            Xb = np.stack(cols, axis=1)
            mask = masks[0].copy()
            for m in masks[1:]:
                mask |= m
            valid = ~mask
            if valid.any():
                Xv = Xb[valid]
                sums += Xv.sum(axis=0, dtype=np.float64)
                sumsqs += (Xv.astype(np.float64) ** 2).sum(axis=0, dtype=np.float64)
                counts += Xv.shape[0]
    finally:
        for ds in dsets:
            ds.close()

    means = sums / np.maximum(counts, 1)
    var = np.maximum(sumsqs / np.maximum(counts, 1) - means ** 2, 1e-12)
    stds = np.sqrt(var).astype(np.float32)
    return means.astype(np.float32), stds


def build_features(paths, H, W, tile_rows, means, stds, standardize=True):
    """
    Returns:
      X_cpu: (N,B) float32 NumPy array
      valid_mask: (N,) bool, True where all bands valid
    """
    B = len(paths)
    N = H * W
    X = np.empty((N, B), dtype=np.float32)
    valid_mask = np.ones(N, dtype=bool)

    dsets = [rio.open(p) for p in paths]
    try:
        nodatas = [ds.nodata for ds in dsets]
        base = 0
        for r0 in range(0, H, tile_rows):
            h = min(tile_rows, H - r0)
            cols = []
            masks = []
            for j, ds in enumerate(dsets):
                band = ds.read(1, window=Window(0, r0, W, h))
                c = band.reshape(-1).astype(np.float32, copy=False)
                cols.append(c)
                nd = nodatas[j]
                if nd is not None and not np.isnan(nd):
                    m = (c == nd)
                else:
                    m = np.isnan(c) if np.issubdtype(c.dtype, np.floating) else np.zeros_like(c, dtype=bool)
                masks.append(m)
            Xb = np.stack(cols, axis=1)
            mask = masks[0].copy()
            for m in masks[1:]:
                mask |= m
            if standardize:
                Xb_valid = Xb[~mask]
                if Xb_valid.shape[0] > 0:
                    Xb[~mask] = (Xb_valid - means) / stds
            X[base:base + h * W, :] = Xb
            valid_mask[base:base + h * W] = ~mask
            base += h * W
    finally:
        for ds in dsets:
            ds.close()

    return X, valid_mask


# ---------- GPU_INSCY integration ----------
def import_inscy(inscy_dir: Path):
    """Import GPU_INSCY module from specified directory."""
    sys.path.insert(0, str(inscy_dir))
    from inscy import INSCY, GPU_INSCY, GPU_INSCY_star, GPU_INSCY_memory
    return {
        "INSCY": INSCY,
        "GPU_INSCY": GPU_INSCY,
        "GPU_INSCY_star": GPU_INSCY_star,
        "GPU_INSCY_memory": GPU_INSCY_memory,
    }


def write_labels_tif(labels_dense: np.ndarray, H: int, W: int, meta: dict, out_tif: str, compress="LZW"):
    """Write cluster labels as GeoTIFF."""
    img = labels_dense.reshape(H, W)
    meta2 = meta.copy()
    meta2.update(count=1, dtype='int32', nodata=-1)
    if compress != "NONE":
        meta2.update(compress=compress, tiled=True)
    with rio.open(out_tif, 'w', **meta2) as dst:
        dst.write(img, 1)


def main():
    args = get_args()
    root = Path(args.root_dir)

    Path(args.output_tif).parent.mkdir(parents=True, exist_ok=True)
    if args.artifacts_dir:
        Path(args.artifacts_dir).mkdir(parents=True, exist_ok=True)

    # Discover rasters
    paths = discover_tifs(root, args.include_dirs_regex, args.exclude_dirs_regex)
    if args.save_band_list:
        Path(args.save_band_list).write_text("\n".join(map(str, paths)), encoding="utf-8")
    print(f"[Discovery] Found {len(paths)} GeoTIFF bands.")

    # Geometry/meta
    H, W, meta = read_geometry_meta(paths[0])
    N, B = H * W, len(paths)
    print(f"[Info] Grid H={H} W={W} N={N} Bands={B}")

    # Stats (CPU)
    if args.standardize:
        means, stds = compute_band_stats_cpu(paths, H, W, args.tile_rows)
        print("[Stats] Per-band mean/std computed on CPU.")
    else:
        means = np.zeros(B, dtype=np.float32)
        stds = np.ones(B, dtype=np.float32)

    # Features (CPU)
    X_cpu, valid_mask = build_features(paths, H, W, args.tile_rows, means, stds, standardize=args.standardize)
    valid_count = int(valid_mask.sum())
    invalid_count = N - valid_count
    print(f"[Features] Built CPU feature matrix: shape={X_cpu.shape}, valid pixels={valid_count:,}, invalid={invalid_count:,}")

    # Filter to valid pixels only for clustering
    X_valid_cpu = X_cpu[valid_mask]
    print(f"[Features] Filtered to valid pixels: shape={X_valid_cpu.shape}")

    # Ensure data is contiguous in memory
    if not X_valid_cpu.flags['C_CONTIGUOUS']:
        X_valid_cpu = np.ascontiguousarray(X_valid_cpu)
        print("[Features] Made array contiguous")

    # Torch tensor on GPU
    X_torch = torch.from_numpy(X_valid_cpu).pin_memory()
    #X = X_torch.to(device="cuda", dtype=torch.float32, non_blocking=True)
    X = X_torch
    
    # Ensure CUDA tensor is contiguous
    if not X.is_contiguous():
        X = X.contiguous()
    
    print(f"[GPU] Moved data to CUDA device: {X.shape}")
    
    # Normalize to [0,1] range per band (like GPU_INSCY examples)
    # This is CRITICAL - GPU_INSCY expects normalized data
    print(f"[Normalize] Normalizing data to [0,1] range per band...")
    min_x = X.min(0, keepdim=True)[0]
    max_x = X.max(0, keepdim=True)[0]
    X_normalized = (X - min_x) / (max_x - min_x + 1e-10)  # Add epsilon to avoid division by zero
    
    print(f"[Normalize] Data range before: [{X.min().item():.4f}, {X.max().item():.4f}]")
    print(f"[Normalize] Data range after: [{X_normalized.min().item():.4f}, {X_normalized.max().item():.4f}]")
    
    # Check for NaN or Inf values
    if torch.isnan(X_normalized).any():
        print(f"[ERROR] Normalized data contains NaN values!")
        raise ValueError("Normalized data contains NaN values")
    if torch.isinf(X_normalized).any():
        print(f"[ERROR] Normalized data contains Inf values!")
        raise ValueError("Normalized data contains Inf values")
    
    X = X_normalized
    
    # Ensure all GPU operations are complete before calling GPU_INSCY
    torch.cuda.synchronize()

    # Import GPU_INSCY variant
    inscy_map = import_inscy(Path(args.inscy_dir))
    inscy_fn = inscy_map[args.variant]

    print(inscy_fn)

    # Parameter defaults and validation
    min_size = args.min_size if args.min_size is not None else int(valid_count * 0.05)
    
    # Ensure minimum viable parameters
    if min_size < 1:
        min_size = 1
        print(f"[Warning] Adjusted min_size to 1 (minimum value)")
    
    if min_size > valid_count:
        min_size = max(1, int(valid_count * 0.05))
        print(f"[Warning] min_size exceeds data size, adjusted to {min_size}")

    # Ensure tensor is float32 (required by GPU_INSCY)
    if X.dtype != torch.float32:
        X = X.float()
        print(f"[Warning] Converted tensor to float32")
    
    # Check dataset size against GPU_INSCY's tested limits
    N, B = X.shape
    MAX_SAMPLES_TESTED = 10000  # Largest tested: pendigits ~7.5K, test.py 8K
    MAX_DIMS_TESTED = 20  # Largest tested: pendigits 17, test.py 15
    
    if N > MAX_SAMPLES_TESTED or B > MAX_DIMS_TESTED:
        print(f"\n[WARNING] ================================================")
        print(f"[WARNING] Dataset size ({N:,} × {B}) exceeds GPU_INSCY tested limits!")
        print(f"[WARNING] Tested max: {MAX_SAMPLES_TESTED:,} samples × {MAX_DIMS_TESTED} dimensions")
        print(f"[WARNING] Your data is {N/MAX_SAMPLES_TESTED:.1f}x larger in samples")
        print(f"[WARNING] Your data is {B/MAX_DIMS_TESTED:.1f}x larger in dimensions")
        print(f"[WARNING] ================================================")
        print(f"[WARNING] GPU_INSCY may crash or produce incorrect results!")
        print(f"[WARNING] Recommendations:")
        print(f"[WARNING]   1. Downsample spatially: X[::stride] to reduce samples")
        print(f"[WARNING]   2. Select top bands: X[:, band_indices] to reduce dimensions")
        print(f"[WARNING]   3. Process in spatial chunks/tiles")
        print(f"[WARNING] ================================================\n")
        
        # Don't automatically downsample - let user make the decision
        # But provide clear guidance
        if N > MAX_SAMPLES_TESTED * 100:  # More than 100x tested size
            print(f"[ERROR] Dataset is {N/MAX_SAMPLES_TESTED:.0f}x too large!")
            print(f"[ERROR] GPU_INSCY will almost certainly crash. Stopping.")
            print(f"[ERROR] Please downsample your data before running.")
            raise ValueError(f"Dataset size ({N:,} × {B}) far exceeds GPU_INSCY capacity")
    
    print(f"[GPU_INSCY] {args.variant}: neighborhood_size={args.neighborhood_size}, F={args.F}, "
          f"num_obj={args.num_obj}, min_size={min_size}, r={args.r}, "
          f"number_of_cells={args.number_of_cells}, rectangular={args.rectangular}")
    print(f"[GPU_INSCY] Input tensor: shape={X.shape}, dtype={X.dtype}, device={X.device}, contiguous={X.is_contiguous()}")
    print(f"[GPU_INSCY] Input data stats: min={X.min().item():.6f}, max={X.max().item():.6f}, mean={X.mean().item():.6f}, std={X.std().item():.6f}")
    print(f"[GPU_INSCY] Memory allocated: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")
    print(f"[GPU_INSCY] Calling {args.variant}...")
    print(f"[GPU_INSCY] Parameters: X.shape={X.shape}, neighborhood_size={args.neighborhood_size}, F={args.F}, num_obj={args.num_obj}, min_size={min_size}, r={args.r}, number_of_cells={args.number_of_cells}, rectangular={args.rectangular}")
    import sys
    sys.stdout.flush()  # Force flush before potential crash

    # ---- run GPU_INSCY ----
    print("CHECKING INPUTS")
    print(X.mean(), args.neighborhood_size, args.F, args.num_obj, min_size, args.r,  args.number_of_cells, args.rectangular)
    print("TYPES SHOULD BE:","<class 'torch.Tensor'> <class 'float'> <class 'float'> <class 'int'> <class 'int'> <class 'float'> <class 'int'>")
    print("TYPES GO IN ARE:", type(X), type(args.neighborhood_size), type(args.F), type(args.num_obj), type(min_size), type(args.r),  type(args.number_of_cells), type(args.rectangular))

    #if 1 == 2:
    if 1 == 1:
        print("TES")
        n = 8000#64000 #512000
        d = 15
        c = 4
        num_obj = 1
        F = .1
        r = 1.
        cl = max(1, n//4000)
        min_size = 500
        std = .5
        dims_pr_cl = 3

        N_size = 0.0005

        #ns =  [8*1000, 16*1000, 32*1000, 64*1000, 128*1000, 256*1000, 512*1000, 1024*1000]
        #N_sizes = [(((150)*cl/n)**(1/dims_pr_cl))*(std**(1/2))/200. for n in ns]
        #print(N_sizes)
        #n = ns[test]
        #N_size = N_sizes[test]

        XT = load_synt_gauss(n=n, d=d, cl=cl, std=std, cl_d=dims_pr_cl, re=0)
        # X = load_synt(n=n, d=d, cl=cl, cl_d=dims_pr_cl, re=0)
        n = XT.shape[0]

        if 1 == 2:
            t0 = time.time()
            rs = GPU_INSCY_memory(XT, N_size, F, num_obj, min_size, r, number_of_cells=c, rectangular=True)
            print("GPU_INSCY_memory, took: %.4fs" % (time.time() - t0))

        print("X STATS:", X.min(), X.max(), X.mean(), X.std(), X.dtype, X.shape)
        print("XT STATs:", XT.min(), XT.max(), XT.mean(), XT.std(), XT.dtype, XT.shape)

        print(XT.shape, N_size, F, num_obj, min_size, r, c)
        print(type(XT), type(N_size), type(F), type(num_obj), type(min_size), type(r), type(c))

        #quit(3)
        print(XT.shape, XT)
        #print(X.shape, X)

    try:
        print(X.dtype)
        X = X[0:8000,0:15]
        print(X.shape, X.dtype)
        
        result = inscy_fn(X, args.neighborhood_size, args.F, args.num_obj, min_size, args.r,
                         number_of_cells=args.number_of_cells, rectangular=args.rectangular)
        print(f"[GPU_INSCY] Completed successfully!")
    except Exception as e:
        print(f"[Error] GPU_INSCY failed with exception: {e}")
        print(f"[Error] Exception type: {type(e).__name__}")
        import traceback
        print(f"[Error] Traceback:")
        traceback.print_exc()
        print(f"[Error] This may be due to incompatible parameters or insufficient GPU memory.")
        print(f"[Error] Try adjusting: neighborhood_size (smaller), min_size (larger), or use fewer pixels.")
        raise

    # GPU_INSCY returns [subspaces, clusterings]
    # subspaces: list of dimension lists (e.g., [[0,1,2], [3,4,5]])
    # clusterings: list of cluster label arrays, one per subspace
    subspaces, clusterings = result[0], result[1]

    print(f"[Result] Found {len(subspaces)} subspace clusterings")
    for i, (dims, labels) in enumerate(zip(subspaces, clusterings)):
        # Convert to numpy if needed
        if torch.is_tensor(labels):
            labels_np = labels.detach().cpu().numpy()
        else:
            labels_np = np.array(labels)
        
        n_clusters = len(np.unique(labels_np[labels_np >= 0]))
        print(f"  Subspace {i}: dims={dims} (n={len(dims)}), clusters={n_clusters}, "
              f"labeled={int((labels_np >= 0).sum()):,}/{len(labels_np):,}")

    # Select which subspace clustering to output
    if len(subspaces) == 0:
        print("[Warning] No subspace clusters found. Writing empty labels.")
        dense = np.full(N, -1, dtype=np.int32)
    else:
        if args.output_subspace_idx == -1:
            # Combine all subspace clusterings (take first non-negative label)
            print("[Output] Combining all subspace clusterings...")
            combined = np.full(valid_count, -1, dtype=np.int32)
            for i, labels in enumerate(clusterings):
                if torch.is_tensor(labels):
                    labels_np = labels.detach().cpu().numpy().astype(np.int32)
                else:
                    labels_np = np.array(labels, dtype=np.int32)
                # Offset cluster IDs to avoid conflicts
                labels_np[labels_np >= 0] += i * 10000
                # Update combined where still unlabeled
                mask = (combined < 0) & (labels_np >= 0)
                combined[mask] = labels_np[mask]
            selected_labels = combined
            selected_subspace = "combined"
        else:
            # Use specific subspace
            idx = args.output_subspace_idx
            if idx >= len(subspaces):
                print(f"[Warning] Requested subspace {idx} but only {len(subspaces)} found. Using subspace 0.")
                idx = 0
            selected_labels = clusterings[idx]
            if torch.is_tensor(selected_labels):
                selected_labels = selected_labels.detach().cpu().numpy().astype(np.int32)
            else:
                selected_labels = np.array(selected_labels, dtype=np.int32)
            selected_subspace = subspaces[idx]
            print(f"[Output] Using subspace {idx}: dims={selected_subspace}")

        # Densify to full N with -1 at invalid pixels
        dense = np.full(N, -1, dtype=np.int32)
        dense[valid_mask] = selected_labels

    # Cluster statistics
    valid_labels = dense[dense >= 0]
    if valid_labels.size == 0:
        print("[Summary] No labeled pixels (all nodata or no clusters found)")
    else:
        counts = np.bincount(valid_labels)
        n_clusters = counts.size
        total_labeled = int(valid_labels.size)
        top_k = 10

        order = np.argsort(counts)[::-1]
        largest = [(int(cid), int(counts[cid])) for cid in order[:top_k]]

        print(f"[Summary] Labeled pixels: {total_labeled:,}  |  Non-labeled (nodata): {(dense < 0).sum():,}")
        print(f"[Summary] Non-empty clusters: {n_clusters}")
        print("[Summary] Top clusters by size:", ", ".join([f"{cid}:{cnt:,}" for cid, cnt in largest]))

    # Write GeoTIFF
    write_labels_tif(dense, H, W, meta, args.output_tif, args.compress)
    print(f"[Done] Wrote labels GeoTIFF: {args.output_tif}")

    # Artifacts
    if args.artifacts_dir:
        outdir = Path(args.artifacts_dir)
        outdir.mkdir(parents=True, exist_ok=True)

        def _to_list(x):
            if x is None:
                return []
            if torch.is_tensor(x):
                return x.detach().cpu().tolist()
            if isinstance(x, np.ndarray):
                return x.tolist()
            return x

        artifacts = {
            "variant": args.variant,
            "params": {
                "neighborhood_size": args.neighborhood_size,
                "F": args.F,
                "num_obj": args.num_obj,
                "min_size": min_size,
                "r": args.r,
                "number_of_cells": args.number_of_cells,
                "rectangular": args.rectangular
            },
            "bands": [str(p) for p in paths],
            "grid": {"H": H, "W": W, "N": int(N), "B": int(B)},
            "invalid_pixels": int((~valid_mask).sum()),
            "subspaces": [_to_list(s) for s in subspaces],
            "output_subspace": str(selected_subspace)
        }

        # Cluster counts
        valid_labels = dense[dense >= 0]
        if valid_labels.size > 0:
            counts = np.bincount(valid_labels)
            order = np.argsort(counts)[::-1]
            top_k = 50
            largest = [{"cluster_id": int(cid), "count": int(counts[cid])} for cid in order[:top_k]]
        else:
            counts = np.array([], dtype=np.int64)
            largest = []

        artifacts.update({
            "label_summary": {
                "total_pixels": int(dense.size),
                "labeled_pixels": int((dense >= 0).sum()),
                "nodata_pixels": int((dense < 0).sum()),
                "non_empty_clusters": int(counts.size),
                "top_clusters": largest
            }
        })

        (outdir / "inscy_artifacts.json").write_text(json.dumps(artifacts, indent=2))
        print(f"[Artifacts] {outdir / 'inscy_artifacts.json'}")


if __name__ == "__main__":
    main()
