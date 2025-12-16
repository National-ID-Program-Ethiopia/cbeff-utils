# MOSIP Bio Utils Python Client

Python client for converting CBEFF/ISO19794 biometric data to images via MOSIP Bio Utils REST service.

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Process All BIRs from CBEFF XML (Recommended)

Process all biometric records and save each with subtype as filename:

```bash
python bio_utils_client.py \
    --format cbeff \
    --input cbeff.xml \
    --all-birs \
    --output-dir ./output_images
```

### Convert Single CBEFF File

```bash
# CBEFF XML
python bio_utils_client.py \
    --format cbeff \
    --input cbeff.xml \
    --output fingerprint.jpg

# Base64 CBEFF
python bio_utils_client.py \
    --format cbeff \
    --input cbeff.txt \
    --output fingerprint.jpg
```

### Python API

```python
from bio_utils_client import BioUtilsClient

client = BioUtilsClient(base_url="http://localhost:8080")

# Process all BIRs from XML
results = client.convert_cbeff_xml_all_birs_from_file(
    cbeff_file_path="cbeff.xml",
    output_dir="./output_images"
)
# Returns: {"Left Thumb": "output_images/Left_Thumb.jpg", ...}

# Convert single CBEFF
with open("cbeff.xml", "r") as f:
    image_bytes = client.convert_cbeff_to_image(
        cbeff_base64=f.read(),
        output_path="fingerprint.jpg"
    )
```

## Command Line Options

- `--url`: REST service URL (default: `http://localhost:8080`)
- `--input`: Input file path (required)
- `--format`: `iso` or `cbeff` (default: `cbeff`)
- `--output`: Output image file (required unless `--all-birs`)
- `--output-dir`: Output directory for `--all-birs` mode (default: `.`)
- `--all-birs`: Process all BIR elements (CBEFF XML only)
- `--modality`: `FINGER`, `IRIS`, or `FACE` (optional for CBEFF)
- `--iso-version`: ISO version (optional for CBEFF)
- `--compression`: Compression ratio 1-100 (default: 95)

## Supported Formats

- **CBEFF XML**: Automatically extracts modality and ISO bytes
- **Base64 CBEFF**: Binary CBEFF encoded as base64
- **ISO19794**: Direct ISO files (requires modality and version)

## Examples

See `example_usage.py` for more examples.
