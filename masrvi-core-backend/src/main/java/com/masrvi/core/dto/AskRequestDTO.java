package com.masrvi.core.dto;

public record AskRequestDTO(Long sessionId, String question, String sourceFilter, String typeFilter) {}
