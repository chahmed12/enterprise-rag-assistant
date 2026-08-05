package com.masrvi.core.dto;

import java.util.List;

public record ChatMessageDTO(Long id, String role, String content, List<SourceDTO> sources) {}