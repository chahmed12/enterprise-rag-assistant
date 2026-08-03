package com.masrvi.core.entity;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "sources")
@Getter
@Setter
// Exclut "message" pour éviter la boucle : Source.toString() → Message.toString() → Source...
@ToString(exclude = "message")
@EqualsAndHashCode(onlyExplicitlyIncluded = true)
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Source {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @EqualsAndHashCode.Include
    private Long id;

    // Nom du document d'où provient le texte
    @Column(nullable = false)
    private String documentName;

    // La page (peut être null si la source est un fichier .txt sans pages)
    private Integer page;

    // Le message (réponse IA) auquel cette source est attachée
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "message_id", nullable = false)
    private Message message;
}
