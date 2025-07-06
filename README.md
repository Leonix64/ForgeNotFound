# ⚙️ Minecraft Fabric Server - 1.21.6

Servidor de Minecraft personalizado usando Fabric Loader para la versión 1.21.6 con mods optimizados para rendimiento, estética y experiencia inmersiva.

---

## 🧱 Características

- Basado en **Fabric Loader 0.16.14**
- Compatible con **Minecraft 1.21.6**
- ✅ Mods de rendimiento: `Lithium`, `Sodium`, `FerriteCore`
- 🎨 Mods visuales/físicos: `Iris`, `Physics Mod`, `Visuality`
- ⚙️ Soporte para configuración personalizada

---

## 📁 Estructura del Proyecto

```bash
.
├── mods/                  # Mods instalados
├── config/                # Configs personalizadas
├── .fabric/               # Archivos técnicos de Fabric
├── libraries/             # Dependencias necesarias
├── server.jar             # Jar del servidor oficial de Mojang
├── fabric-server-*.jar    # Launcher oficial de Fabric
└── server.properties      # Config básica del servidor
```

---

## 🔧 Requisitos y Guía de Instalación

### 💾 1. Descargar el servidor oficial de Minecraft

👉 [minecraft.net/en-us/download/server](https://www.minecraft.net/en-us/download/server)  
👉 [mcversions.net](https://mcversions.net/) *(para versiones anteriores como 1.21.6)*

Busca la sección de **Java Edition Server** y descarga el `.jar`.

---

### 🧬 2. Descargar el Fabric Installer

👉 [fabricmc.net/use](https://fabricmc.net/use/)  
Selecciona la pestaña **"Server"** y usa:
- Minecraft Version: `1.21.6`
- Loader Version: `0.16.14` (o la más reciente estable)

Haz clic en **"Download Server Executable (.jar)"**.

---

### 📦 3. Instalar el servidor de Fabric

Ejecuta el installer con doble clic o por consola:

```bash
java -jar fabric-installer-*.jar server -mcversion 1.21.6 -downloadMinecraft
```

Se generarán archivos como:
- `fabric-server-mc.1.21.6-loader.0.16.14-launcher.1.0.3.jar`
- `server.jar`
- `fabric-server-launcher.properties`

---

### 🧪 4. Aceptar la EULA

Edita el archivo `eula.txt` y escribe:

```txt
eula=true
```

---

### 🚀 5. Ejecutar el servidor

Comando recomendado (con 8 GB de RAM):

```bash
java -Xmx8G -Xms4G -jar ./.fabric/server/fabric-loader-server-0.16.14-minecraft-1.21.6.jar nogui
```

Alternativa:

```bash
java -Xmx4G -Xms2G -jar fabric-server-mc.1.21.6-loader.0.16.14-launcher.1.0.3.jar nogui
```

Ejemplo de `.bat` para Windows:

```bat
@echo off
java -Xmx8G -Xms4G -jar .\.fabric\server\fabric-loader-server-0.16.14-minecraft-1.21.6.jar nogui
pause
```

---

### 🧩 6. Instalar mods

1. Crea la carpeta `mods/`
2. Mete ahí los `.jar` compatibles con **1.21.6** y **Fabric**

👉 [modrinth.com](https://modrinth.com/)  
👉 [curseforge.com/minecraft/mc-mods](https://www.curseforge.com/minecraft/mc-mods)

---

### 🛡️ 7. Configurar seguridad y acceso

- `server.properties`: Cambia puerto, online-mode, dificultad, etc.
- `whitelist.json`: Lista blanca de jugadores permitidos
- `ops.json`: Lista de operadores/admins

---

## 🎮 ¡Listo para jugar!

Ahora solo te queda prender el servidor y disfrutar. Puedes subir este proyecto a Git y mantenerlo versionado como Dios manda.

