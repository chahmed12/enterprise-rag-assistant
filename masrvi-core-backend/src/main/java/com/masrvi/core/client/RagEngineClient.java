package com.masrvi.core.client;

import com.masrvi.core.dto.IngestResponseDTO;
import com.masrvi.core.dto.ReloadResponseDTO;
import com.masrvi.core.dto.SourceDTO;
import com.masrvi.core.exception.RagEngineException;
import lombok.Data;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpRequest;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.MediaType;
import org.springframework.http.client.ClientHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Proxy HTTP vers le moteur RAG (FastAPI) via RestClient.
 * Timeouts (5 s connexion / 60 s réponse) et gestion d'erreurs centralisée :
 * toute erreur (réseau ou HTTP 4xx/5xx) est levée en RagEngineException → HTTP 503.
 */
@Component
public class RagEngineClient {

    private final RestClient ragRestClient;

    public RagEngineClient(RestClient ragRestClient) {
        this.ragRestClient = ragRestClient;
    }

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
        Map<String, String> body = new HashMap<>();
        body.put("question", question);
        if (sourceFilter != null && !sourceFilter.isBlank()) {
            body.put("source_filter", sourceFilter);
        }
        if (typeFilter != null && !typeFilter.isBlank()) {
            body.put("type_filter", typeFilter);
        }
        return execute(ragRestClient.post()
                .uri("/ask")
                .contentType(MediaType.APPLICATION_JSON)
                .body(body), RagResponse.class);
    }

    /**
     * Demande au moteur RAG de recharger son index depuis le disque.
     */
    public ReloadResponseDTO reload() {
        return execute(ragRestClient.post().uri("/reload"), ReloadResponseDTO.class);
    }

    /**
     * Transfère un fichier vers le moteur RAG pour l'ingestion dans la base vectorielle.
     *
     * @param file Le fichier à ingérer (MultipartFile Spring).
     */
    public IngestResponseDTO ingest(MultipartFile file) throws IOException {
        // Construction du corps multipart : une clé → liste de valeurs
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        // ByteArrayResource : octets du fichier embarqués en mémoire ; getFilename()
        // préserve le nom original, indispensable côté Python (basename du document)
        ByteArrayResource fileResource = new ByteArrayResource(file.getBytes()) {
            @Override
            public String getFilename() {
                return file.getOriginalFilename();
            }
        };
        body.add("file", fileResource);

        return execute(ragRestClient.post()
                .uri("/ingest")
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .body(body), IngestResponseDTO.class);
    }

    /**
     * Exécute la requête : les erreurs HTTP (4xx/5xx) sont levées par onStatus,
     * les erreurs réseau/techniques sont enveloppées ici, toutes en RagEngineException.
     */
    private <T> T execute(RestClient.RequestHeadersSpec<?> request, Class<T> responseType) {
        try {
            return request.retrieve()
                    .onStatus(this::isError, this::handleError)
                    .body(responseType);
        } catch (RestClientException e) {
            throw new RagEngineException("Erreur de communication avec le moteur RAG (IA indisponible).", e);
        }
    }

    private boolean isError(HttpStatusCode status) {
        return status.isError();
    }

    private void handleError(HttpRequest request, ClientHttpResponse response) throws IOException {
        HttpStatusCode status = response.getStatusCode();
        String detail = "";
        try (InputStream body = response.getBody()) {
            if (body != null) {
                detail = new String(body.readAllBytes(), StandardCharsets.UTF_8).trim();
            }
        }
        throw new RagEngineException("Erreur HTTP " + status.value() + " du moteur RAG. " + detail);
    }
}
