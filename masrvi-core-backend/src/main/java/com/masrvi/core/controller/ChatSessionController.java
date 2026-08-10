package com.masrvi.core.controller;

import com.masrvi.core.dto.ChatMessageDTO;
import com.masrvi.core.dto.ChatSessionSummaryDTO;
import com.masrvi.core.service.ChatService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * Contrôleur REST pour la gestion de l'historique des sessions de chat.
 */
@RestController
@RequestMapping("/api/chat/sessions")
@RequiredArgsConstructor
public class ChatSessionController {

    private final ChatService chatService;

    /**
     * GET /api/chat/sessions
     * Retourne la liste résumée de toutes les sessions (id, titre, date, nb messages).
     */
    @GetMapping
    public ResponseEntity<List<ChatSessionSummaryDTO>> getAllSessions() {
        return ResponseEntity.ok(chatService.getAllSessions());
    }

    /**
     * GET /api/chat/sessions/{id}/messages
     * Retourne l'historique complet des messages d'une session, ordonnés par timestamp.
     */
    @GetMapping("/{id}/messages")
    public ResponseEntity<List<ChatMessageDTO>> getSessionMessages(@PathVariable Long id) {
        return ResponseEntity.ok(chatService.getSessionMessages(id));
    }
}
