# Laboratorio #1 – Esquemas de comunicación (Reporte de la Parte 1)

**Universidad del Valle de Guatemala** · CC3067 Redes · Semestre II 2026

**Nombre:** Luis Pedro Lira · **Carnet:** 23669

> **Modalidad:** la actividad estaba pensada en parejas y en grupos de cuatro, pero la realicé **de forma
> individual** porque no tuve pareja. Para mantener el sentido de la práctica (enviar, recibir, medir errores y
> conmutar mensajes), reemplacé a los demás participantes con programas propios que se describen en la sección 2.
> Por la misma razón, el reporte grupal y la información de la "otra pareja" corresponden solo a mí.

## 1. Introducción

En esta práctica se emuló la transmisión de información de la época de la telegrafía con dos esquemas de
codificación:

- el **código Morse**, formado por pulsos cortos y largos de longitud variable;
- el **código de Baudot**, formado por palabras binarias de 5 bits de longitud fija.

Se transmitieron mensajes de al menos 10 caracteres de tres maneras: en tiempo real (3.1), de forma
"empaquetada" como notas de voz (3.2) y a través de un conmutador que recibe y reenvía los mensajes entre tres
clientes (3.3).

## 2. Metodología (adaptación individual)

| Parte | Actividad original | Cómo la realicé |
|---|---|---|
| 3.1 | Una persona transmite con la voz y la pareja decodifica | La computadora es el emisor: [simulacion/practica.py](simulacion/practica.py) reproduce el mensaje como audio y yo lo decodifico de oído. Al igual que en vivo, puedo pedir que se repita. |
| 3.2 | Se envían notas de voz por WhatsApp/Discord | El mismo programa genera cada mensaje como archivo `.wav` (la "nota de voz", guardada en `simulacion/audios/`) y lo reproduce **una sola vez**, sin opción de pedir que se repita, igual que un paquete que llega completo y no se puede reenviar en el momento. |
| 3.3 | Tres clientes y un conmutador humano | [simulacion/conmutador.py](simulacion/conmutador.py) y [simulacion/cliente.py](simulacion/cliente.py): un conmutador y tres clientes que se comunican por TCP con el protocolo de la sección 5. Los mensajes viajan codificados en Morse o Baudot. |
| Extra | — | [simulacion/canal_ruidoso.py](simulacion/canal_ruidoso.py): simula miles de transmisiones por un canal con ruido para comparar la robustez de los dos esquemas. |

**Representación sonora.** En Morse, un punto es un tono de 700 Hz de 1 unidad y una raya dura 3 unidades
(10 palabras por minuto, con pausas extendidas entre letras). En Baudot, cada bit es un tono de 250 ms: agudo
(880 Hz) para el 1 y grave (440 Hz) para el 0, con una pausa larga entre grupos de 5 bits. Es la misma idea que la
modulación por desplazamiento de frecuencia (FSK) que usaban los teletipos.

**Medición de errores.** Cada intento se registró en `herramientas/registro_intento1.csv`. Con
`python herramientas/codificador.py errores herramientas/registro_intento1.csv` se calcula, para cada mensaje, la distancia
de Levenshtein entre lo enviado y lo recibido. Esa distancia cuenta los caracteres sustituidos, perdidos o
agregados. A partir de ella se obtiene la **tasa de error por carácter (CER)**.

## 3. Resultados

### 3.1 Transmisión de códigos

| Esquema | Mensajes | Mensajes sin error | Caracteres | Errores | CER | Repeticiones pedidas | Tiempo promedio por mensaje* |
|---|---|---|---|---|---|---|---|
| Morse | 4 | 0 | 58 | 53 | 91.4 % | 0 | 36.3 s |
| Baudot | 3 | 0 | 44 | 36 | 81.8 % | 0 | 60.6 s |

\* Desde que empieza el audio hasta que se escribe la respuesta. Incluye la reproducción: unos 20–24 s por mensaje
en Morse y 38.5 s en Baudot.

