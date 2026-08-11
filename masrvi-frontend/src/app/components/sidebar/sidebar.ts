import { Component, signal, output, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChatService } from '../../services/chat.service';
import { ChatSessionSummaryDTO } from '../../models/api.models';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './sidebar.html',
  styleUrl: './sidebar.css'
})
export class SidebarComponent implements OnInit {
  newChat = output<void>();
  sessionSelected = output<number>();

  sessions = signal<ChatSessionSummaryDTO[]>([]);
  activeSessionId = signal<number | null>(null);
  isLoadingSessions = signal(false);

  constructor(
    private chatService: ChatService
  ) {}

  ngOnInit() {
    this.loadSessions();
  }

  loadSessions() {
    this.isLoadingSessions.set(true);
    this.chatService.getSessions().subscribe({
      next: (sessions) => {
        this.sessions.set(sessions);
        this.isLoadingSessions.set(false);
      },
      error: () => {
        this.isLoadingSessions.set(false);
      }
    });
  }

  onNewChat() {
    this.activeSessionId.set(null);
    this.newChat.emit();
  }

  onSessionClick(id: number) {
    this.activeSessionId.set(id);
    this.sessionSelected.emit(id);
  }

  setActive(id: number) {
    this.activeSessionId.set(id);
  }
}
