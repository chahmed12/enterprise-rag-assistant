// ===== Chat =====
export interface SourceDTO {
  documentName: string;
  page?: number;
  score?: number;
  section?: string;
}

export interface ChatMessageDTO {
  id: number;
  role: 'USER' | 'AI';
  content: string;
  timestamp: string;
  sources?: SourceDTO[];
}

export interface ChatResponseDTO {
  sessionId: number;
  userMessage: ChatMessageDTO;
  aiMessage: ChatMessageDTO;
}

export interface AskRequestDTO {
  sessionId?: number | null;
  question: string;
  sourceFilter?: string | null;
  typeFilter?: string | null;
}

export interface ChatSessionSummaryDTO {
  id: number;
  title: string;
  createdAt: string;
  messageCount: number;
}
