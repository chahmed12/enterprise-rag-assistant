import { Component, signal, ElementRef, ViewChild, AfterViewChecked, Input, OnChanges, SimpleChanges, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatMessageComponent } from '../chat-message/chat-message';
import { ChatService } from '../../services/chat.service';
import { ChatMessageDTO, SourceDTO } from '../../models/api.models';

// On réutilise l'interface locale pour le rendu du composant chat-message
export interface UiMessage {
  id: number;
  role: 'USER' | 'AI';
  content: string;
  timestamp?: string;
  sources?: SourceDTO[];
}

@Component({
  selector: 'app-chat-area',
  standalone: true,
  imports: [CommonModule, FormsModule, ChatMessageComponent],
  templateUrl: './chat-area.html',
  styleUrl: './chat-area.css'
})
export class ChatAreaComponent implements AfterViewChecked, OnChanges {
  @ViewChild('messagesList') private messagesList!: ElementRef;
  @Input() sessionId: number | null = null;
  sessionCreated = output<number>();

  question = signal('');
  isLoading = signal(false);
  messages = signal<UiMessage[]>([]);

  private shouldScrollToBottom = false;

  constructor(private chatService: ChatService) {}

  ngOnChanges(changes: SimpleChanges) {
    if (changes['sessionId'] && this.sessionId !== null) {
      this.loadSessionMessages(this.sessionId);
    } else if (changes['sessionId'] && this.sessionId === null) {
      // Nouvelle session : on réinitialise avec le message de bienvenue
      this.messages.set([{
        id: 0,
        role: 'AI',
        content: 'Bonjour ! Je suis MASRVI, votre assistant documentaire. Posez-moi une question sur vos documents internes et je vous répondrai avec des sources précises.',
      }]);
    }
  }

  loadSessionMessages(sessionId: number) {
    this.isLoading.set(true);
    this.chatService.getSessionMessages(sessionId).subscribe({
      next: (dtos) => {
        this.messages.set(dtos.map(this.mapDto));
        this.isLoading.set(false);
        this.shouldScrollToBottom = true;
      },
      error: () => this.isLoading.set(false)
    });
  }

  private mapDto(dto: ChatMessageDTO): UiMessage {
    return {
      id: dto.id,
      role: dto.role,
      content: dto.content,
      timestamp: dto.timestamp
        ? new Date(dto.timestamp).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
        : undefined,
      sources: dto.sources ?? []
    };
  }

  ngAfterViewChecked() {
    if (this.shouldScrollToBottom) {
      this.scrollToBottom();
      this.shouldScrollToBottom = false;
    }
  }

  private scrollToBottom(): void {
    try {
      this.messagesList.nativeElement.scrollTop = this.messagesList.nativeElement.scrollHeight;
    } catch(err) { /* ignore */ }
  }

  onSend() {
    const q = this.question().trim();
    if (!q || this.isLoading()) return;

    const userMsg: UiMessage = {
      id: Date.now(),
      role: 'USER',
      content: q,
      timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
    };
    this.messages.update(msgs => [...msgs, userMsg]);
    this.question.set('');
    this.isLoading.set(true);
    this.shouldScrollToBottom = true;

    this.chatService.ask({ sessionId: this.sessionId, question: q }).subscribe({
      next: (res) => {
        // Mettre à jour la session active si c'est une nouvelle session
        if (!this.sessionId) {
          this.sessionId = res.sessionId;
          this.sessionCreated.emit(res.sessionId);
        }
        const aiMsg: UiMessage = this.mapDto(res.aiMessage);
        this.messages.update(msgs => [...msgs, aiMsg]);
        this.isLoading.set(false);
        this.shouldScrollToBottom = true;
      },
      error: () => {
        const errMsg: UiMessage = {
          id: Date.now(),
          role: 'AI',
          content: 'Une erreur est survenue. Vérifiez que le moteur RAG est en ligne et réessayez.',
        };
        this.messages.update(msgs => [...msgs, errMsg]);
        this.isLoading.set(false);
      }
    });
  }

  onKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.onSend();
    }
  }
}
