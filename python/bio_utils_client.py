#!/usr/bin/env python3
"""
MOSIP Bio Utils Python Client

A Python client for interacting with the MOSIP Bio Utils REST service.
Converts ISO19794 biometric data to JPEG/PNG images.
"""

import requests
import base64
import json
import struct
import re
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any, Tuple
from pathlib import Path


class BioUtilsClient:
    """
    Client for MOSIP Bio Utils REST Service
    
    Example 1: Convert CBEFF (base64 encoded):
        client = BioUtilsClient(base_url="http://localhost:8080")
        
        # Read base64 CBEFF from file
        with open("cbeff.txt", "r") as f:
            cbeff_base64 = f.read().strip()
        
        # Convert to image (modality auto-detected from CBEFF)
        image_bytes = client.convert_cbeff_to_image(
            cbeff_base64=cbeff_base64,
            compression_ratio=95
        )
        
        # Save image
        with open("fingerprint.jpg", "wb") as f:
            f.write(image_bytes)
    
    Example 2: Convert ISO bytes:
        client = BioUtilsClient(base_url="http://localhost:8080")
        
        # Read ISO bytes from file
        with open("fingerprint.iso", "rb") as f:
            iso_bytes = f.read()
        
        # Convert to image
        image_bytes = client.convert_iso_to_image(
            modality="FINGER",
            iso_version="ISO19794_4_2011",
            iso_bytes=iso_bytes,
            compression_ratio=95
        )
        
        # Save image
        with open("fingerprint.jpg", "wb") as f:
            f.write(image_bytes)
    """
    
    def __init__(self, base_url: str = "http://localhost:8080", timeout: int = 30):
        """
        Initialize the Bio Utils client
        
        Args:
            base_url: Base URL of the Bio Utils REST service
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
    
    def parse_cbeff_xml(
        self,
        cbeff_xml: str
    ) -> Tuple[bytes, str, str]:
        """
        Parse CBEFF XML file to extract ISO bytes, modality, and ISO version.
        
        CBEFF XML Structure:
        - <BIR> root element
        - <BIR> contains <BDBInfo> with <Type> (modality) and <BDB> (base64 encoded ISO bytes)
        
        Args:
            cbeff_xml: CBEFF XML content as string
        
        Returns:
            Tuple of (iso_bytes, modality, iso_version)
            - iso_bytes: Extracted ISO19794 bytes (from BDB element)
            - modality: Biometric modality (FINGER, IRIS, or FACE)
            - iso_version: ISO version string
        
        Raises:
            ValueError: If CBEFF XML parsing fails
        """
        try:
            # Parse XML
            root = ET.fromstring(cbeff_xml)
            
            # Extract namespace from root element if present
            namespace = None
            if root.tag.startswith('{'):
                namespace = root.tag[1:root.tag.index('}')]
            
            # Define namespace map for find operations
            ns_map = {}
            if namespace:
                ns_map['ns'] = namespace
            
            # Helper function to find elements with or without namespace
            def find_with_ns(parent, tag, direct_child=False):
                """Find element handling namespace"""
                # Try direct child first if requested, then descendants
                search_paths = []
                if direct_child:
                    # Direct child paths
                    if namespace:
                        search_paths.append(f'{{{namespace}}}{tag}')
                        if ns_map:
                            search_paths.append(f'ns:{tag}')
                    search_paths.append(tag)
                else:
                    # Descendant paths (default)
                    if namespace:
                        search_paths.append(f'.//{{{namespace}}}{tag}')
                        if ns_map:
                            search_paths.append(f'.//ns:{tag}')
                    search_paths.append(f'.//{tag}')
                
                # Try all search paths
                for path in search_paths:
                    if ns_map and 'ns:' in path:
                        result = parent.find(path, ns_map)
                    else:
                        result = parent.find(path)
                    if result is not None:
                        return result
                return None
            
            # Find all BIR elements (nested BIR elements inside root BIR)
            # The root might be BIR, and there might be nested BIR elements
            bir_elements = []
            
            # Try with full namespace URL format (most reliable)
            if namespace:
                bir_elements = root.findall(f'.//{{{namespace}}}BIR')
                if not bir_elements and ns_map:
                    # Try with namespace prefix as fallback
                    bir_elements = root.findall('.//ns:BIR', ns_map)
            
            # Try without namespace
            if not bir_elements:
                bir_elements = root.findall('.//BIR')
            
            # If root itself is BIR, include it
            if root.tag.endswith('BIR') or root.tag == 'BIR':
                if root not in bir_elements:
                    bir_elements.insert(0, root)
            
            if not bir_elements:
                raise ValueError("No BIR elements found in CBEFF XML")
            
            # Use the first BIR element that has BDBInfo and BDB
            # (skip the root BIR if it only contains nested BIRs)
            bir = None
            for bir_candidate in bir_elements:
                bdbinfo_test = find_with_ns(bir_candidate, 'BDBInfo')
                bdb_test = find_with_ns(bir_candidate, 'BDB')
                if bdbinfo_test is not None and bdb_test is not None:
                    bir = bir_candidate
                    break
            
            # If no BIR with both BDBInfo and BDB found, use the first one
            if bir is None:
                bir = bir_elements[0]
            
            # Find BDBInfo to get modality
            bdbinfo = find_with_ns(bir, 'BDBInfo')
            
            modality = None
            if bdbinfo is not None:
                # Find Type element within BDBInfo (try direct child first, then descendant)
                type_elem = find_with_ns(bdbinfo, 'Type', direct_child=True)
                if type_elem is None:
                    type_elem = find_with_ns(bdbinfo, 'Type', direct_child=False)
                
                if type_elem is not None and type_elem.text:
                    type_text = type_elem.text.strip().upper()
                    # Map common type names to modality
                    if 'FINGER' in type_text or 'FMR' in type_text:
                        modality = "FINGER"
                    elif 'IRIS' in type_text or 'IRI' in type_text:
                        modality = "IRIS"
                    elif 'FACE' in type_text or 'FAC' in type_text:
                        modality = "FACE"
            
            # Find BDB element containing base64 encoded ISO bytes
            bdb = find_with_ns(bir, 'BDB')
            
            if bdb is None or not bdb.text:
                raise ValueError("No BDB element found or BDB is empty in CBEFF XML")
            
            # Extract base64 data from BDB
            bdb_base64 = bdb.text.strip()
            
            # Decode base64 to get ISO bytes
            try:
                iso_bytes = base64.b64decode(bdb_base64, validate=True)
            except Exception as e:
                raise ValueError(f"Failed to decode BDB base64 data: {str(e)}")
            
            if len(iso_bytes) == 0:
                raise ValueError("BDB contains no data")
            
            if modality is None:
                raise ValueError(
                    "Could not detect modality from CBEFF XML. "
                    "Please specify modality explicitly or ensure BDBInfo contains Type information."
                )
            
            # Determine ISO version from modality
            iso_version = "ISO19794_4_2011"  # Default
            if modality == "IRIS":
                iso_version = "ISO19794_6_2011"
            elif modality == "FACE":
                iso_version = "ISO19794_5_2011"
            elif modality == "FINGER":
                iso_version = "ISO19794_4_2011"
            
            return iso_bytes, modality.upper(), iso_version
            
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML format: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to parse CBEFF XML: {str(e)}") from e
    
    def parse_cbeff(
        self,
        cbeff_base64: str
    ) -> Tuple[bytes, str, str]:
        """
        Parse CBEFF (Common Biometric Exchange Formats Framework) file
        to extract ISO bytes, modality, and ISO version.
        
        Supports both:
        1. CBEFF XML format - parses XML directly
        2. Base64 encoded binary CBEFF - decodes and extracts ISO bytes
        
        CBEFF Structure:
        - Header (magic number, format identifier)
        - SBH (Standard Biometric Header) - contains modality info
        - BDB (Biometric Data Block) - contains ISO19794 bytes
        
        Args:
            cbeff_base64: Base64 encoded CBEFF file OR CBEFF XML content as string
        
        Returns:
            Tuple of (iso_bytes, modality, iso_version)
            - iso_bytes: Extracted ISO19794 bytes (BDB)
            - modality: Biometric modality (FINGER, IRIS, or FACE)
            - iso_version: ISO version string
        
        Raises:
            ValueError: If CBEFF parsing fails
        """
        # Check if input is XML (starts with <?xml or <BIR)
        cbeff_stripped = cbeff_base64.strip()
        if cbeff_stripped.startswith('<?xml') or cbeff_stripped.startswith('<BIR'):
            # It's XML format, parse directly
            return self.parse_cbeff_xml(cbeff_base64)
        
        # Otherwise, treat as base64 encoded binary CBEFF
        try:
            # Clean and prepare base64 string
            # Base64 characters: A-Z, a-z, 0-9, +, /, = (padding)
            # Remove all whitespace and non-base64 characters
            # Remove all whitespace first
            cbeff_base64_clean = ''.join(cbeff_base64.split())
            # Keep only valid base64 characters (A-Z, a-z, 0-9, +, /, =)
            cbeff_base64_clean = re.sub(r'[^A-Za-z0-9+/=]', '', cbeff_base64_clean)
            
            if not cbeff_base64_clean:
                raise ValueError("CBEFF file appears to be empty or contains no valid base64 characters")
            
            # Remove padding characters temporarily to check length
            # Then add correct padding
            base64_without_padding = cbeff_base64_clean.rstrip('=')
            missing_padding = len(base64_without_padding) % 4
            if missing_padding:
                cbeff_base64_clean = base64_without_padding + '=' * (4 - missing_padding)
            
            # Decode base64 CBEFF
            try:
                cbeff_bytes = base64.b64decode(cbeff_base64_clean, validate=True)
            except Exception as e:
                # base64.b64decode raises binascii.Error for invalid base64
                error_msg = str(e)
                if "base64" in error_msg.lower() or "incorrect padding" in error_msg.lower():
                    raise ValueError(
                        f"Invalid base64 encoding: {error_msg}. "
                        "Make sure the CBEFF file contains valid base64 data. "
                        "The file should contain only base64 characters (A-Z, a-z, 0-9, +, /, =)."
                    )
                else:
                    raise ValueError(f"Failed to decode base64: {error_msg}")
            
            if len(cbeff_bytes) < 8:
                raise ValueError("CBEFF file too short")
            
            # CBEFF typically starts with format identifier
            # Common structure: [Format ID (4 bytes)] [Version] [SBH Length] [SBH] [BDB Length] [BDB]
            
            # Try to find BDB (Biometric Data Block)
            # BDB usually starts after SBH (Standard Biometric Header)
            # SBH contains modality information
            
            # Method 1: Look for ISO19794 magic numbers/patterns
            # ISO19794 formats have specific headers:
            # - Finger: ISO19794-4 format identifier
            # - Iris: ISO19794-6 format identifier  
            # - Face: ISO19794-5 format identifier
            
            # Try parsing as CBEFF with SBH/BDB structure
            # CBEFF format: FormatOwner (2 bytes) + FormatType (2 bytes) + Version (1 byte) + ...
            
            offset = 0
            
            # Read format identifier (first 4 bytes often contain format info)
            if len(cbeff_bytes) < 4:
                raise ValueError("Invalid CBEFF: too short")
            
            # CBEFF structure can vary, but typically:
            # - Format Owner (2 bytes)
            # - Format Type (2 bytes) 
            # - Version (1 byte)
            # - Record Count (1 byte)
            # - SBH Length (4 bytes, big-endian)
            # - SBH data
            # - BDB Length (4 bytes, big-endian)
            # - BDB data (ISO19794 bytes)
            
            # Try to locate BDB by looking for ISO19794 patterns
            # ISO19794 records often start with specific byte patterns
            
            # For MOSIP CBEFF, the structure might be:
            # - Header with format info
            # - SBH with modality (can be XML or binary)
            # - BDB with ISO19794 bytes
            
            # Simple approach: Try to extract BDB by finding ISO19794 signatures
            # or by parsing known CBEFF structure
            
            # Check if this might be a direct ISO file (not CBEFF)
            # ISO19794 files have specific format identifiers
            iso_magic_finger = b'\x46\x4D\x52'  # FMR (Finger Minutia Record)
            iso_magic_iris = b'\x49\x52\x49'    # IRI (Iris Image)
            iso_magic_face = b'\x46\x41\x43'    # FAC (Face Image)
            
            # Try to find ISO19794 data within CBEFF
            # Look for BDB section which contains the ISO bytes
            modality = None
            iso_bytes = None
            
            # Method: Parse CBEFF structure
            # Many CBEFF implementations have:
            # - Fixed header (8-16 bytes)
            # - SBH length (4 bytes)
            # - SBH data
            # - BDB length (4 bytes) 
            # - BDB data
            
            # Try parsing as binary CBEFF
            if len(cbeff_bytes) >= 12:
                # Try to read lengths (often 4-byte big-endian integers)
                # Skip header, try to find length fields
                
                # Look for SBH length (often at offset 8-12)
                try:
                    sbh_length = struct.unpack('>I', cbeff_bytes[8:12])[0]
                    if 0 < sbh_length < len(cbeff_bytes) - 12:
                        sbh_start = 12
                        sbh_end = sbh_start + sbh_length
                        
                        if sbh_end < len(cbeff_bytes):
                            sbh = cbeff_bytes[sbh_start:sbh_end]
                            
                            # Try to extract modality from SBH
                            # SBH might contain XML or binary format info
                            sbh_str = sbh.decode('utf-8', errors='ignore')
                            if 'FINGER' in sbh_str.upper() or 'FMR' in sbh_str.upper():
                                modality = "FINGER"
                            elif 'IRIS' in sbh_str.upper() or 'IRI' in sbh_str.upper():
                                modality = "IRIS"
                            elif 'FACE' in sbh_str.upper() or 'FAC' in sbh_str.upper():
                                modality = "FACE"
                            
                            # Read BDB length
                            bdb_length_start = sbh_end
                            if bdb_length_start + 4 <= len(cbeff_bytes):
                                bdb_length = struct.unpack('>I', cbeff_bytes[bdb_length_start:bdb_length_start+4])[0]
                                bdb_start = bdb_length_start + 4
                                bdb_end = bdb_start + bdb_length
                                
                                if bdb_end <= len(cbeff_bytes):
                                    iso_bytes = cbeff_bytes[bdb_start:bdb_end]
                except:
                    pass
            
            # Fallback: Try to find ISO19794 data by pattern matching
            if iso_bytes is None:
                # Look for ISO19794 format identifiers in the data
                for i in range(len(cbeff_bytes) - 100):
                    chunk = cbeff_bytes[i:i+100]
                    
                    # Check for ISO19794-4 (Finger)
                    if b'ISO19794-4' in chunk or iso_magic_finger in chunk:
                        # Try to extract from this position
                        # ISO19794 records have length fields
                        if i + 4 < len(cbeff_bytes):
                            try:
                                record_length = struct.unpack('>I', cbeff_bytes[i:i+4])[0]
                                if 0 < record_length < len(cbeff_bytes) - i:
                                    iso_bytes = cbeff_bytes[i:i+record_length]
                                    modality = "FINGER"
                                    break
                            except:
                                pass
                    
                    # Check for ISO19794-6 (Iris)
                    elif b'ISO19794-6' in chunk or iso_magic_iris in chunk:
                        if i + 4 < len(cbeff_bytes):
                            try:
                                record_length = struct.unpack('>I', cbeff_bytes[i:i+4])[0]
                                if 0 < record_length < len(cbeff_bytes) - i:
                                    iso_bytes = cbeff_bytes[i:i+record_length]
                                    modality = "IRIS"
                                    break
                            except:
                                pass
                    
                    # Check for ISO19794-5 (Face)
                    elif b'ISO19794-5' in chunk or iso_magic_face in chunk:
                        if i + 4 < len(cbeff_bytes):
                            try:
                                record_length = struct.unpack('>I', cbeff_bytes[i:i+4])[0]
                                if 0 < record_length < len(cbeff_bytes) - i:
                                    iso_bytes = cbeff_bytes[i:i+record_length]
                                    modality = "FACE"
                                    break
                            except:
                                pass
            
            # If still not found, assume the entire file is ISO (might be direct ISO, not CBEFF)
            if iso_bytes is None:
                # Check if it's a direct ISO file
                if iso_magic_finger in cbeff_bytes[:100]:
                    iso_bytes = cbeff_bytes
                    modality = "FINGER"
                elif iso_magic_iris in cbeff_bytes[:100]:
                    iso_bytes = cbeff_bytes
                    modality = "IRIS"
                elif iso_magic_face in cbeff_bytes[:100]:
                    iso_bytes = cbeff_bytes
                    modality = "FACE"
                else:
                    # Last resort: use entire file as ISO, modality must be specified
                    iso_bytes = cbeff_bytes
                    raise ValueError(
                        "Could not automatically detect modality from CBEFF. "
                        "Please specify modality explicitly or ensure CBEFF contains valid SBH."
                    )
            
            if iso_bytes is None or len(iso_bytes) == 0:
                raise ValueError("Could not extract ISO bytes from CBEFF")
            
            if modality is None:
                raise ValueError(
                    "Could not detect modality from CBEFF. "
                    "Please specify modality explicitly."
                )
            
            # Determine ISO version from the ISO bytes
            # ISO19794 versions are typically embedded in the format identifier
            iso_version = "ISO19794_4_2011"  # Default
            if modality == "IRIS":
                iso_version = "ISO19794_6_2011"
            elif modality == "FACE":
                iso_version = "ISO19794_5_2011"
            elif modality == "FINGER":
                iso_version = "ISO19794_4_2011"
            
            return iso_bytes, modality.upper(), iso_version
            
        except Exception as e:
            raise ValueError(f"Failed to parse CBEFF: {str(e)}") from e
    
    def convert_iso_to_image(
        self,
        modality: str,
        iso_version: str,
        iso_bytes: bytes,
        compression_ratio: int = 95,
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Convert ISO19794 bytes to JPEG/PNG image
        
        Args:
            modality: Biometric modality (FINGER, IRIS, or FACE)
            iso_version: ISO version (e.g., ISO19794_4_2011, ISO19794_6_2011)
            iso_bytes: ISO19794 binary data
            compression_ratio: Compression ratio (1-100, default 95)
            output_path: Optional path to save the image file
        
        Returns:
            Image bytes (JPEG/PNG)
        
        Raises:
            requests.RequestException: If the request fails
            ValueError: If the response is invalid
        """
        # Validate inputs
        modality_upper = modality.upper()
        if modality_upper not in ["FINGER", "IRIS", "FACE"]:
            raise ValueError(f"Unsupported modality: {modality}. Must be FINGER, IRIS, or FACE")
        
        if not (1 <= compression_ratio <= 100):
            raise ValueError(f"Compression ratio must be between 1 and 100, got {compression_ratio}")
        
        # Encode ISO bytes to Base64
        iso_base64 = base64.b64encode(iso_bytes).decode('utf-8')
        
        # Prepare request payload
        payload = {
            "modality": modality_upper,
            "isoVersion": iso_version,
            "isoBase64": iso_base64,
            "compressionRatio": compression_ratio
        }
        
        # Make request
        url = f"{self.base_url}/bio-utils/iso-to-image"
        
        try:
            response = self.session.post(
                url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            # Check for errors
            response.raise_for_status()
            
            # Get image bytes
            image_bytes = response.content
            
            if not image_bytes:
                raise ValueError("Received empty image response")
            
            # Save to file if output path is provided
            if output_path:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(image_bytes)
                print(f"Image saved to: {output_path}")
            
            return image_bytes
            
        except requests.exceptions.HTTPError as e:
            # Try to parse error response
            try:
                error_data = e.response.json()
                error_msg = error_data.get("message", str(e))
            except:
                error_msg = str(e)
            
            raise requests.RequestException(
                f"HTTP {e.response.status_code}: {error_msg}"
            ) from e
        
        except requests.exceptions.RequestException as e:
            raise requests.RequestException(
                f"Request failed: {str(e)}"
            ) from e
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the Bio Utils service is healthy
        
        Returns:
            Health status dictionary
        """
        url = f"{self.base_url}/bio-utils/health"
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return {
                "status": "healthy",
                "message": response.text,
                "status_code": response.status_code
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def convert_cbeff_xml_all_birs(
        self,
        cbeff_xml: str,
        output_dir: str = ".",
        compression_ratio: int = 95,
        file_extension: str = "jpg"
    ) -> Dict[str, str]:
        """
        Process all BIR elements in CBEFF XML and save each as a separate image file.
        Files are named using the subtype from BDBInfo.
        
        Args:
            cbeff_xml: CBEFF XML content as string
            output_dir: Directory to save output images (default: current directory)
            compression_ratio: Compression ratio (1-100, default 95)
            file_extension: Output file extension (default: "jpg")
        
        Returns:
            Dictionary mapping subtype to output file path
        
        Raises:
            ValueError: If CBEFF XML parsing fails
            requests.RequestException: If the request fails
        """
        import os
        from pathlib import Path
        
        try:
            # Parse XML
            root = ET.fromstring(cbeff_xml)
            
            # Extract namespace from root element if present
            namespace = None
            if root.tag.startswith('{'):
                namespace = root.tag[1:root.tag.index('}')]
            
            # Define namespace map for find operations
            ns_map = {}
            if namespace:
                ns_map['ns'] = namespace
            
            # Helper function to find elements with or without namespace
            def find_with_ns(parent, tag, direct_child=False):
                """Find element handling namespace"""
                search_paths = []
                if direct_child:
                    if namespace:
                        search_paths.append(f'{{{namespace}}}{tag}')
                        if ns_map:
                            search_paths.append(f'ns:{tag}')
                    search_paths.append(tag)
                else:
                    if namespace:
                        search_paths.append(f'.//{{{namespace}}}{tag}')
                        if ns_map:
                            search_paths.append(f'.//ns:{tag}')
                    search_paths.append(f'.//{tag}')
                
                for path in search_paths:
                    if ns_map and 'ns:' in path:
                        result = parent.find(path, ns_map)
                    else:
                        result = parent.find(path)
                    if result is not None:
                        return result
                return None
            
            # Find all BIR elements
            bir_elements = []
            if namespace:
                bir_elements = root.findall(f'.//{{{namespace}}}BIR')
                if not bir_elements and ns_map:
                    bir_elements = root.findall('.//ns:BIR', ns_map)
            if not bir_elements:
                bir_elements = root.findall('.//BIR')
            
            if not bir_elements:
                raise ValueError("No BIR elements found in CBEFF XML")
            
            # Create output directory if it doesn't exist
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            results = {}
            processed_count = 0
            
            # Process each BIR element
            for bir_idx, bir in enumerate(bir_elements):
                try:
                    # Find BDBInfo
                    bdbinfo = find_with_ns(bir, 'BDBInfo')
                    if bdbinfo is None:
                        continue
                    
                    # Extract Type (modality)
                    type_elem = find_with_ns(bdbinfo, 'Type', direct_child=True)
                    if type_elem is None:
                        type_elem = find_with_ns(bdbinfo, 'Type', direct_child=False)
                    
                    if type_elem is None or not type_elem.text:
                        continue
                    
                    type_text = type_elem.text.strip().upper()
                    if 'FINGER' in type_text or 'FMR' in type_text:
                        modality = "FINGER"
                    elif 'IRIS' in type_text or 'IRI' in type_text:
                        modality = "IRIS"
                    elif 'FACE' in type_text or 'FAC' in type_text:
                        modality = "FACE"
                    else:
                        continue
                    
                    # Extract Subtype
                    subtype_elem = find_with_ns(bdbinfo, 'Subtype', direct_child=True)
                    if subtype_elem is None:
                        subtype_elem = find_with_ns(bdbinfo, 'Subtype', direct_child=False)
                    
                    if subtype_elem is not None and subtype_elem.text:
                        subtype = subtype_elem.text.strip()
                        # Handle "None" as empty
                        if subtype.upper() == "NONE" or not subtype:
                            subtype = None
                    else:
                        subtype = None
                    
                    # Create filename from subtype or use modality + index
                    if subtype:
                        safe_subtype = re.sub(r'[^\w\s-]', '', subtype)
                        safe_subtype = re.sub(r'[-\s]+', '_', safe_subtype)
                        safe_subtype = safe_subtype.strip('_')
                    else:
                        safe_subtype = f"{modality}_{bir_idx + 1}"
                    
                    if not safe_subtype:
                        safe_subtype = f"{modality}_{bir_idx + 1}"
                    
                    # Find BDB element
                    bdb = find_with_ns(bir, 'BDB')
                    if bdb is None or not bdb.text:
                        continue
                    
                    # Extract and decode ISO bytes
                    bdb_base64 = bdb.text.strip()
                    try:
                        iso_bytes = base64.b64decode(bdb_base64, validate=True)
                    except Exception as e:
                        continue
                    
                    if len(iso_bytes) == 0:
                        continue
                    
                    # Determine ISO version
                    iso_version = "ISO19794_4_2011"
                    if modality == "IRIS":
                        iso_version = "ISO19794_6_2011"
                    elif modality == "FACE":
                        iso_version = "ISO19794_5_2011"
                    
                    # Convert to image
                    image_bytes = self.convert_iso_to_image(
                        modality=modality,
                        iso_version=iso_version,
                        iso_bytes=iso_bytes,
                        compression_ratio=compression_ratio
                    )
                    
                    # Save with subtype as filename
                    output_file = output_path / f"{safe_subtype}.{file_extension}"
                    with open(output_file, "wb") as f:
                        f.write(image_bytes)
                    
                    results[subtype] = str(output_file)
                    processed_count += 1
                    
                except Exception as e:
                    # Log error but continue with next BIR
                    continue
            
            if processed_count == 0:
                raise ValueError("No valid BIR elements with BDB data found in CBEFF XML")
            
            return results
            
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML format: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to process CBEFF XML: {str(e)}") from e
    
    def convert_cbeff_to_image(
        self,
        cbeff_base64: str,
        modality: Optional[str] = None,
        iso_version: Optional[str] = None,
        compression_ratio: int = 95,
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Convert CBEFF to JPEG/PNG image.
        Automatically extracts ISO bytes and modality from CBEFF.
        
        Supports both:
        1. CBEFF XML format - parses XML directly
        2. Base64 encoded binary CBEFF - decodes and extracts ISO bytes
        
        Args:
            cbeff_base64: CBEFF XML content or base64 encoded CBEFF file
            modality: Optional modality override (FINGER, IRIS, or FACE).
                     If not provided, will be extracted from CBEFF.
            iso_version: Optional ISO version override.
                        If not provided, will be inferred from modality.
            compression_ratio: Compression ratio (1-100, default 95)
            output_path: Optional path to save the image file
        
        Returns:
            Image bytes (JPEG/PNG)
        
        Raises:
            ValueError: If CBEFF parsing fails or modality cannot be determined
            requests.RequestException: If the request fails
        """
        # Parse CBEFF to extract ISO bytes and modality
        iso_bytes, detected_modality, detected_version = self.parse_cbeff(cbeff_base64)
        
        # Use provided values or fall back to detected values
        final_modality = modality.upper() if modality else detected_modality
        final_version = iso_version if iso_version else detected_version
        
        # Convert using extracted ISO bytes
        return self.convert_iso_to_image(
            modality=final_modality,
            iso_version=final_version,
            iso_bytes=iso_bytes,
            compression_ratio=compression_ratio,
            output_path=output_path
        )
    
    def convert_cbeff_from_file(
        self,
        cbeff_file_path: str,
        modality: Optional[str] = None,
        iso_version: Optional[str] = None,
        output_path: Optional[str] = None,
        compression_ratio: int = 95
    ) -> bytes:
        """
        Convert CBEFF file to image.
        Supports both XML format and base64 encoded binary CBEFF files.
        
        Args:
            cbeff_file_path: Path to CBEFF file (XML format or base64 encoded text file)
            modality: Optional modality override
            iso_version: Optional ISO version override
            output_path: Path to save output image
            compression_ratio: Compression ratio (1-100)
        
        Returns:
            Image bytes
        """
        # Read CBEFF file
        try:
            with open(cbeff_file_path, "r", encoding='utf-8') as f:
                cbeff_content = f.read().strip()
            
            if not cbeff_content:
                raise ValueError(f"CBEFF file is empty: {cbeff_file_path}")
            
        except FileNotFoundError:
            raise FileNotFoundError(f"CBEFF file not found: {cbeff_file_path}")
        except Exception as e:
            raise ValueError(f"Error reading CBEFF file: {str(e)}")
        
        return self.convert_cbeff_to_image(
            cbeff_base64=cbeff_content,  # Can be XML or base64
            modality=modality,
            iso_version=iso_version,
            compression_ratio=compression_ratio,
            output_path=output_path
        )
    
    def convert_cbeff_xml_all_birs_from_file(
        self,
        cbeff_file_path: str,
        output_dir: str = ".",
        compression_ratio: int = 95,
        file_extension: str = "jpg"
    ) -> Dict[str, str]:
        """
        Process all BIR elements in CBEFF XML file and save each as a separate image file.
        Files are named using the subtype from BDBInfo.
        
        Args:
            cbeff_file_path: Path to CBEFF XML file
            output_dir: Directory to save output images (default: current directory)
            compression_ratio: Compression ratio (1-100, default 95)
            file_extension: Output file extension (default: "jpg")
        
        Returns:
            Dictionary mapping subtype to output file path
        
        Raises:
            ValueError: If CBEFF XML parsing fails
            requests.RequestException: If the request fails
        """
        # Read CBEFF XML file
        try:
            with open(cbeff_file_path, "r", encoding='utf-8') as f:
                cbeff_xml = f.read().strip()
            
            if not cbeff_xml:
                raise ValueError(f"CBEFF file is empty: {cbeff_file_path}")
            
        except FileNotFoundError:
            raise FileNotFoundError(f"CBEFF file not found: {cbeff_file_path}")
        except Exception as e:
            raise ValueError(f"Error reading CBEFF file: {str(e)}")
        
        return self.convert_cbeff_xml_all_birs(
            cbeff_xml=cbeff_xml,
            output_dir=output_dir,
            compression_ratio=compression_ratio,
            file_extension=file_extension
        )
    
    def convert_from_file(
        self,
        iso_file_path: str,
        modality: str,
        iso_version: str,
        output_path: str,
        compression_ratio: int = 95
    ) -> bytes:
        """
        Convert ISO file to image file
        
        Args:
            iso_file_path: Path to input ISO file
            modality: Biometric modality (FINGER, IRIS, or FACE)
            iso_version: ISO version
            output_path: Path to save output image
            compression_ratio: Compression ratio (1-100)
        
        Returns:
            Image bytes
        """
        # Read ISO file
        with open(iso_file_path, "rb") as f:
            iso_bytes = f.read()
        
        # Convert and save
        return self.convert_iso_to_image(
            modality=modality,
            iso_version=iso_version,
            iso_bytes=iso_bytes,
            compression_ratio=compression_ratio,
            output_path=output_path
        )


def main():
    """
    Example usage of BioUtilsClient
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="MOSIP Bio Utils Python Client - Convert ISO19794 or CBEFF to images"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8080",
        help="Bio Utils REST service URL"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input file path (ISO file or base64 CBEFF text file)"
    )
    parser.add_argument(
        "--output",
        help="Output image file path (required if --all-birs not set)"
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Output directory for --all-birs mode (default: current directory)"
    )
    parser.add_argument(
        "--format",
        choices=["iso", "cbeff"],
        default="cbeff",
        help="Input format: 'iso' for ISO19794 binary file, 'cbeff' for base64 CBEFF file (default: cbeff)"
    )
    parser.add_argument(
        "--all-birs",
        action="store_true",
        help="Process all BIR elements in CBEFF XML and save each with subtype as filename (XML format only)"
    )
    parser.add_argument(
        "--modality",
        choices=["FINGER", "IRIS", "FACE"],
        help="Biometric modality (optional for CBEFF, will be auto-detected)"
    )
    parser.add_argument(
        "--iso-version",
        help="ISO version (e.g., ISO19794_4_2011). Optional for CBEFF, will be auto-detected"
    )
    parser.add_argument(
        "--compression",
        type=int,
        default=95,
        help="Compression ratio (1-100, default: 95)"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.all_birs and not args.output:
        parser.error("--output is required unless --all-birs is specified")
    
    # Create client
    client = BioUtilsClient(base_url=args.url)
    
    # Check health
    health = client.health_check()
    print(f"Service health: {health}")
    
    if health.get("status") != "healthy":
        print("Warning: Service may not be available")
    
    # Convert based on format
    try:
        if args.all_birs:
            # Process all BIRs in CBEFF XML
            if args.format != "cbeff":
                print("Error: --all-birs only works with CBEFF XML format")
                return 1
            
            print(f"Processing all BIRs from {args.input}...")
            results = client.convert_cbeff_xml_all_birs_from_file(
                cbeff_file_path=args.input,
                output_dir=args.output_dir,
                compression_ratio=args.compression
            )
            
            print(f"\nSuccessfully processed {len(results)} BIR elements:")
            for subtype, file_path in results.items():
                print(f"  - {subtype}: {file_path}")
        
        else:
            # Single file conversion
            print(f"Converting {args.input} ({args.format}) to {args.output}...")
            
            if args.format == "cbeff":
                # CBEFF format (base64 encoded or XML)
                image_bytes = client.convert_cbeff_from_file(
                    cbeff_file_path=args.input,
                    modality=args.modality,
                    iso_version=args.iso_version,
                    output_path=args.output,
                    compression_ratio=args.compression
                )
            else:
                # ISO format (binary)
                if not args.modality:
                    print("Error: --modality is required for ISO format")
                    return 1
                if not args.iso_version:
                    print("Error: --iso-version is required for ISO format")
                    return 1
                
                image_bytes = client.convert_from_file(
                    iso_file_path=args.input,
                    modality=args.modality,
                    iso_version=args.iso_version,
                    output_path=args.output,
                    compression_ratio=args.compression
                )
            
            print(f"Success! Image size: {len(image_bytes)} bytes")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

