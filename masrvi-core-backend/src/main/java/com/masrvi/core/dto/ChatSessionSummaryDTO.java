package com.masrvi.core.dto;

import lombok.Builder;
import lombok.Data;
import java.time.LocalDateTime;

/**
 * DTO de résumé d'une session de chat pour la liste des sessions.
 */
@Data
@Builder
public class ChatSessionSummaryDTO {
    private Long id;
    private String title;
    private LocalDateTime createdAt;
    private int messageCount;
}
