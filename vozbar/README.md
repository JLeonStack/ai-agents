# VozBar

> Dictado de voz local para macOS.

## Qué construí

VozBar es una mini barra flotante para macOS que transcribe lo que hablo mientras mantengo apretada la tecla Option. Al soltarla pega el texto en el campo que tenga el foco, usando el reconocimiento de voz de Apple on-device sin llamar a una API externa. La armé para la entrega de Agentes de IA, como una automatización de dictado simple y local.

## Cómo se lo pedí

1. "Quiero una app chica de speech-to-text para macOS. Una barra flotante que se active mientras mantengo apretada una tecla, y al soltar pegue el texto donde esté el cursor. Si puede ser sin API externa, mejor, porque la consigna pide no depender de servicios de afuera."

2. "Fijate en Willow Dictation y Wispr Flow como referencia: hold-to-talk, soltar y el texto aparece en el campo de destino."

3. "En el repo ya tengo un proyecto que se llama Taller. Reemplazá todo por este nuevo, VozBar."

4. "Implementalo con reconocimiento de voz on-device. Si se rompe por permisos de macOS o por PyObjC, iterá hasta que funcione, no pares en el primer error."

5. "Cuando termines, dejame el README con el formato que pide la materia, así lo corrige el agente."

## Qué funciona

- `python app.py --check` devuelve `locale=es-MX`, `on_device=True`, `available=True` en mi Mac (Apple Silicon, macOS 26).
- Correr `./run.sh` construye `VozBar.app` y lo abre. La primera vez pide permisos de Micrófono, Reconocimiento de voz y Accesibilidad.
- Uso: pongo el cursor en TextEdit o Notas, mantengo Option derecha, hablo, suelto. Aparece "Transcribiendo..." y luego pega el texto. Si no pega, queda en el portapapeles y la barra muestra `Cmd+V`.
- El menú de la barra tiene "Dictar / parar" como fallback si Option no dispara o falta Accesibilidad.

## Qué falta o qué falló

- No es un clon completo de Wispr/Willow: le falta limpieza con IA, diccionario personal, estilo por app, soporte para la tecla Fn (usamos Option), empaquetado firmado/notarizado y soporte para Windows/iPhone.
- Errores que aparecieron y corregí: `python app.py` crasheaba por TCC porque el bundle no tenía `NSSpeechRecognitionUsageDescription`; PyObjC tiró `BadPrototypeError` por nombres de métodos; el primer launcher C no encontraba `PYTHONHOME` ni el path del repo; al correrlo desde Cursor el crash report decía `responsibleProc: Cursor`, así que ahora se abre con `open VozBar.app`.
- El reconocimiento on-device pide autorización en el primer `open`: hasta aceptar el diálogo, la barra avisa que falta el permiso.
- No hay forma de saber si el `Cmd+V` realmente pegó; si Accesibilidad falla, el texto queda copiado nada más.

## Qué aprendí

Trabajar con un agente es más un loop de probar y corregir que pedir código y listo. Yo describí el producto, el agente compiló, leyó los crash reports de macOS y ajustó el launcher, y yo fui recortando el alcance para que entre en una tarde. Aprendí que en macOS "local" no es solo usar Speech: los permisos siguen al bundle que corre el binario. Sin un `.app` con `Info.plist` correcto, el script de Python muere en TCC. También entendí que la magia de Wispr/Willow no es la barra flotante, sino el modelo que limpia la transcripción; nosotros dejamos eso afuera para cumplir la consigna.

¿No sabés crear el repositorio? Pedíselo a tu tutor IA, literalmente así:

Soy principiante. Quiero crear un repositorio público en GitHub desde el navegador,
subir mis archivos y un README, sin usar la terminal. Guiame paso a paso,
uno por vez, y esperá mi confirmación antes de seguir.
