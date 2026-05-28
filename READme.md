# PCAP to Image Dataset Creator

A Python toolkit for converting PCAP files into fixed-size grayscale images for machine learning datasets, with support for nested directory structures.

## Repository Structure

```
.
├── 0_pcap/                 # Original PCAP files (input)
│   ├── malware/           # Example: nested structure
│   │   ├── trojan/
│   │   └── ransomware/
│   └── benign/
├── 1_splitted_pcap/        # Split PCAP files (preserves structure)
│   ├── malware/
│   │   ├── trojan/
│   │   └── ransomware/
│   └── benign/
├── 2_Images/               # Generated images (preserves structure)
│   ├── malware/
│   │   ├── trojan/
│   │   └── ransomware/
│   └── benign/
├── split_pcap.py           # Script to split PCAP files
├── pcap_to_image.py        # Script to convert PCAP to images
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Installation

1. **Clone or create the repository:**
```bash
mkdir pcap-dataset-creator
cd pcap-dataset-creator
```

2. **Create the directory structure:**
```bash
mkdir -p 0_pcap 1_splitted_pcap 2_Images
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

## Requirements

The `requirements.txt` file contains:
```
scapy>=2.5.0
numpy>=1.21.0
Pillow>=9.0.0
```

## Usage

### Step 1: Split PCAP Files

Split PCAP files by session or flow, with automatic trimming/padding to 800 bits (100 bytes):

**Process a single file:**
```bash
python split_pcap.py 0_pcap/capture.pcap --mode session --max-bits 800
```

**Process entire directory tree (preserves nested structure):**
```bash
python split_pcap.py 0_pcap/ --mode session --max-bits 800
```

**Custom bit size:**
```bash
python split_pcap.py 0_pcap/ --mode flow --max-bits 1600
```

### Step 2: Convert to Images

Convert split PCAP files to fixed-size grayscale images:

**Full packet mode with 28x28 images:**
```bash
python pcap_to_image.py --mode full --size 28x28
```

**Header-only mode with custom size:**
```bash
python pcap_to_image.py --mode header --size 32x32
```

**Custom input/output directories:**
```bash
python pcap_to_image.py --input 1_splitted_pcap --output 2_Images --mode full --size 64x64
```

### Parameters

#### split_pcap.py
- `input`: Input PCAP file or directory path (required)
- `--mode`: Split mode - `session` (bidirectional) or `flow` (unidirectional) [default: session]
- `--output`: Output base directory [default: 1_splitted_pcap]
- `--max-bits`: Maximum bits per split file, will trim or pad to this exact size [default: 800]

#### pcap_to_image.py
- `--input`: Input directory with PCAP files [default: 1_splitted_pcap]
- `--output`: Output directory for images [default: 2_Images]
- `--mode`: Conversion mode - `header` (headers only) or `full` (entire packet) [default: full]
- `--size`: Image dimensions as WIDTHxHEIGHT (e.g., 28x28, 32x32, 64x64) [default: 28x28]

## Complete Workflow Example

### Simple (Single File)
```bash
# Place PCAP in 0_pcap/
cp capture.pcap 0_pcap/

# Split by sessions (800 bits each)
python split_pcap.py 0_pcap/capture.pcap --mode session --max-bits 800

# Convert to 28x28 images (full packet)
python pcap_to_image.py --mode full --size 28x28
```

### Advanced (Nested Directory Structure)
```bash
# Organize your PCAPs by category
0_pcap/
├── malware/
│   ├── trojan/
│   │   ├── sample1.pcap
│   │   └── sample2.pcap
│   └── ransomware/
│       └── sample3.pcap
└── benign/
    └── normal_traffic.pcap

# Split all files, preserving structure
python split_pcap.py 0_pcap/ --mode session --max-bits 800

# Result in 1_splitted_pcap/:
1_splitted_pcap/
├── malware/
│   ├── trojan/
│   │   ├── sample1_20241216_143052_session_0001.pcap
│   │   ├── sample1_20241216_143052_session_0002.pcap
│   │   └── ...
│   └── ransomware/
│       └── ...
└── benign/
    └── ...

# Convert to images, preserving structure
python pcap_to_image.py --mode full --size 32x32

# Result in 2_Images/:
2_Images/
├── malware/
│   ├── trojan/
│   │   ├── sample1_20241216_143052_session_0001.png
│   │   ├── sample1_20241216_143052_session_0002.png
│   │   └── ...
│   └── ransomware/
│       └── ...
└── benign/
    └── ...
```

## Key Features

### 🎯 Fixed Size Processing
- **Bit-level control**: Specify exact bit size (default: 800 bits = 100 bytes)
- **Automatic trimming**: Files larger than max-bits are truncated
- **Automatic padding**: Files smaller than max-bits are zero-padded
- **Perfect uniformity**: All split PCAPs are exactly the same size

### 📊 Image Generation
- **Fixed dimensions**: Specify exact image size (e.g., 28x28, 32x32, 64x64)
- **Automatic trimming**: Data exceeding image size is cut off
- **Automatic padding**: Data smaller than image size is zero-padded
- **Dataset-ready**: All images have identical dimensions

