package io.github.carat_team.carat;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication(scanBasePackages = {
        "io.github.carat_team.carat",
        // Cogniflex-derived core: analysis pipeline and input processing
        "io.github.duckysmacky.cogniflex"
})
public class CaratApplication {

    public static void main(String[] args) {
        SpringApplication.run(CaratApplication.class, args);
    }

}
