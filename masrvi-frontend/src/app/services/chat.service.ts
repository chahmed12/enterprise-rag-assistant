import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  AskRequestDTO,
  ChatMessageDTO,
  ChatResponseDTO,
  ChatSessionSummaryDTO
} from '../models/api.models';

const API_URL = 'http://localhost:8080/api/chat';

@Injectable({ providedIn: 'root' })
export class ChatService {
  constructor(private http: HttpClient) {}

  /**
   * Envoie une question au backend (POST /api/chat/ask).
   * Le JWT est attaché automatiquement par l'intercepteur.
   */
  ask(request: AskRequestDTO): Observable<ChatResponseDTO> {
    return this.http.post<ChatResponseDTO>(`${API_URL}/ask`, request);
  }

  /**
   * Récupère les sessions de l'utilisateur connecté (GET /api/chat/sessions).
   */
  getSessions(): Observable<ChatSessionSummaryDTO[]> {
    return this.http.get<ChatSessionSummaryDTO[]>(`${API_URL}/sessions`);
  }

  /**
   * Récupère les messages d'une session (GET /api/chat/sessions/{id}/messages).
   */
  getSessionMessages(sessionId: number): Observable<ChatMessageDTO[]> {
    return this.http.get<ChatMessageDTO[]>(`${API_URL}/sessions/${sessionId}/messages`);
  }
}
