package com.masrvi.core.repository;

import com.masrvi.core.entity.ChatSession;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ChatSessionRepository extends JpaRepository<ChatSession, Long> {
    List<ChatSession> findByCreatedBy(String createdBy);
}
