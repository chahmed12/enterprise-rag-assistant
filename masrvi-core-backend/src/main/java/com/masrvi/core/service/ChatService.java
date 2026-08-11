package com.masrvi.core.service;

import com.masrvi.core.client.RagEngineClient;
import com.masrvi.core.dto.*;
import com.masrvi.core.entity.*;
import com.masrvi.core.repository.*;
import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.List;


@Service
@RequiredArgsConstructor
public class ChatService {

    private static final String DEFAULT_USER = "anonymous";

    private final ChatSessionRepository sessionRepo;
    private final MessageRepository messageRepo;
    private final RagEngineClient ragClient;

    // Pas de @Transactional ici pour éviter de bloquer la base pendant l'appel HTTP
    public ChatResponseDTO ask(AskRequestDTO request) {
        String createdBy = DEFAULT_USER;

        // 1. Récupérer ou créer la session
        ChatSession session;
        if (request.sessionId() != null) {
            session = sessionRepo.findById(request.sessionId())
                    .orElseThrow(() -> new EntityNotFoundException(
                            "La session de chat avec l'ID " + request.sessionId() + " n'existe pas."));
        } else {
            session = sessionRepo.save(ChatSession.builder()
                    .title("Session du " + java.time.LocalDate.now())
                    .createdBy(createdBy)
                    .build());
        }

        // 2. Sauvegarder le message USER
        Message userMessage = Message.builder()
                .role("USER")
                .content(request.question())
                .chatSession(session)
                .build();
        userMessage = messageRepo.save(userMessage);

        // 3. Appeler le RAG Engine (FastAPI) hors transaction
        // Le client lève RagEngineException en cas d'erreur (réseau ou HTTP) → HTTP 503
        RagEngineClient.RagResponse ragResponse = ragClient.ask(request.question(), request.sourceFilter(), request.typeFilter());

        // 4. Sauvegarder la réponse AI + ses sources
        Message aiMessage = Message.builder()
                .role("AI")
                .content(ragResponse.getReponse())
                .chatSession(session)
                .build();

        if (ragResponse.getSources() != null && !ragResponse.getSources().isEmpty()) {
            List<Source> sources = ragResponse.getSources().stream()
                    .map(s -> Source.builder()
                            .documentName(s.documentName()) // Appel sur un record (parenthèses au lieu de get)
                            .page(s.page())
                            .section(s.section())
                            .score(s.score())
                            .message(aiMessage)
                            .build())
                    .toList();
            aiMessage.setSources(sources);
        }

        // La cascade JPA sauvegarde l'AI Message ET ses Sources en base (1 transaction
        // implicite)
        Message savedAiMessage = messageRepo.save(aiMessage);

        // 5. Construire la réponse DTO (Records)
        return new ChatResponseDTO(
                session.getId(),
                toDTO(userMessage),
                toDTO(savedAiMessage));
    }

    private ChatMessageDTO toDTO(Message m) {
        List<SourceDTO> sourceDTOs = null;
        if (m.getSources() != null && !m.getSources().isEmpty()) {
            sourceDTOs = m.getSources().stream()
                    .map(s -> new SourceDTO(s.getDocumentName(), s.getPage(), s.getScore(), s.getSection()))
                    .toList();
        }
        return new ChatMessageDTO(m.getId(), m.getRole(), m.getContent(), m.getTimestamp(), sourceDTOs);
    }

    /**
     * Retourne la liste résumée de toutes les sessions (id, titre, date, nombre de messages).
     */
    @Transactional(readOnly = true)
    public List<ChatSessionSummaryDTO> getAllSessions() {
        return sessionRepo.findByCreatedBy(DEFAULT_USER).stream()
                .map(s -> ChatSessionSummaryDTO.builder()
                        .id(s.getId())
                        .title(s.getTitle())
                        .createdAt(s.getCreatedAt())
                        .messageCount(s.getMessages().size())
                        .build())
                .toList();
    }

    /**
     * Retourne l'historique ordonné des messages d'une session.
     * Lève EntityNotFoundException si la session est introuvable.
     */
    @Transactional(readOnly = true)
    public List<ChatMessageDTO> getSessionMessages(Long sessionId) {
        sessionRepo.findById(sessionId)
                .orElseThrow(() -> new EntityNotFoundException("La session de chat avec l'ID " + sessionId + " n'existe pas."));
        
        return messageRepo.findByChatSessionIdOrderByTimestampAsc(sessionId)
                .stream()
                .map(this::toDTO)
                .toList();
    }
}