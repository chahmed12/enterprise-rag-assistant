import { Component, signal, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SidebarComponent } from './components/sidebar/sidebar';
import { ChatAreaComponent } from './components/chat-area/chat-area';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, SidebarComponent, ChatAreaComponent],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  activeSessionId = signal<number | null>(null);

  @ViewChild('sidebar') private sidebar?: SidebarComponent;

  onSessionSelected(id: number) {
    this.activeSessionId.set(id);
  }

  onNewChat() {
    this.activeSessionId.set(null);
  }

  onSessionCreated(id: number) {
    this.activeSessionId.set(id);
    this.sidebar?.loadSessions();
    this.sidebar?.setActive(id);
  }
}
