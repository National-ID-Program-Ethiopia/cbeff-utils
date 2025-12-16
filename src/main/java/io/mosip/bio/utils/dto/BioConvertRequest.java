package io.mosip.bio.utils.dto;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.Min;
import javax.validation.constraints.Max;

/**
 * Request DTO for ISO to image conversion
 */
public class BioConvertRequest {

    @NotBlank(message = "Modality is required (FINGER, IRIS, or FACE)")
    private String modality;

    @NotBlank(message = "ISO version is required (e.g., ISO19794_4_2011, ISO19794_6_2011)")
    private String isoVersion;

    @NotBlank(message = "ISO Base64 encoded bytes are required")
    private String isoBase64;

    @Min(value = 1, message = "Compression ratio must be between 1 and 100")
    @Max(value = 100, message = "Compression ratio must be between 1 and 100")
    private int compressionRatio = 95;

    // Getters and Setters
    public String getModality() {
        return modality;
    }

    public void setModality(String modality) {
        this.modality = modality;
    }

    public String getIsoVersion() {
        return isoVersion;
    }

    public void setIsoVersion(String isoVersion) {
        this.isoVersion = isoVersion;
    }

    public String getIsoBase64() {
        return isoBase64;
    }

    public void setIsoBase64(String isoBase64) {
        this.isoBase64 = isoBase64;
    }

    public int getCompressionRatio() {
        return compressionRatio;
    }

    public void setCompressionRatio(int compressionRatio) {
        this.compressionRatio = compressionRatio;
    }
}

