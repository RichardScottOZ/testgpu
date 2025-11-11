# GPU-INSCY
Implementation of GPU-INSCY from the article "GPU-INSCY: A GPU-Parallel Algorithm and Tree Structure for Efficient Density-based Subspace Clustering".

## Requirements
The original implementation was tested on a workstation with Ubuntu 20.4 LTS and CUDA 10.1.

**Windows 11 Support**: This version has been refactored to work on Windows 11. 
- **Quick Start**: See [QUICKSTART_WINDOWS.md](QUICKSTART_WINDOWS.md) for step-by-step installation
- **Details**: See [README_WINDOWS.md](README_WINDOWS.md) for complete Windows documentation and troubleshooting

The important packages used are: torch=1.6.0, numpy=1.19.2, matplotlib=3.3.2, pandas=1.1.3, and ninja=1.10.0. However, it should work for newer versions.

Install the newest versions:
```
pip install -r requirements.txt
```

**Windows Users**: Run the setup checker to verify your environment:
```
python check_windows_setup.py
```

## Example
The implementation comes with three real-world datasets vowel, glass, and pendigits.

Run a small example with INSCY, GPU-INSCY, GPU-INSCY*, and GPU-INSCY-memory, on the datasets vowel and glass:
```
python run_example.py
```
Running the script should take around 5 minutes and result in a plot of the average running times.
The pendigits dataset is not a part of the example since it would take around 8 hours for INSCY to process.

![plot](example.png)

## Contact
If you have any difficulties you can contact us at: jakobrj@cs.au.dk
