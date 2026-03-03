# Generador de Diagramas de Gantt de GitHub

Una herramienta en Python simple y elegante para generar diagramas de Gantt visuales directamente desde los issues y milestones de tu repositorio de GitHub, perfectamente integrada con los campos personalizados de GitHub Projects V2.

## Características

- **Sin configuraciones complejas**: Solo un script en Python que funciona de inmediato.
- **Agrupación por milestone**: Divide automáticamente tus issues en diagramas de Gantt por sprint (milestone).
- **Soporte para Projects V2**: Lee `Priority` (Prioridad), `Early Start` (Inicio Temprano), `Early Finish` (Final Temprano), `Late Start` (Inicio Tardío), `Late Finish` (Final Tardío), y `Estimated Duration` (Duración Estimada) de tu Proyecto de GitHub.

## Estructura del Repositorio

```
generador-diagramas/
├── .venv/                     # Entorno virtual de Python
├── charts/                    # Directorio de salida para los diagramas generados
├── data/                      # JSON cacheados de GitHub (issues y milestones)
├── src/                       # Código fuente
│   ├── main.py                # Script principal de ejecución
│   ├── config.py              # Configuración de variables (Token, Repo, Owner)
│   ├── github_api.py          # Cliente API para descargar metadata via GraphQL
│   └── gantt_generator.py     # Lógica de renderizado de diagramas (Gantt y PERT)
├── README.md                  # Este documento de ayuda
└── requirements.txt           # Dependencias del proyecto
```

## Requisitos Previos

1. Python 3.8+
2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Configuración

Edita el archivo `src/config.py` en el directorio principal para que coincida con tu repositorio.

```python
# config.py
GITHUB_OWNER = "tu_usuario_u_organizacion"
GITHUB_REPO = "tu_repositorio"
GITHUB_TOKEN = "tu_token_de_acceso_personal"  # Requerido para los campos de GraphQL de Projects V2
```

## Uso

¡Simplemente ejecuta el script principal! Obtendrá toda la información basándose en tu `config.py` y generará los resultados en el directorio `charts/`.

```bash
python src/main.py
```

### Sobrescritura de CLI

Si deseas probar rápidamente otro repositorio sin cambiar el archivo de configuración:

```bash
python src/main.py --owner sergiogarfella --repo dsr-ai --token ghp_...
```

Para volver a generar los diagramas a partir de datos JSON en caché local (sin llamadas a la API):

```bash
python main.py --from-json
```

## Configuración de Campos Personalizados en GitHub Projects

Para que el diagrama de Gantt funcione perfectamente, tu proyecto de GitHub debe contener los siguientes campos (el script los asocia por nombre en español o inglés):

1. **Priority / Prioridad** (Selección única: Alta/Media/Baja o High/Medium/Low)
2. **Early Start / Inicio Temprano** (Fecha)
3. **Early Finish / Final Temprano** (Fecha)
4. **Late Start / Inicio Tardío** (Fecha)
5. **Late Finish / Final Tardío** (Fecha)
6. **Estimated Duration / Duración Estimada** (Número)
