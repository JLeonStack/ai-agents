# VozBar

Barra de dictado flotante para macOS. Mantené presionada **Option** mientras hablás y, al soltarla, VozBar transcribe el audio y pega el texto en el campo que tenga el foco. Usa el reconocimiento de voz de Apple en el dispositivo, sin enviar audio a una API externa.

## Características

- Dictado *hold-to-talk* con Option derecha (Option izquierda también es compatible).
- Barra flotante con estado de escucha y transcripción.
- Pegado automático en la aplicación activa.
- Copia el resultado al portapapeles como alternativa si no puede pegarlo.
- Acción alternativa **Dictar / parar** desde el menú de la barra.
- Reconocimiento de voz local (*on-device*), sujeto a la disponibilidad de macOS.

## Requisitos

- macOS 14 o posterior.
- Mac compatible con reconocimiento de voz local de Apple.
- Python 3.10 con headers y librería de desarrollo disponibles.
- Xcode Command Line Tools (`clang`).

Las dependencias de Python se instalan automáticamente en `.venv` la primera vez que se ejecuta el proyecto:

- PyObjC Cocoa, Quartz, AVFoundation y Speech.

## Instalación y ejecución

Desde la carpeta `vozbar`:

```bash
./run.sh
```

El script crea un entorno virtual, instala las dependencias, construye `VozBar.app`, lo firma localmente y lo abre. Para comprobar la disponibilidad del reconocimiento antes de iniciar la app:

```bash
.venv/bin/python app.py --check
```

La salida incluye `locale`, `on_device`, `available` y el estado de autorización. El comando debe mostrar `on_device=True` y `available=True` para que el dictado local esté disponible.

## Primer uso y permisos

macOS puede solicitar estos permisos la primera vez que se abre la aplicación:

1. **Micrófono**: permite capturar la voz.
2. **Reconocimiento de voz**: permite transcribirla.
3. **Accesibilidad**: permite detectar Option y enviar `Cmd+V` a la aplicación activa.

Si un permiso fue rechazado, habilitá **VozBar** en **Configuración del Sistema → Privacidad y seguridad** y reiniciá la aplicación. El reconocimiento de voz y el micrófono se solicitan para el bundle de la app, por eso se recomienda iniciar siempre con `./run.sh` y no ejecutar `python app.py` directamente.

## Uso

1. Abrí TextEdit, Notas o cualquier campo de texto.
2. Colocá el cursor donde querés insertar el resultado.
3. Mantené presionada **Option derecha**.
4. Hablá y soltá la tecla.
5. Esperá la transcripción: VozBar pegará el texto automáticamente.

Si el pegado automático no funciona, el texto queda en el portapapeles y la barra indica que podés usar `Cmd+V`. También podés iniciar o detener el dictado desde el menú de la barra de macOS.

## Limitaciones conocidas

- No incluye limpieza de texto con IA, diccionario personal ni estilos por aplicación.
- Option es el atajo disponible actualmente; no se admite la tecla Fn.
- La disponibilidad del modo local depende de macOS y del idioma configurado.
- El proyecto no está firmado ni notarizado para distribución.
- Si falla Accesibilidad, VozBar puede transcribir y copiar, pero no confirmar que el pegado se haya realizado.

## Estructura del proyecto

- `app.py`: interfaz, barra flotante, atajo y pegado.
- `speech_engine.py`: autorización y reconocimiento de voz.
- `build_app.sh`: crea el bundle y el launcher nativo.
- `run.sh`: construye y abre la aplicación.
- `macos/Info.plist`: metadatos y descripciones de permisos.

## Licencia

Este proyecto fue creado como una automatización de dictado local para la entrega de Agentes de IA.
