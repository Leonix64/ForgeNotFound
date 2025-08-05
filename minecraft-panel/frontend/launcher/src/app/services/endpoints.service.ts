import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from 'src/environments/environment.prod';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class EndpointsService {
  private apiUrl = environment.apiUrl

  constructor(private http: HttpClient) { }

  startServer(): Observable<any> {
    return this.http.post(`${this.apiUrl}/start`, {});
  }

  stopServer(): Observable<any> {
    return this.http.post(`${this.apiUrl}/stop`, {});
  }

  sendCommand(cmd: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/command`, { cmd });
  }

  kickPlayer(name: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/kick`, { name });
  }

  banPlayer(name: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/ban`, { name });
  }

  broadcastMessage(msg: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/say`, { msg });
  }

  getLogs(): Observable<string> {
    return this.http.get(`${this.apiUrl}/logs`, { responseType: 'text' });
  }

  getStatus(): Observable<any> {
    return this.http.get(`${this.apiUrl}/status`);
  }

  getPlayers(): Observable<{ players: string[]; count: number }> {
    return this.http.get<{ players: string[]; count: number }>(`${this.apiUrl}/players/online`);
  }

  getMetrics(): Observable<{ cpu: number; memory: number }> {
    return this.http.get<{ cpu: number; memory: number }>(`${this.apiUrl}/metrics`);
  }

  getBackups(): Observable<{ backups: string[] }> {
    return this.http.get<{ backups: string[] }>(`${this.apiUrl}/backups`);
  }

  createBackup(): Observable<any> {
    return this.http.post(`${this.apiUrl}/backup`, {});
  }

  getServerProperties(): Observable<{ [key: string]: string }> {
    return this.http.get<{ [key: string]: string }>(`${this.apiUrl}/server_properties`);
  }

  saveServerProperties(payload: { [key: string]: string }): Observable<any> {
    return this.http.post(`${this.apiUrl}/save_properties`, payload);
  }
}