| Esquema | Enviado | Recibido | Errores |
|---|---|---|---|
| Morse | BUENAS NOCHES | HOLAAAAAAAAAAAA | 14 |
| Morse | MENSAJE URGENTE | YO VOY MUY BIEN! | 14 |
| Morse | PAQUETE PERDIDO | MUCHO GUSTO | 12 |
| Morse | PAQUETE PERDIDO (2.º intento) | BUENAS NOCHES | 13 |
| Baudot | CODIGO BINARIO | HOLA | 12 |
| Baudot | TELEGRAFO VIEJO | ADIOS | 13 |
| Baudot | HOLA COMO ESTAS | HOLA | 11 |

**Ningún mensaje fue decodificado.** Al no lograr identificar los símbolos a la velocidad del audio (10 palabras
por minuto en Morse y 250 ms por bit en Baudot), las respuestas que registré no son transcripciones parciales del
mensaje, sino intentos sin relación con él. Por eso la CER cercana al 100 % indica que **no hubo comunicación
efectiva**, no que hubo errores en algunos símbolos. Tampoco sirve para comparar los esquemas entre sí: que Baudot
tenga una CER algo menor (81.8 %) se debe solo a que las respuestas fueron más cortas.

### 3.2 Transmisión "empaquetada"

Esquema elegido: **Morse**, porque su audio es más corto y su ritmo resultó menos agotador que la secuencia de
tonos de Baudot.

| Enviado | Recibido | Errores | Duración del audio | Tiempo hasta responder |
|---|---|---|---|---|
| LATENCIA ALTA | NOSE ("no sé") | 12 | 19.7 s | 28.1 s |
| SEGUNDO SEMESTRE | PARA QUE | 14 | 23.5 s | 59.2 s |
| ROUTER OCUPADO | FELIZ CUMPLEAÑOS | 12 | 24.7 s | 124.0 s |

Resumen: 3 mensajes, 0 decodificados, 38 errores en 43 caracteres (CER 88.4 %). Sin la posibilidad de pedir
"repite", el tiempo promedio para responder subió a **70.4 s**, el doble que en 3.1 con Morse (36.3 s). Aun así, el
resultado fue el mismo.

### 3.3 Conmutación de mensajes

Resultado de `python simulacion/conmutador.py --demo`: los clientes A, B y C envían 6 mensajes al mismo tiempo, y
el conmutador tiene una cola de 1 paquete y tarda 1 s en cada reenvío. Se entregaron y confirmaron **5 de 5**
mensajes con destino válido. El sexto, dirigido a un destino inexistente (`D`), fue rechazado con `NODEST`.
Extracto del registro:

```
22:14:35.443 [S] A pregunta el estado -> LISTO
22:14:35.444 [S] paquete de B en cola (1/1)
22:14:35.444 [S] procesando paquete de B: primer carácter -> destino C
22:14:35.444 [S] A pregunta el estado -> OCUPADO
22:14:35.444 [A] conmutador OCUPADO, se reintenta en 1 s
22:14:36.445 [C] <- de B: "REDES DE DATOS"
22:14:36.445 [S] C responde OK para B
22:14:36.445 [B] confirmación: C recibió el mensaje
...
22:15:04.723 [S] destino D desconocido, se avisa a C
```

El registro completo de una ejecución está en [simulacion/demo_conmutador.log](simulacion/demo_conmutador.log).

**Captura en Wireshark.** Durante la demo capturé la interfaz *Adapter for loopback traffic capture* con el filtro
`tcp port 5050`. El archivo es `capturas/lab1_23669_conmutador.pcapng` y tiene 152 paquetes. Cada mensaje del
protocolo es un segmento TCP con la carga en texto plano. Los primeros mensajes con datos son:

