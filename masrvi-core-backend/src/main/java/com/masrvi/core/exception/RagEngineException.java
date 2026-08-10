package com.masrvi.core.exception;

public class RagEngineException extends RuntimeException {
    public RagEngineException(String message) {
        super(message);
    }

    public RagEngineException(String message, Throwable cause) {
        super(message, cause);
    }
}
