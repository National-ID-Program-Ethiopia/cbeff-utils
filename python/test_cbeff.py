#!/usr/bin/env python3
"""
Quick test script for CBEFF conversion

This script demonstrates how to use the Python client with a base64 encoded CBEFF file.
"""

from bio_utils_client import BioUtilsClient
import sys

def test_cbeff_conversion(cbeff_file_path: str, output_path: str = "output.jpg"):
    """
    Test CBEFF conversion from a base64 encoded file
    
    Args:
        cbeff_file_path: Path to file containing base64 encoded CBEFF
        output_path: Path to save the output image
    """
    print(f"Testing CBEFF conversion...")
    print(f"  Input: {cbeff_file_path}")
    print(f"  Output: {output_path}")
    print()
    
    # Initialize client
    client = BioUtilsClient(base_url="http://localhost:8080")
    
    # Check service health
    print("Checking service health...")
    health = client.health_check()
    print(f"  Status: {health.get('status')}")
    
    if health.get("status") != "healthy":
        print("  ⚠️  Warning: Service may not be available")
        print(f"  Error: {health.get('error', 'Unknown error')}")
        return False
    
    print("  ✓ Service is healthy")
    print()
    
    # Convert CBEFF
    try:
        print("Converting CBEFF to image...")
        image_bytes = client.convert_cbeff_from_file(
            cbeff_file_path=cbeff_file_path,
            output_path=output_path,
            compression_ratio=95
        )
        
        print(f"  ✓ Conversion successful!")
        print(f"  Image size: {len(image_bytes)} bytes")
        print(f"  Image saved to: {output_path}")
        return True
        
    except FileNotFoundError:
        print(f"  ✗ Error: CBEFF file not found: {cbeff_file_path}")
        return False
    except ValueError as e:
        print(f"  ✗ Error: {e}")
        print()
        print("  Note: Make sure the CBEFF file contains valid base64 encoded CBEFF data.")
        print("  If modality cannot be auto-detected, you can specify it:")
        print("    client.convert_cbeff_from_file(..., modality='FINGER')")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_cbeff.py <cbeff_file> [output_image]")
        print()
        print("Example:")
        print("  python test_cbeff.py cbeff.txt fingerprint.jpg")
        sys.exit(1)
    
    cbeff_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "output.jpg"
    
    success = test_cbeff_conversion(cbeff_file, output_file)
    sys.exit(0 if success else 1)

