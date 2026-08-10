package com.masrvi.core.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Réponse typée du endpoint /ingest du moteur RAG.
 * Les @JsonProperty conservent le format snake_case du moteur Python (contrat API inchangé).
 */
public record IngestResponseDTO(
        @JsonProperty("file_name") String fileName,
        @JsonProperty("nb_passages") Integer nbPassages,
        @JsonProperty("messages") String messages) {
}
