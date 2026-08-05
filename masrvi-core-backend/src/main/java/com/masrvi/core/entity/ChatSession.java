package com.masrvi.core.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "chat_sessions")
@Getter
@Setter
// @ToString exclut "messages" pour éviter la boucle infinie (ChatSession →
// Message → ChatSession...)
@ToString(exclude = "messages")
// equals/hashCode uniquement sur l'id pour éviter le chargement lazy de toute
// la liste
@EqualsAndHashCode(onlyExplicitlyIncluded = true)
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ChatSession {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @EqualsAndHashCode.Include // seul le id est utilisé pour comparer deux sessions
    private Long id;

    private String title;

    @Column(nullable = false)
    private LocalDateTime createdAt;

    // Relation 1 à N : Une session contient plusieurs messages
    @OneToMany(mappedBy = "chatSession", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    private List<Message> messages = new ArrayList<>();

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
}
