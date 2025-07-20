import { Component, OnDestroy } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-root',
  standalone: false,
  templateUrl: 'app.component.html',
  styleUrls: ['app.component.scss'],
})
export class AppComponent implements OnDestroy {
  command = '';
  logs = '';
  serverStatus = 'detenido';
  loading = false;
  private logInterval: any;
  private statusInterval: any;
  selectedTab = 'jugadores';
  players: { name: string, joined_at: string }[] = [];

  constructor(private http: HttpClient) {
    this.checkServerStatus();
    this.loadPlayers();
    this.statusInterval = setInterval(() => this.checkServerStatus(), 5000);
  }

  ngOnDestroy() {
    clearInterval(this.logInterval);
    clearInterval(this.statusInterval);
  }

  startServer() {
    this.loading = true;
    this.http.post('http://127.0.0.1:5000/start', {}).subscribe({
      next: () => {
        this.logInterval = setInterval(() => this.loadLogs(), 1000);
        this.serverStatus = 'iniciando...';
      },
      error: (err) => {
        console.error('Error al iniciar:', err);
        this.loading = false;
      },
      complete: () => this.loading = false
    });
  }

  stopServer() {
    this.loading = true;
    this.http.post('http://127.0.0.1:5000/stop', {}).subscribe({
      next: () => {
        clearInterval(this.logInterval);
        this.serverStatus = 'deteniendo...';
      },
      error: (err) => {
        console.error('Error al detener:', err);
        this.loading = false;
      },
      complete: () => this.loading = false
    });
  }

  sendCommand() {
    if (!this.command.trim()) return;

    this.http.post('http://127.0.0.1:5000/command', { cmd: this.command }).subscribe({
      next: () => this.command = '',
      error: (err) => console.error('Error en comando:', err)
    });
  }

  private loadLogs() {
    this.http.get('http://127.0.0.1:5000/logs', { responseType: 'text' }).subscribe({
      next: (data) => {
        if (data) {
          this.logs += data;
          this.scrollToBottom();
        }
      },
      error: (err) => console.error('Error cargando logs:', err)
    });
  }

  private scrollToBottom() {
    setTimeout(() => {
      const textarea = document.querySelector('ion-textarea textarea');
      if (textarea) {
        textarea.scrollTop = textarea.scrollHeight;
      }
    }, 100);
  }

  private checkServerStatus() {
    this.http.get('http://127.0.0.1:5000/status').subscribe({
      next: (res: any) => {
        this.serverStatus = res.status === 'running' ? 'en ejecución' : 'detenido';
      },
      error: () => this.serverStatus = 'error de conexión'
    });
  }

  loadPlayers() {
    this.http.get<{ name: string, joined_at: string }[]>('http://127.0.0.1:5000/players').subscribe({
      next: (res) => this.players = res,
      error: () => this.players = []
    });
    console.log('Jugadores cargados:', this.players);
  }

  getOnlineTime(joinedAt: string): string {
    const now = new Date();
    const [hours, minutes, seconds] = joinedAt.split(':').map(Number);
    const joinedDate = new Date();
    joinedDate.setHours(hours, minutes, seconds, 0);

    const diffMs = now.getTime() - joinedDate.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffSecs = Math.floor((diffMs % 60000) / 1000);

    return `${diffMins} min ${diffSecs} seg`;
  }
}