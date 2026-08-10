package com.masrvi.core.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Réponse typée du endpoint /reload du moteur RAG.
 * Le @JsonProperty conserve le format snake_case du moteur Python (contrat API inchangé).
 */
public record ReloadResponseDTO(
        @JsonProperty("messages") String messages) {
}
