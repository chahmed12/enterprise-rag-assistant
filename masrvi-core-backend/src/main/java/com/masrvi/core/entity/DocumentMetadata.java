package com.masrvi.core.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.List;

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

    @Column
    private String department;

    @Enumerated(EnumType.STRING)
    @Column
    private DocumentVisibility visibility;

    @ElementCollection(fetch = FetchType.EAGER)
    @CollectionTable(name = "document_allowed_departments", joinColumns = @JoinColumn(name = "document_id"))
    @Column(name = "department_name")
    private List<String> allowedDepartments;

    @PrePersist
    protected void onCreate() {
        uploadDate = LocalDateTime.now();
    }
}
