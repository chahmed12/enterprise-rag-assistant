package com.masrvi.core.client;

import com.masrvi.core.dto.SourceDTO;
import lombok.Data;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.*;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Component
public class RagEngineClient {

    @Value("${rag.engine.url}") // on supprime le :8000 de l'url, on le mettra dans application.properties pour
                                // ne pas avoir le serveur sur le même port que le backend
    private String ragEngineUrl;

    private final RestTemplate restTemplate = new RestTemplate();

    @Data
    public static class RagResponse {
        private String reponse;
        private List<SourceDTO> sources;
    }

    /**
     * Envoie la question au moteur RAG avec des filtres optionnels.
     *
     * @param question     La question posée par l'utilisateur.
     * @param sourceFilter Filtre sur le nom du document source (peut être null).
     * @param typeFilter   Filtre sur le type de document (peut être null).
     */
    public RagResponse ask(String question, String sourceFilter, String typeFilter) {
        String url = ragEngineUrl + "/ask";
        Map<String, String> body = new HashMap<>();
        body.put("question", question);
        if (sourceFilter != null && !sourceFilter.isBlank()) {
            body.put("source_filter", sourceFilter);
        }
        if (typeFilter != null && !typeFilter.isBlank()) {
            body.put("type_filter", typeFilter);
        }
        return restTemplate.postForObject(url, body, RagResponse.class);
    }

    /**
     * Demande au moteur RAG de recharger son index depuis le disque.
     * @return La réponse JSON du moteur Python (ex: {"message": "..."}).
     */
    public Map<?, ?> reload() {
        String url = ragEngineUrl + "/reload";
        return restTemplate.postForObject(url, null, Map.class);
    }

    /**
     * Transfère un fichier vers le moteur RAG pour l'ingestion dans la base vectorielle.
     *
     * @param file Le fichier à ingérer (MultipartFile Spring).
     * @return La réponse brute de l'API Python (Map JSON).
     */
    public Map<?, ?> ingest(MultipartFile file) throws IOException {
        String url = ragEngineUrl + "/ingest";

        // Construction du corps multipart
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        ByteArrayResource fileResource = new ByteArrayResource(file.getBytes()) {
            @Override
            public String getFilename() {
                return file.getOriginalFilename();
            }
        };
        body.add("file", fileResource);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);
        ResponseEntity<Map> response = restTemplate.exchange(url, HttpMethod.POST, requestEntity, Map.class);
        return response.getBody();
    }
}