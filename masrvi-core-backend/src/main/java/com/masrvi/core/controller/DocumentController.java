package com.masrvi.core.controller;

import com.masrvi.core.client.RagEngineClient;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.Map;

/**
 * Contrôleur REST pour la gestion des documents dans le moteur RAG.
 * Sert de proxy entre le frontend Angular et l'API Python FastAPI.
 */
@RestController
@RequestMapping("/api/documents")
@RequiredArgsConstructor
public class DocumentController {

    private final RagEngineClient ragClient;

    /**
     * Recharge l'index vectoriel du moteur RAG depuis le disque.
     * Utile après une ingestion manuelle de fichiers.
     *
     * @return HTTP 200 OK si le rechargement a réussi.
     */
    @PostMapping("/reload")
    public ResponseEntity<Map<?, ?>> reload() {
        return ResponseEntity.ok(ragClient.reload());
    }

    /**
     * Ingère un nouveau document dans la base vectorielle du moteur RAG.
     * Le fichier est transféré directement vers l'API Python.
     *
     * @param file Le fichier à ingérer (form-data, clé "file").
     * @return La réponse JSON du moteur RAG Python.
     */
    @PostMapping("/ingest")
    public ResponseEntity<Map<?, ?>> ingest(@RequestParam("file") MultipartFile file) throws IOException {
        return ResponseEntity.ok(ragClient.ingest(file));
    }
}