| Paquete | Origen → Destino (puertos) | Carga TCP |
|---|---|---|
| 4 | 54435 (cliente A) → 5050 (conmutador) | `HOLA A` |
| 6 | 5050 → 54435 | `BIENVENIDO A` |
| 22 | 54435 → 5050 | `S?` |
| 25 | 5050 → 54435 | `LISTO` |
| 28 | 54435 → 5050 | `DATA morse -... / .- / .... --- .-.. .- / -.. . ... -.. . / .-` |
| 36 | 5050 → 54435 | `RECIBIDO` |

### 3.4 Simulación de canal con ruido

Con `python simulacion/canal_ruidoso.py` (2000 mensajes por fila, semilla 2026), cada símbolo se altera con
probabilidad *p*. La mitad de las veces el símbolo se invierte y la otra mitad se pierde. En Morse, además, se
pueden perder las pausas entre letras. Cada celda muestra la CER y el porcentaje de mensajes que llegaron perfectos.

| p (error por símbolo) | Morse | Baudot | Baudot sin pérdida de bits |
|---|---|---|---|
| 1 % | 3.6 % / 65.7 % | 18.4 % / 50.1 % | 4.5 % / 50.1 % |
| 2 % | 7.3 % / 41.9 % | 33.0 % / 23.2 % | 9.6 % / 23.9 % |
| 5 % | 16.8 % / 12.4 % | 59.1 % / 3.0 % | 21.5 % / 2.9 % |
| 10 % | 31.0 % / 1.1 % | 76.3 % / 0.1 % | 39.8 % / 0.1 % |

En promedio, un mensaje necesitó **32.2 puntos/rayas en Morse** y **71.9 bits en Baudot**. Como Baudot usa más
símbolos por mensaje, tiene más oportunidades de error. Además, perder un solo bit desfasa todos los grupos de 5
bits siguientes, lo que multiplica la CER (18.4 % frente a 4.5 % con p = 1 %).

## 4. Respuestas a las preguntas

### ¿Qué esquema fue más fácil de transmitir y por qué? ¿Cuál fue más difícil y por qué?

No logré decodificar ningún mensaje con ninguno de los dos esquemas. Aun así, la experiencia fue claramente
distinta, y el **código Morse** fue el menos difícil:
- Sus símbolos tienen un ritmo reconocible.
- Las letras más frecuentes son las más cortas (E = `.`, T = `-`).
- Los mensajes son más cortos: 32 símbolos en promedio contra 72 bits en Baudot, y unos 22 s de audio contra
  38.5 s.

Por eso lo elegí para la parte 3.2.

El **código de Baudot** fue el más difícil. La frase que más me costó fue **"TELEGRAFO VIEJO"**: 15 caracteres ×
5 bits = 75 tonos casi idénticos seguidos. Entre las dificultades:
- En secuencias repetidas como `11110` o `00001` es fácil perder la cuenta de en qué bit se va.
- Si se pierde un solo bit, todos los grupos siguientes quedan desfasados (pérdida de sincronía).
- La tabla de Baudot no tiene ninguna lógica intuitiva para una persona.

Los tiempos lo reflejan: cada mensaje en Baudot tomó en promedio 60.6 s, contra 36.3 s en Morse. Baudot fue pensado
para que lo leyera una máquina (el teletipo), no un operador humano.

### ¿Qué esquema tuvo menos errores?

En mi práctica **no hay una diferencia medible**. Ningún mensaje fue decodificado en ninguno de los dos esquemas,
con una CER de 91.4 % en Morse y 81.8 % en Baudot. Como se explica en la sección 3.1, esos valores reflejan que no
hubo comunicación, no la cantidad de errores de cada esquema.

Para comparar los esquemas con datos, usé la **simulación del canal con ruido** (sección 3.4), que aplica la misma
probabilidad de error por símbolo a ambos esquemas sobre 2000 mensajes. **Morse tuvo menos errores**: con p = 1 %,
su CER fue de 3.6 %, frente a 18.4 % en Baudot, y 65.7 % de los mensajes llegaron perfectos, frente a 50.1 %. La
diferencia se debe a dos causas:

