package com.masrvi.core.dto;

import java.time.LocalDateTime;
import java.util.List;

public record ChatMessageDTO(Long id, String role, String content, LocalDateTime timestamp, List<SourceDTO> sources) {}