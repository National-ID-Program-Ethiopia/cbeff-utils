package io.mosip.bio.utils.service;

import io.mosip.biometrics.util.ConvertRequestDto;
import io.mosip.biometrics.util.finger.FingerDecoder;
import io.mosip.biometrics.util.iris.IrisDecoder;
import io.mosip.biometrics.util.face.FaceDecoder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.Base64;

/**
 * Service layer for Bio Utils operations
 * 
 * Converts ISO19794 biometric data to JPEG/PNG images using MOSIP Bio Utils
 */
@Service
public class BioUtilsService {

    private static final Logger logger = LoggerFactory.getLogger(BioUtilsService.class);

    /**
     * Convert ISO19794 bytes to image
     * 
     * @param modality FINGER, IRIS, or FACE
     * @param isoVersion ISO version (e.g., ISO19794_4_2011, ISO19794_6_2011)
     * @param isoBase64 Base64 encoded ISO bytes
     * @param compressionRatio Compression ratio (1-100, default 95)
     * @return Image bytes (JPEG/PNG)
     */
    public byte[] convertIsoToImage(String modality, String isoVersion, String isoBase64, int compressionRatio) {
        try {
            // Decode Base64
            byte[] isoBytes = Base64.getDecoder().decode(isoBase64);
            
            if (isoBytes == null || isoBytes.length == 0) {
                throw new IllegalArgumentException("ISO bytes are empty");
            }

            // Create ConvertRequestDto
            ConvertRequestDto dto = new ConvertRequestDto();
            dto.setVersion(isoVersion);
            dto.setInputBytes(isoBytes);
            dto.setModality(modality.toUpperCase());
            
            // Note: compressionRatio parameter is accepted for API compatibility
            // but ConvertRequestDto doesn't expose compression settings.
            // The decoder will use its default compression settings.

            byte[] imageBytes;

            switch (modality.toUpperCase()) {
                case "FINGER":
                    imageBytes = FingerDecoder.convertFingerISOToImageBytes(dto);
                    break;

                case "IRIS":
                    imageBytes = IrisDecoder.convertIrisISOToImageBytes(dto);
                    break;

                case "FACE":
                    imageBytes = FaceDecoder.convertFaceISOToImageBytes(dto);
                    break;

                default:
                    throw new IllegalArgumentException("Unsupported modality: " + modality + 
                        ". Supported modalities: FINGER, IRIS, FACE");
            }

            if (imageBytes == null || imageBytes.length == 0) {
                throw new IllegalArgumentException("Failed to convert ISO to image. Result is empty.");
            }

            logger.info("Successfully converted {} ISO bytes to {} image bytes", 
                isoBytes.length, imageBytes.length);

            return imageBytes;

        } catch (IllegalArgumentException e) {
            logger.error("Invalid request: {}", e.getMessage());
            throw e;
        } catch (Exception e) {
            logger.error("Error converting ISO to image", e);
            throw new RuntimeException("Failed to convert ISO to image: " + e.getMessage(), e);
        }
    }
}

