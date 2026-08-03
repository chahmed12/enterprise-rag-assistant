package com.masrvi.core.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "documents")
@Getter
@Setter
@ToString
// Pas de relations bidirectionnelles ici, mais on garde la cohérence :
// equals/hashCode basé sur l'id uniquement (jamais sur les champs métier)
@EqualsAndHashCode(onlyExplicitlyIncluded = true)
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class DocumentMetadata {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @EqualsAndHashCode.Include
    private Long id;

    @Column(nullable = false)
    private String filename;

    @Column(nullable = false)
    private LocalDateTime uploadDate;

    // Statut : "PROCESSING", "INDEXED", "ERROR"
    @Column(nullable = false)
    private String status;

    @PrePersist
    protected void onCreate() {
        uploadDate = LocalDateTime.now();
    }
}
