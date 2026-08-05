package com.masrvi.core.client;

import com.masrvi.core.dto.SourceDTO;
import lombok.Data;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;
import java.util.List;
import java.util.Map;

@Component
public class RagEngineClient {

    @Value("${rag.engine.url}") // on supprimme le :8000 de l'url on le mettra dans application.properties pour
                                // ne pas avoir le serveur sur le meme port que le backend, de même pour le url
                                // http://localhost
    private String ragEngineUrl;

    private final RestTemplate restTemplate = new RestTemplate();

    @Data
    public static class RagResponse {
        private String reponse;
        private List<SourceDTO> sources;
    }

    public RagResponse ask(String question) {
        String url = ragEngineUrl + "/ask";
        Map<String, String> body = Map.of("question", question);
        return restTemplate.postForObject(url, body, RagResponse.class);
    }
}