### 📁 Directory Structure Preservation
- **Nested folders**: Automatically preserves nested directory structure
- **Organized datasets**: Maintains your classification/labeling hierarchy
- **Batch processing**: Processes entire directory trees recursively

### 🔍 Flexible Extraction
- **Header mode**: Extract only packet headers (Ethernet + IP + TCP/UDP)
- **Full mode**: Extract complete packet data including payload
- **Privacy control**: Use header mode to exclude sensitive payload data

## Calculation Examples

### Bit Size to Image Size
```
800 bits = 100 bytes
→ 10x10 image (100 pixels)
→ 28x28 image (784 pixels) - requires padding
→ 8x12 image (96 pixels) - requires trimming

1600 bits = 200 bytes
→ 14x14 image (196 pixels) - requires padding
→ 10x20 image (200 pixels) - perfect fit!
```

### Common Configurations
```bash
# Small images (MNIST-style)
--max-bits 784 --size 28x28  # 784 bits = 98 bytes, perfect fit

# Medium images
--max-bits 1024 --size 32x32  # 1024 pixels = 128 bytes

# Larger images
--max-bits 4096 --size 64x64  # 4096 pixels = 512 bytes
```

## Session vs Flow

- **Session mode**: Groups packets bidirectionally (both directions of communication)
  - Better for: Protocol analysis, connection behavior
  - Fewer files, more context per file
  - Example: All packets between 192.168.1.10:443 ↔ 10.0.0.5:8080

- **Flow mode**: Keeps each direction separate
  - Better for: Asymmetric analysis, one-way traffic patterns
  - More files, more granular control
  - Example: 192.168.1.10:443 → 10.0.0.5:8080 (separate from reverse)

## Header vs Full Packet

- **Header mode**: Only packet headers
  - Ethernet (14 bytes) + IP (20-60 bytes) + TCP/UDP (20-60 / 8 bytes)
  - Typically 42-134 bytes per packet
  - Privacy-preserving (no payload data)
  - Good for protocol-based classification

- **Full mode**: Complete packet data
  - Headers + payload
  - Variable size depending on packet
  - Better for deep packet inspection
  - Includes application-layer data

## Output Format

### Split PCAP Files
- **Naming**: `{original}_{timestamp}_{mode}_{index}.pcap`
- **Example**: `capture_20241216_143052_session_0001.pcap`
- **Size**: Exactly `max-bits` bits (trimmed or padded)

### Images
- **Format**: PNG (grayscale, 8-bit)
- **Naming**: Same as PCAP but with `.png` extension
- **Dimensions**: Exactly as specified (e.g., 28x28)
- **Pixel values**: 0-255 (each byte becomes one pixel value)

## Use Cases

- **Network intrusion detection**: Train CNNs on packet patterns
- **Traffic classification**: Identify applications from packet headers
- **Malware detection**: Analyze C&C communication patterns
- **Protocol fingerprinting**: Visual signatures of network protocols
- **Anomaly detection**: Identify unusual network behavior

## Tips

1. **Choose appropriate max-bits**: 
   - 800 bits works well for header-only analysis
   - 1600-3200 bits better for full packet analysis

2. **Match max-bits to image size**:
   - 28x28 = 784 bytes = 6,272 bits
   - Recommended: `--max-bits 6272 --size 28x28`

3. **Directory organization**:
   - Organize by traffic type (malware/benign)
   - Organize by protocol (HTTP/SSH/DNS)
   - Scripts preserve any structure you create

4. **Header mode benefits**:
   - Faster processing
   - Privacy-compliant (no payload)
   - Smaller files

## Troubleshooting

### Common Issues

**"No module named 'scapy'"**
```bash
pip install -r requirements.txt
```

**"Permission denied" when reading PCAP**
```bash
# On Linux/Mac, you may need sudo for some PCAPs
sudo python split_pcap.py 0_pcap/capture.pcap
```

**Images look random/noisy**
- This is normal! Network traffic as images appears random
- ML models learn patterns humans can't see
- Try different modes (header vs full) to see differences

**Empty output directories**
- Check that input PCAPs contain IP traffic
- Non-IP packets are filtered out
- Check file permissions

## License

MIT License - Feel free to use and modify for your projects.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Citation

If you use this tool in your research, please cite:

```
@software{pcap_to_image_dataset,
  title = {PCAP to Image Dataset Creator},
  year = {2024},
  url = {https://github.com/yourusername/pcap-dataset-creator}
}
```

## Linked to

This code is part of the following paper:

```
@inproceedings{camerota2024addressing,
  title={Addressing data security in iot: Minimum sample size and denoising diffusion models for improved malware detection},
  author={Camerota, Chiara and Pappone, Lorenzo and Pecorella, Tommaso and Esposito, Flavio},
  booktitle={2024 20th International Conference on Network and Service Management (CNSM)},
  pages={1--7},
  year={2024},
  organization={IEEE}
}
```
