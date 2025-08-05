import { Component, OnDestroy } from '@angular/core';
import { EndpointsService } from './services/endpoints.service';

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
  selectedTab = 'comandos';
  players: string[] = [];
  backups: string[] = [];
  cpuUsage = 0;
  memoryUsage = 0;
  messageToBroadcast = '';
  serverProperties: { [key: string]: string } = {};
  selectedPlayer: string = '';
  selectedQuickCommand: any = null;
  commandResponse: string = '';

  quickCommands = [
    { label: 'Kick', value: 'kick' },
    { label: 'Ban', value: 'ban' },
    { label: 'Op', value: 'op' },
    { label: 'Deop', value: 'deop' },
    { label: 'Teleport to player', value: 'tp @s' },
    { label: 'Gamemode Survival', value: 'gamemode survival' },
    { label: 'Gamemode Creative', value: 'gamemode creative' },
    { label: 'Gamemode Adventure', value: 'gamemode adventure' },
    { label: 'Gamemode Spectator', value: 'gamemode spectator' },
  ];

  booleanKeys = [
    "accepts-transfers", "allow-flight", "allow-nether", "broadcast-console-to-ops",
    "broadcast-rcon-to-ops", "enable-command-block", "enable-jmx-monitoring",
    "enable-query", "enable-rcon", "enable-status", "enforce-secure-profile",
    "enforce-whitelist", "force-gamemode", "generate-structures", "hardcore",
    "hide-online-players", "log-ips", "online-mode", "prevent-proxy-connections",
    "pvp", "require-resource-pack", "spawn-monsters", "sync-chunk-writes",
    "use-native-transport", "white-list"
  ];

  numericKeys = [
    "entity-broadcast-range-percentage", "function-permission-level",
    "max-chained-neighbor-updates", "max-players", "max-tick-time",
    "max-world-size", "network-compression-threshold", "op-permission-level",
    "pause-when-empty-seconds", "player-idle-timeout", "query.port",
    "rate-limit", "rcon.port", "server-port", "simulation-distance",
    "spawn-protection", "text-filtering-version", "view-distance"
  ];

  selectKeys = ["difficulty", "gamemode", "region-file-compression", "level-type"];

  selectOptions: { [key: string]: string[] } = {
    difficulty: ["peaceful", "easy", "normal", "hard"],
    gamemode: ["survival", "creative", "adventure", "spectator"],
    "region-file-compression": ["none", "gzip", "zlib", "deflate"],
    "level-type": ["minecraft:normal", "minecraft:flat", "minecraft:large_biomes", "minecraft:amplified"]
  };

  constructor(private endpoints: EndpointsService) { }

  ngOnInit() {
    this.logs = localStorage.getItem('logs') || '';
    this.checkServerStatus();
    this.loadPlayers();
    this.loadMetrics();
    this.loadBackups();
    this.loadServerProperties();
    this.statusInterval = setInterval(() => {
      this.checkServerStatus();
      this.loadMetrics();
    }, 5000);
    setInterval(() => this.loadPlayers(), 10000);
  }

  ngOnDestroy() {
    clearInterval(this.logInterval);
    clearInterval(this.statusInterval);
  }

  startServer() {
    this.loading = true;
    this.endpoints.startServer().subscribe({
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
    this.endpoints.stopServer().subscribe({
      next: () => {
        clearInterval(this.logInterval);
        this.serverStatus = 'deteniendo...';
        this.logs = '';
        localStorage.removeItem('logs');
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
    this.endpoints.sendCommand(this.command).subscribe({
      next: (res: any) => {
        this.commandResponse = res.output || 'Comando ejecutado.';
        this.command = '';
      },
      error: (err) => {
        console.error(err);
        this.commandResponse = 'Error al ejecutar el comando.';
      }
    });
  }

  kickPlayer(name: string) {
    this.endpoints.kickPlayer(name).subscribe({
      next: () => this.loadPlayers(),
      error: (err) => console.error('Error al expulsar jugador:', err)
    });
  }

  banPlayer(name: string) {
    this.endpoints.banPlayer(name).subscribe({
      next: () => this.loadPlayers(),
      error: (err) => console.error('Error al banear jugador:', err)
    });
  }

  broadcastMessage() {
    if (!this.messageToBroadcast.trim()) return;
    this.endpoints.broadcastMessage(this.messageToBroadcast).subscribe({
      next: () => this.messageToBroadcast = '',
      error: (err) => console.error('Error al enviar mensaje:', err),
    });
  }

  private loadLogs() {
    this.endpoints.getLogs().subscribe({
      next: (data) => {
        if (data) {
          this.logs += data;
          localStorage.setItem('logs', this.logs);
          this.scrollToBottom();
        }
      },
      error: (err) => console.error('Error cargando logs:', err)
    });
  }

  private scrollToBottom() {
    setTimeout(() => {
      const textarea = document.querySelector('ion-textarea textarea');
      if (textarea) textarea.scrollTop = textarea.scrollHeight;
    }, 100);
  }

  private checkServerStatus() {
    this.endpoints.getStatus().subscribe({
      next: (res) => {
        this.serverStatus = res.status === 'running' ? 'en ejecución' : 'detenido';
      },
      error: () => this.serverStatus = 'error de conexión'
    });
  }

  loadPlayers() {
    this.endpoints.getPlayers().subscribe({
      next: (res) => this.players = res.players,
      error: (err) => {
        console.error('Error cargando jugadores:', err);
        this.players = [];
      }
    });
  }

  loadMetrics() {
    this.endpoints.getMetrics().subscribe({
      next: (data) => {
        this.cpuUsage = data.cpu;
        this.memoryUsage = data.memory;
      },
      error: (err) => console.error('Error cargando métricas:', err)
    });
  }

  loadBackups() {
    this.endpoints.getBackups().subscribe({
      next: (res) => this.backups = res.backups,
      error: (err) => console.error('Error cargando backups:', err)
    });
  }

  createBackup() {
    this.endpoints.createBackup().subscribe({
      next: () => this.loadBackups(),
      error: (err) => console.error('Error creando backup:', err)
    });
  }

  get stringKeys() {
    return Object.keys(this.serverProperties).filter(k =>
      !this.booleanKeys.includes(k) &&
      !this.numericKeys.includes(k) &&
      !this.selectKeys.includes(k)
    );
  }

  get propertyKeys(): string[] {
    return Object.keys(this.serverProperties);
  }

  loadServerProperties() {
    this.endpoints.getServerProperties().subscribe({
      next: (res) => {
        for (const k in res) {
          let clean = res[k].trim();
          if (this.booleanKeys.includes(k)) {
            this.serverProperties[k] = clean === 'true' ? 'true' : 'false';
          } else if (this.numericKeys.includes(k)) {
            this.serverProperties[k] = Number(clean).toString();
          } else {
            this.serverProperties[k] = clean;
          }
        }
      },
      error: (err) => console.error('Error cargando propiedades del servidor:', err)
    });
  }

  saveServerProperties() {
    const payload: { [key: string]: string } = {};
    for (const k in this.serverProperties) {
      let val = this.serverProperties[k];
      if (this.booleanKeys.includes(k)) {
        payload[k] = val === 'true' ? 'true' : 'false';
      } else {
        payload[k] = String(val);
      }
    }
    this.endpoints.saveServerProperties(payload).subscribe({
      next: () => console.log('Propiedades guardadas correctamente'),
      error: (err) => console.error('Error guardando propiedades del servidor:', err)
    });
  }

  isPortOrExtreme(key: string): boolean {
    return key.includes('port') || ['max-world-size', 'max-chained-neighbor-updates'].includes(key);
  }

  fillQuickCommand() {
    const cmd = this.selectedQuickCommand?.value || '';
    const player = this.selectedPlayer || '';
    if (cmd.includes('@s')) {
      this.command = cmd.replace('@s', player);
    } else if (player) {
      this.command = `${cmd} ${player}`;
    } else {
      this.command = cmd;
    }
  }

  runQuick(cmd: string) {
    if (!cmd.trim()) return;
    this.endpoints.sendCommand(cmd).subscribe({
      next: (res: any) => {
        this.commandResponse = res.output || 'Comando ejecutado.';
      },
      error: (err) => {
        console.error(err);
        this.commandResponse = 'Error al ejecutar el comando.';
      }
    });
  }
}
