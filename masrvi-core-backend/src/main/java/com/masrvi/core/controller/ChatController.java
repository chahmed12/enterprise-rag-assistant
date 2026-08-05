package com.masrvi.core.controller;

import com.masrvi.core.dto.AskRequestDTO;
import com.masrvi.core.dto.ChatResponseDTO;
import com.masrvi.core.service.ChatService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/chat")
@RequiredArgsConstructor
public class ChatController {

    private final ChatService chatService;

    @PostMapping("/ask")
    public ResponseEntity<ChatResponseDTO> ask(@RequestBody AskRequestDTO request) {
        return ResponseEntity.ok(chatService.ask(request));
    }
}
