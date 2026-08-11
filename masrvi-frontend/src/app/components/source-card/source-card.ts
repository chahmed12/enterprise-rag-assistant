import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SourceDTO } from '../../models/api.models';

@Component({
  selector: 'app-source-card',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './source-card.html',
  styleUrl: './source-card.css'
})
export class SourceCardComponent {
  @Input() source!: SourceDTO;

  get scorePercent(): string {
    if (this.source.score == null) return '';
    return Math.round(this.source.score * 100) + '%';
  }
}
