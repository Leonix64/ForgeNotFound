import { Component, OnInit, OnDestroy } from '@angular/core';
import { EndpointsService } from 'src/app/services/endpoints.service';
import { ToastService } from 'src/app/services/toast.service';

@Component({
  selector: 'app-home',
  standalone: false,
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss'],
})
export class HomeComponent implements OnDestroy {
  serverStatus = 'Detenido';
  loading = false;
  private statusInterval: any;

  constructor(
    private endpoints: EndpointsService,
    private toast: ToastService
  ) { }

  ngOnInit() {
    this.checkServerStatus();
    this.statusInterval = setInterval(() => this.checkServerStatus(), 5000);
  }

  ngOnDestroy() {
    clearInterval(this.statusInterval);
  }

  startServer() {
    this.loading = true;
    this.endpoints.startServer().subscribe({
      next: () => {
        this.serverStatus = 'Iniciando...';
        this.toast.showToast('Servidor iniciado', 'success');
      },
      error: (err) => {
        this.toast.showToast(`Error al iniciar: ${err.message}`, 'danger');
        this.loading = false
      },
      complete: () => this.loading = false
    });
  }

  stopServer() {
    this.loading = true;
    this.endpoints.stopServer().subscribe({
      next: () => {
        this.serverStatus = 'Deteniendo...';
        this.toast.showToast('Servidor deteniendose', 'warning');
      },
      error: (err) => {
        this.toast.showToast(`Error al detener: ${err.message}`, 'danger');
        this.loading = false;
      },
      complete: () => this.loading = false
    });
  }

  private checkServerStatus() {
    this.endpoints.getStatus().subscribe({
      next: (res) => {
        this.serverStatus = res.status === 'running' ? 'En ejecucion' : 'Detenido';
      },
      error: () => this.serverStatus = 'Error de conexion'
    });
  }
}
