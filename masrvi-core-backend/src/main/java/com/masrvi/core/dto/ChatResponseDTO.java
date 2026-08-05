package com.masrvi.core.dto;

public record ChatResponseDTO(Long sessionId, ChatMessageDTO userMessage, ChatMessageDTO aiMessage) {}