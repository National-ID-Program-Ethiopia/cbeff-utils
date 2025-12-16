package io.mosip.bio.utils.controller;

import io.mosip.bio.utils.dto.BioConvertRequest;
import io.mosip.bio.utils.dto.ErrorResponse;
import io.mosip.bio.utils.service.BioUtilsService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;

/**
 * REST Controller for MOSIP Bio Utils
 * 
 * Exposes endpoints for converting ISO19794 biometric data to images
 */
@RestController
@RequestMapping("/bio-utils")
@Validated
public class BioUtilsController {

    private static final Logger logger = LoggerFactory.getLogger(BioUtilsController.class);

    @Autowired
    private BioUtilsService bioUtilsService;

    /**
     * Convert ISO19794 biometric data to JPEG/PNG image
     * 
     * @param request BioConvertRequest containing modality, ISO version, and Base64 encoded ISO bytes
     * @return JPEG/PNG image bytes
     */
    @PostMapping(value = "/iso-to-image", produces = MediaType.IMAGE_JPEG_VALUE)
    public ResponseEntity<?> convertIsoToImage(@Valid @RequestBody BioConvertRequest request) {
        try {
            logger.info("Received conversion request for modality: {}", request.getModality());
            
            byte[] imageBytes = bioUtilsService.convertIsoToImage(
                request.getModality(),
                request.getIsoVersion(),
                request.getIsoBase64(),
                request.getCompressionRatio()
            );

            logger.info("Successfully converted ISO to image. Image size: {} bytes", imageBytes.length);

            return ResponseEntity.ok()
                    .header("Content-Type", MediaType.IMAGE_JPEG_VALUE)
                    .body(imageBytes);

        } catch (IllegalArgumentException e) {
            logger.error("Invalid request: {}", e.getMessage());
            ErrorResponse error = new ErrorResponse(
                HttpStatus.BAD_REQUEST.value(),
                "Bad Request",
                e.getMessage(),
                "/bio-utils/iso-to-image"
            );
            return ResponseEntity.badRequest().body(error);

        } catch (Exception e) {
            logger.error("Error converting ISO to image", e);
            ErrorResponse error = new ErrorResponse(
                HttpStatus.INTERNAL_SERVER_ERROR.value(),
                "Internal Server Error",
                "Failed to convert ISO to image: " + e.getMessage(),
                "/bio-utils/iso-to-image"
            );
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }

    /**
     * Health check endpoint
     */
    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("Bio Utils REST Service is running");
    }
}

