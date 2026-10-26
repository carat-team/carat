package io.github.carat_team.carat.controllers;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.BDDMockito.given;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.List;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.web.server.ResponseStatusException;

import io.github.carat_team.carat.dto.BackgroundCheckResponse;
import io.github.carat_team.carat.dto.BackgroundCheckResponse.BackgroundStatsResponse;
import io.github.carat_team.carat.dto.BackgroundCheckResponse.BackgroundVerdict;
import io.github.carat_team.carat.dto.BackgroundCheckResponse.ForeignObjectResponse;
import io.github.carat_team.carat.dto.BackgroundCheckResponse.ForeignObjectSource;
import io.github.carat_team.carat.dto.BackgroundCheckResponse.ObjectBoxResponse;
import io.github.carat_team.carat.services.background.BackgroundCheckService;

@ExtendWith(SpringExtension.class)
@WebMvcTest(BackgroundController.class)
@ActiveProfiles("test")
public class BackgroundControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private BackgroundCheckService service;

    private final MockMultipartFile photo =
        new MockMultipartFile("file", "perfume.jpg", "image/jpeg", new byte[] {1, 2, 3});

    @Test
    @WithMockUser(username = "user")
    public void checkBackgroundIsOk() throws Exception {
        given(service.check(any())).willReturn(new BackgroundCheckResponse(
            BackgroundVerdict.OBJECTS,
            false,
            1200,
            1200,
            new ObjectBoxResponse(400, 150, 400, 900, 0.2),
            new BackgroundStatsResponse("#f4f2ef", 0.93, 0.015),
            List.of(new ForeignObjectResponse(new ObjectBoxResponse(820, 640, 260, 300, 0.04), ForeignObjectSource.MASK))
        ));

        mockMvc.perform(MockMvcRequestBuilders.multipart("/api/analyze/background").file(photo).with(csrf()))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.verdict").value("OBJECTS"))
            .andExpect(jsonPath("$.ok").value(false))
            .andExpect(jsonPath("$.mainObject.width").value(400))
            .andExpect(jsonPath("$.background.color").value("#f4f2ef"))
            .andExpect(jsonPath("$.foreignObjects[0].source").value("MASK"))
            .andExpect(jsonPath("$.foreignObjects[0].box.x").value(820));
    }

    @Test
    @WithMockUser(username = "user")
    public void checkBackgroundRejectsNonImage() throws Exception {
        given(service.check(any()))
            .willThrow(new ResponseStatusException(HttpStatus.UNSUPPORTED_MEDIA_TYPE, "File is not a supported image"));

        mockMvc.perform(MockMvcRequestBuilders.multipart("/api/analyze/background").file(photo).with(csrf()))
            .andExpect(status().isUnsupportedMediaType());
    }

    @Test
    @WithMockUser(username = "user")
    public void cutOutReturnsPng() throws Exception {
        byte[] png = {(byte) 0x89, 'P', 'N', 'G'};
        given(service.cutOut(any())).willReturn(png);

        mockMvc.perform(MockMvcRequestBuilders.multipart("/api/analyze/background/cutout").file(photo).with(csrf()))
            .andExpect(status().isOk())
            .andExpect(content().contentType(MediaType.IMAGE_PNG))
            .andExpect(content().bytes(png));
    }
}
