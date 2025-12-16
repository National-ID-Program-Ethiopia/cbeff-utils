# MOSIP Bio Utils REST Service

REST service for converting ISO19794/CBEFF biometric data to JPEG/PNG images using MOSIP Bio Utils.

## Quick Start

### Java Service

```bash
# Build
mvn clean package

# Run
java -jar target/bio-utils-rest-service-1.0.0.jar
```

Service runs on `http://localhost:8080`

### Python Client

```bash
cd python
pip install -r requirements.txt

# Process all BIRs from CBEFF XML
python bio_utils_client.py \
    --format cbeff \
    --input cbeff.xml \
    --all-birs \
    --output-dir ./output_images

# Convert single file
python bio_utils_client.py \
    --format cbeff \
    --input cbeff.xml \
    --output fingerprint.jpg
```

## API

### POST `/bio-utils/iso-to-image`

Convert ISO19794 bytes to image.

**Request:**
```json
{
  "modality": "FINGER",
  "isoVersion": "ISO19794_4_2011",
  "isoBase64": "base64-encoded-iso-bytes",
  "compressionRatio": 95
}
```

**Response:** JPEG/PNG image bytes

### GET `/bio-utils/health`

Health check endpoint.

## Features

- CBEFF XML and base64 support
- Process all BIRs from XML (saves with subtype as filename)
- FINGER, IRIS, FACE modalities
- Auto-detects modality and ISO version
- Python client included

## Supported Formats

- **CBEFF XML**: Full XML with multiple BIR elements
- **Base64 CBEFF**: Binary CBEFF encoded as base64
- **ISO19794**: Direct ISO files

## Configuration

Edit `src/main/resources/application.yml`:

```yaml
server:
  port: 8080
  servlet:
    multipart:
      max-file-size: 10MB
```

## Docker

```bash
docker build -t bio-utils-service .
docker run -p 8080:8080 bio-utils-service
```

## Project Structure

```
cbeff-utils/
├── src/main/java/          # Java REST service
├── python/                 # Python client
│   ├── bio_utils_client.py
│   └── README.md
├── pom.xml
└── Dockerfile
```

## Dependencies

- Java 11+
- Spring Boot 2.7.18
- MOSIP biometrics-util 1.2.0
- Python 3.7+ (for client)

See `python/README.md` for detailed Python client documentation.