- Baudot transmite más del doble de símbolos por mensaje, así que tiene más oportunidades de error.
- La pérdida de un bit desincroniza todo el resto del mensaje. Sin pérdidas de bits, la CER de Baudot baja de
  18.4 % a 4.5 %.

### ¿Qué dificultades involucra enviar un mensaje de forma "empaquetada"?

- **No hay retroalimentación inmediata.** En vivo se puede pedir "repite"; con una nota de voz el error solo se
  detecta al final, y corregirlo implica enviar otro paquete completo (retransmisión). En mi práctica, sin la opción
  de repetir, el tiempo para responder se duplicó (70.4 s contra 36.3 s) y en un caso llegó a 124 s. Al no poder
  pedir el mensaje de nuevo, el receptor se queda "atascado" con un paquete que no logró interpretar.
- **Latencia.** No se puede decodificar hasta que el mensaje completo se graba, se envía y se descarga
  (*store-and-forward*).
- **Calidad del medio.** La compresión de audio de WhatsApp o Discord, el ruido y el volumen distorsionan los tonos
  y hacen difícil distinguir un punto de una raya o un 1 de un 0.
- **Delimitación.** Hay que acordar cómo se marca el inicio y el fin del mensaje y la separación entre letras y
  palabras.
- **Orden y tamaño.** Si un mensaje se divide en varias notas, estas pueden reproducirse fuera de orden. Las notas
  largas son más propensas a errores y más costosas de repetir.

### ¿Qué ventajas/desventajas tiene agregar más conmutadores al sistema?

**Ventajas**
- **Escalabilidad:** se conectan más clientes sin necesitar un enlace directo entre cada par. Una malla completa de
  *n* clientes necesita *n(n−1)/2* enlaces.
- **Redundancia:** si hay rutas alternativas, la caída de un conmutador no aísla a toda la red.
- **Reparto de carga:** en la demo, un solo conmutador con cola de 1 paquete obligó a los clientes a reintentar
  varias veces (`OCUPADO`). Con más conmutadores, ese tráfico se habría distribuido.
- **Cobertura:** se pueden comunicar grupos que están lejos entre sí.

**Desventajas**
- **Más retardo:** cada conmutador suma tiempo de recepción, procesamiento, cola y reenvío. En la demo, cada salto
  agregaba 1 s.
- **Más puntos de error:** cada reenvío es una oportunidad más de corromper o perder el mensaje.
- **Necesidad de enrutamiento:** cada conmutador debe saber hacia dónde enviar cada destino. Hacen falta tablas de
  rutas y aparecen problemas como los bucles.
- **Mayor costo y complejidad** de coordinación y administración.

### ¿Qué posibilidades incluye la introducción de un conmutador?

- Cualquier cliente puede comunicarse con cualquier otro usando un solo enlace propio (topología en estrella).
- **Direccionamiento:** el conmutador lee el destino del encabezado y decide a quién reenviar.
- **Almacenamiento y reenvío:** el conmutador puede guardar los mensajes en una cola si está ocupado o si el destino
  no está disponible.
- **Control de flujo:** las señales `LISTO`/`OCUPADO` evitan que se sature.
- **Verificación y notificaciones:** puede rechazar destinos inexistentes (`NODEST`) y transmitir confirmaciones
  (`OK`) o pedidos de repetición (`REP`).
- **Difusión y multidifusión:** podría enviar un mensaje a varios clientes a la vez.
- Como contrapartida, se vuelve un **punto único de falla** y un punto donde se puede leer todo el tráfico.

## 5. Protocolo utilizado en la conmutación (3.3)

**Direcciones.** Cliente 1 = `A`, Cliente 2 = `B`, Cliente 3 = `C`, conmutador = `S`.

**Formato del paquete.** El mensaje completo se codifica en Morse o Baudot con un encabezado de dos caracteres:

