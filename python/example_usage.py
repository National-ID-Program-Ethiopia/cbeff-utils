#!/usr/bin/env python3
"""
Example usage of MOSIP Bio Utils Python Client

This script demonstrates how to use the BioUtilsClient to convert
ISO19794 biometric data to images.
"""

from bio_utils_client import BioUtilsClient


def example_cbeff_usage():
    """Example: Convert CBEFF (XML or base64 encoded) to image"""
    
    # Initialize client
    client = BioUtilsClient(base_url="http://localhost:8080")
    
    # Check service health
    health = client.health_check()
    print(f"Service Status: {health}")
    
    # Example 1: Read CBEFF XML from file
    try:
        with open("cbeff.xml", "r") as f:
            cbeff_xml = f.read()
        
        # Convert to image (modality and ISO version auto-detected from CBEFF XML)
        image_bytes = client.convert_cbeff_to_image(
            cbeff_base64=cbeff_xml,  # Can be XML content
            compression_ratio=95
        )
        
        # Save image
        with open("output.jpg", "wb") as f:
            f.write(image_bytes)
        
        print(f"Successfully converted CBEFF XML to image. Size: {len(image_bytes)} bytes")
        return
        
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Error with XML: {e}")
    
    # Example 2: Read base64 CBEFF from file
    try:
        with open("cbeff.txt", "r") as f:
            cbeff_base64 = f.read().strip()
        
        # Convert to image (modality and ISO version auto-detected from CBEFF)
        image_bytes = client.convert_cbeff_to_image(
            cbeff_base64=cbeff_base64,
            compression_ratio=95
        )
        
        # Save image
        with open("output.jpg", "wb") as f:
            f.write(image_bytes)
        
        print(f"Successfully converted CBEFF to image. Size: {len(image_bytes)} bytes")
        
    except FileNotFoundError:
        print("Note: Create a 'cbeff.xml' (XML format) or 'cbeff.txt' (base64) file to test")
    except Exception as e:
        print(f"Error: {e}")


def example_basic_usage():
    """Basic example: Convert ISO bytes to image"""
    
    # Initialize client
    client = BioUtilsClient(base_url="http://localhost:8080")
    
    # Check service health
    health = client.health_check()
    print(f"Service Status: {health}")
    
    # Example: Read ISO bytes from file
    # In practice, you would read from your ISO file
    # with open("fingerprint.iso", "rb") as f:
    #     iso_bytes = f.read()
    
    # For demonstration, we'll use empty bytes (replace with actual ISO data)
    iso_bytes = b""  # Replace with actual ISO bytes
    
    if not iso_bytes:
        print("Note: Replace iso_bytes with actual ISO19794 data to test")
        return
    
    # Convert to image
    try:
        image_bytes = client.convert_iso_to_image(
            modality="FINGER",
            iso_version="ISO19794_4_2011",
            iso_bytes=iso_bytes,
            compression_ratio=95
        )
        
        # Save image
        with open("output.jpg", "wb") as f:
            f.write(image_bytes)
        
        print(f"Successfully converted ISO to image. Size: {len(image_bytes)} bytes")
        
    except Exception as e:
        print(f"Error: {e}")


def example_file_conversion():
    """Example: Convert ISO file to image file"""
    
    client = BioUtilsClient(base_url="http://localhost:8080")
    
    try:
        # Convert directly from file to file
        image_bytes = client.convert_from_file(
            iso_file_path="input.iso",
            modality="IRIS",
            iso_version="ISO19794_6_2011",
            output_path="output.jpg",
            compression_ratio=95
        )
        
        print(f"Conversion successful! Image size: {len(image_bytes)} bytes")
        
    except FileNotFoundError:
        print("Error: Input file not found")
    except Exception as e:
        print(f"Error: {e}")


def example_different_modalities():
    """Example: Convert different biometric modalities"""
    
    client = BioUtilsClient(base_url="http://localhost:8080")
    
    modalities = [
        ("FINGER", "ISO19794_4_2011", "fingerprint.iso", "fingerprint.jpg"),
        ("IRIS", "ISO19794_6_2011", "iris.iso", "iris.jpg"),
        ("FACE", "ISO19794_5_2011", "face.iso", "face.jpg"),
    ]
    
    for modality, iso_version, input_file, output_file in modalities:
        try:
            print(f"Converting {modality}...")
            image_bytes = client.convert_from_file(
                iso_file_path=input_file,
                modality=modality,
                iso_version=iso_version,
                output_path=output_file,
                compression_ratio=95
            )
            print(f"  ✓ {modality} converted successfully ({len(image_bytes)} bytes)")
            
        except FileNotFoundError:
            print(f"  ✗ {modality}: Input file not found")
        except Exception as e:
            print(f"  ✗ {modality}: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("MOSIP Bio Utils Python Client - Example Usage")
    print("=" * 60)
    print()
    
    print("Example 1: CBEFF Conversion (Recommended)")
    print("-" * 60)
    example_cbeff_usage()
    print()
    
    print("Example 2: Basic ISO Usage")
    print("-" * 60)
    example_basic_usage()
    print()
    
    print("Example 3: File Conversion")
    print("-" * 60)
    example_file_conversion()
    print()
    
    print("Example 4: Different Modalities")
    print("-" * 60)
    example_different_modalities()

