# Contador de fechas importantes
Este proyecto es un script en Python diseñado para registrar fechas importantes y calcular el tiempo restante o transcurrido.

## Caracteristicas
- Registro de fechas con nombre, descripcion opcional y categoria.
- Calculo automatico de dias faltantes o dias transcurridos.
- Persistencia de datos en formato JSON legible con soporte para caracteres especiales.
- Interfaz de linea de comandos (CLI) para operaciones rapidas.
- Interfaz interactiva en consola (TUI) con barras de progreso y colores.
- Categorias con colores personalizados, filtrado y movimiento de fechas.

## Estructura del Proyecto
El codigo se organiza de forma modular para facilitar su mantenimiento:

- src/fecha_contador/models.py: Definicion de los modelos de datos y validaciones.
- src/fecha_contador/storage.py: Manejo de la persistencia de datos en archivos JSON.
- src/fecha_contador/service.py: Logica de negocio y calculos de fechas.
- src/fecha_contador/cli.py: Manejadores para la interfaz de comandos.
- src/fecha_contador/terminal_ui.py: Interfaz interactiva para el usuario.
- src/fecha_contador/app.py: Punto de entrada principal.

## Instalacion y Configuracion

### Requisitos

- Python 3.8 o superior.
- Dependencias externas: `questionary` y `rich` para la interfaz TUI.

### Instalar dependencias (TUI)

```powershell
python -m pip install questionary rich
```

### Entorno Virtual (Opcional pero recomendado)

En sistemas Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

## Uso del Sistema

### Interfaz Interactiva

Para iniciar la aplicacion con menu interactivo, ejecute:

```powershell
python run_ui.py
```

### Interfaz de Linea de Comandos (CLI)

Tambien puede interactuar directamente mediante comandos:

#### Agregar una fecha
```powershell
python run_cli.py add --name "Cumpleaños" --date "2025-10-25" --description "Dia de fiesta"
```

#### Listar todas las fechas
```powershell
python run_cli.py list
```

#### Listar por categoria
```powershell
python run_cli.py list --group "Personal"
```

#### Listar fechas pasadas y futuras
```powershell
python run_cli.py list --all
```

#### Ver la fecha mas cercana
```powershell
python run_cli.py next
```

#### Eliminar una fecha
```powershell
python run_cli.py remove --name "Cumpleaños"
```

#### Mover una fecha de categoria
```powershell
python run_cli.py move --name "Cumpleaños" --group "Personal"
```

#### Ver categorias
```powershell
python run_cli.py group list
```

#### Crear categoria con color
```powershell
python run_cli.py group add --name "Personal" --color "cyan"
```

#### Cambiar color de categoria
```powershell
python run_cli.py group color --name "Personal" --color "yellow"
```

#### Eliminar categoria (mueve fechas a otra)
```powershell
python run_cli.py group remove --name "Personal" --move-to "General"
```

## Comportamiento del CLI

- `list`: por defecto solo muestra fechas futuras; con `--all` incluye fechas pasadas.
- `next`: muestra la fecha mas cercana a hoy (pasada o futura), con el calculo de dias.
- `add`: guarda una fecha con `name`, `date`, `description` opcional y `group` opcional.
- `move`: mueve una fecha a otra categoria.
- `group`: administra categorias (listar, agregar, cambiar color y eliminar).
- `remove`: elimina una fecha por nombre.

## Datos y persistencia

- El archivo de datos se guarda en `data/important_dates.json` relativo al directorio donde se ejecuta el comando.
- El JSON incluye fechas y categorias con sus colores.
- `created_at` ahora guarda fecha y hora (YYYY-MM-DD HH:MM); los datos antiguos se migran automaticamente.