```
<DESTINO> <ORIGEN> <MENSAJE>
ejemplo en Morse (de A para B, "HOLA DESDE A"):
-... / .- / .... --- .-.. .- / -.. . ... -.. . / .-
 B      A    H    O   L   A     D  E  S   D  E    A
```

El conmutador **solo decodifica el primer carácter** para conocer el destino y reenvía el paquete sin modificarlo,
igual que un conmutador que lee la dirección de destino sin abrir el contenido.

**Diálogo.**

```
Cliente A                    Conmutador S                  Cliente B
   | ---- S? ------------------> |                              |
   | <--- LISTO / OCUPADO ------ |                              |
   | ---- DATA morse <código> -> | (cola FIFO)                  |
   | <--- RECIBIDO ------------- |                              |
   |                             | --- DATA morse <código> ---> |
   |                             | <-- OK A  (o REP A) -------- |
   | <--- ENTREGADO B ---------- |                              |
```

**Cómo se evita sobrecargar al conmutador.**
1. Antes de enviar, el cliente pregunta `S?` y solo transmite si recibe `LISTO`.
2. El conmutador tiene una cola de capacidad fija (1 paquete). Mientras está llena responde `OCUPADO`.
3. Con `OCUPADO`, el cliente espera 1 s y vuelve a preguntar. Es un control de flujo de tipo *stop-and-wait*.
4. Los paquetes se atienden en orden de llegada (FIFO), uno a la vez.

**Confirmación y errores.** El destino responde `OK <origen>` si decodificó el mensaje y `REP <origen>` si hubo
símbolos inválidos. En ese caso, el origen vuelve a enviar el mensaje. Si el destino no existe, el conmutador
responde `NODEST`.

## 6. Conclusiones

1. Recibir mensajes codificados de oído requiere entrenamiento. Sin práctica previa no logré decodificar ningún
   mensaje (CER entre 82 % y 91 %). Esto muestra por qué la telegrafía dependía de operadores entrenados y por qué
   se buscó automatizarla.
2. Los códigos de longitud variable como Morse son más naturales para las personas y, en este caso, más compactos
   (32 símbolos por mensaje contra 72 bits). Los de longitud fija como Baudot facilitan la automatización, pero sin
   un mecanismo de sincronización un solo bit perdido arruina el resto del mensaje. En la simulación, Baudot tuvo
   5 veces más errores que Morse con el mismo ruido.
3. La transmisión "empaquetada" permite que emisor y receptor no estén disponibles al mismo tiempo, pero agrega
   latencia y hace que cada error cueste una retransmisión completa. Sin poder pedir "repite", el tiempo de
   respuesta se duplicó.
4. Un conmutador permite comunicar a varios clientes con pocos enlaces, pero requiere un protocolo común con
   direccionamiento, control de flujo y confirmaciones. Son los mismos elementos que se observan en Wireshark en
   los encabezados de Ethernet, IP y TCP. Con ese protocolo, el conmutador programado entregó 5 de 5 mensajes.
5. Medir los errores con datos (CER) obligó a reconocer que la práctica humana no produjo una comunicación
   efectiva. Por eso, la comparación entre esquemas se apoyó en la simulación y no en impresiones.
6. Hacer la práctica sin pareja obligó a definir el protocolo de manera explícita para poder programarlo. Así quedó
   claro cuántas reglas implícitas usan dos personas cuando se comunican.

## 7. Referencias

- Kurose, J. F., & Ross, K. W. (2021). *Computer Networking: A Top-Down Approach* (8.ª ed.). Pearson.
- Wikipedia. *Morse code*. https://en.wikipedia.org/wiki/Morse_code
- Wikipedia. *Baudot code*. https://en.wikipedia.org/wiki/Baudot_code
- Baudot, J. M. E. (1888). *Printing Telegraph*, US Patent 388,244.
- Python Software Foundation. *socket — Low-level networking interface*. https://docs.python.org/3/library/socket.html
