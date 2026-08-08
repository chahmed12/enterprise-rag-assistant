package com.masrvi.core.dto;

import com.fasterxml.jackson.annotation.JsonAlias;

public record SourceDTO(
        @JsonAlias("document_name") String documentName,
        Integer page,
        Double score,
        String section) {
}