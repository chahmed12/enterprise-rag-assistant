package com.masrvi.core.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

/**
 * Configuration du client HTTP vers le moteur RAG (FastAPI).
 * Timeouts explicites pour ne jamais bloquer le backend pendant un appel IA.
 */
@Configuration
public class RestClientConfig {

    @Bean
    public RestClient ragRestClient(RestClient.Builder builder,
                                    @Value("${rag.engine.url}") String ragEngineUrl) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(5000);   // connexion : 5 s
        factory.setReadTimeout(60000);     // réponse IA : 60 s
        return builder
                .baseUrl(ragEngineUrl)
                .requestFactory(factory)
                .build();
    }
}
