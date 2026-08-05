package com.masrvi.core.repository;

import com.masrvi.core.entity.Message;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface MessageRepository extends JpaRepository<Message, Long> {
    List<Message> findByChatSessionIdOrderByTimestampAsc(Long sessionId);
}
