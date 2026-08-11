import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SourceCardComponent } from '../source-card/source-card';
import { SourceDTO } from '../../models/api.models';

export interface ChatMessage {
  id: number;
  role: 'USER' | 'AI';
  content: string;
  timestamp?: string;
  sources?: SourceDTO[];
}

@Component({
  selector: 'app-chat-message',
  standalone: true,
  imports: [CommonModule, SourceCardComponent],
  templateUrl: './chat-message.html',
  styleUrl: './chat-message.css'
})
export class ChatMessageComponent {
  @Input() message!: ChatMessage;

  get isUser(): boolean {
    return this.message.role === 'USER';
  }
}
