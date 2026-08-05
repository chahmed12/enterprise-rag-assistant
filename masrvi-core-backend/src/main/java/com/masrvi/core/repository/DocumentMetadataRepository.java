package com.masrvi.core.repository;

import com.masrvi.core.entity.DocumentMetadata;
import org.springframework.data.jpa.repository.JpaRepository;

public interface DocumentMetadataRepository extends JpaRepository<DocumentMetadata, Long> {
}