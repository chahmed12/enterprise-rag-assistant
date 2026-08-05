package com.masrvi.core.service;

import com.masrvi.core.client.RagEngineClient;
import com.masrvi.core.dto.*;
import com.masrvi.core.entity.*;
import com.masrvi.core.exception.RagEngineException;
import com.masrvi.core.repository.*;
import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.util.List;


@Service
@RequiredArgsConstructor
public class ChatService {

    private final ChatSessionRepository sessionRepo;
    private final MessageRepository messageRepo;
    private final RagEngineClient ragClient;

    // Pas de @Transactional ici pour éviter de bloquer la base pendant l'appel HTTP
    public ChatResponseDTO ask(AskRequestDTO request) {
        // 1. Récupérer ou créer la session
        ChatSession session;
        if (request.sessionId() != null) {
            session = sessionRepo.findById(request.sessionId())
                    .orElseThrow(() -> new EntityNotFoundException(
                            "La session de chat avec l'ID " + request.sessionId() + " n'existe pas."));
        } else {
            session = sessionRepo.save(ChatSession.builder().title("Session du " + java.time.LocalDate.now()).build());
        }

        // 2. Sauvegarder le message USER
        Message userMessage = Message.builder()
                .role("USER")
                .content(request.question())
                .chatSession(session)
                .build();
        userMessage = messageRepo.save(userMessage);

        // 3. Appeler le RAG Engine (FastAPI) hors transaction
        RagEngineClient.RagResponse ragResponse;
        try {
            ragResponse = ragClient.ask(request.question());
        } catch (Exception e) {
            throw new RagEngineException("Erreur de communication avec le moteur RAG (IA indisponible).", e);
        }

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
                    .map(s -> new SourceDTO(s.getDocumentName(), s.getPage(), null))
                    .toList();
        }
        return new ChatMessageDTO(m.getId(), m.getRole(), m.getContent(), sourceDTOs);
    }
}