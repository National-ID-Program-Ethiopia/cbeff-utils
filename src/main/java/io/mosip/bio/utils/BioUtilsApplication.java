package io.mosip.bio.utils;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * MOSIP Bio Utils REST Service
 * 
 * Exposes MOSIP Bio Utils as a stateless REST service for converting
 * ISO19794 biometric data to JPEG/PNG images.
 */
@SpringBootApplication
public class BioUtilsApplication {

    public static void main(String[] args) {
        SpringApplication.run(BioUtilsApplication.class, args);
    }
}

