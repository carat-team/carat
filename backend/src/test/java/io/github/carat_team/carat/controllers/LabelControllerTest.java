package io.github.carat_team.carat.controllers;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.BDDMockito.given;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.List;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.http.HttpStatus;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.web.server.ResponseStatusException;

import io.github.carat_team.carat.dto.BarcodeResponse;
import io.github.carat_team.carat.dto.LabelScanResponse;
import io.github.carat_team.carat.dto.TextBlockResponse;
import io.github.carat_team.carat.services.LabelScanService;

@ExtendWith(SpringExtension.class)
@WebMvcTest(LabelController.class)
@ActiveProfiles("test")
public class LabelControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private LabelScanService service;

    private final MockMultipartFile photo =
        new MockMultipartFile("file", "label.jpg", "image/jpeg", new byte[] {1, 2, 3});

    @Test
    @WithMockUser(username = "user")
    public void checkScanLabelIsOk() throws Exception {
        given(service.scan(any())).willReturn(new LabelScanResponse(
            List.of(new BarcodeResponse("3614272049520", "EAN_13", false, "Wrong check digit")),
            List.of(new TextBlockResponse("MADE IN FRANCE", 0.97))
        ));

        mockMvc.perform(MockMvcRequestBuilders.multipart("/api/analyze/label").file(photo).with(csrf()))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.barcodes[0].text").value("3614272049520"))
            .andExpect(jsonPath("$.barcodes[0].format").value("EAN_13"))
            .andExpect(jsonPath("$.barcodes[0].valid").value(false))
            .andExpect(jsonPath("$.barcodes[0].validationError").value("Wrong check digit"))
            .andExpect(jsonPath("$.texts[0].text").value("MADE IN FRANCE"))
            .andExpect(jsonPath("$.texts[0].confidence").value(0.97));
    }

    @Test
    @WithMockUser(username = "user")
    public void checkScanLabelRejectsNonImage() throws Exception {
        given(service.scan(any()))
            .willThrow(new ResponseStatusException(HttpStatus.BAD_REQUEST, "File is not a supported image"));

        mockMvc.perform(MockMvcRequestBuilders.multipart("/api/analyze/label").file(photo).with(csrf()))
            .andExpect(status().isBadRequest());
    }
}
