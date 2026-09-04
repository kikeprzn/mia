# Ejercicio 2 — Descripción PEAS de agentes inteligentes

## Objetivo

Analizar diferentes aplicaciones de agentes inteligentes utilizando el modelo **PEAS**:

- **P — Performance:** ¿Cómo se evalúa el desempeño del agente?
- **E — Environment:** ¿En qué entorno opera?
- **A — Actuators:** ¿Qué acciones puede realizar?
- **S — Sensors:** ¿Qué información puede percibir?

## Aplicaciones

Realizar una descripción PEAS para:

1. Asistente virtual de voz.
2. Robot aspirador doméstico.
3. Sistema de recomendación de streaming.
4. Vehículo autónomo en ciudad.
5. Agente de trading algorítmico.
6. Sistema de diagnóstico médico asistido por IA.
7. Dron de inspección de infraestructura.
8. Agente jugador de ajedrez.

## Formato

Para cada aplicación:

### N. Nombre de la aplicación

- **Performance:** métricas utilizadas para evaluar su desempeño.
- **Environment:** entorno donde opera y su clasificación (observable, estocástico, secuencial, dinámico, etc.).
- **Actuators:** acciones que puede ejecutar.
- **Sensors:** información que puede percibir.

## Entrega

Un documento con las **8 descripciones PEAS**, incluyendo los cuatro componentes para cada agente y una breve justificación de la clasificación de su entorno.

> Las respuestas deben ser elaboradas sin el uso de IA.

### 1. Asistente virtual de voz

- **P**: Porcentajes de respuestas positivas, tiempo de respuesta bajo, claridad de la respuesta

- **E**: Casa o espacio personal con uno o múltiples usuarios, ruido ambiental y dispositivos conectados:
  - Es parcialmente observable porque el asistente solo percibe la voz, el contexto disponible y algunos datos del mismo dispositivo, pero no conoce completamente la intención del usuario.
  - Es multiagente porque interactúa con uno o varios usuarios y puede coordinarse con otras aplicaciones o dispositivos.
  - Es estocástico y dinámico porque el usuario, el ruido y los dispositivos pueden cambiar mientras el agente está funcionando.
  - Es principalmente secuencial porque muchas respuestas dependen de lo dicho antes en la conversación
  - Dinámico puede haber otra persona hablando, pueden cambiar el tema rápidamente para una consulta, puede aparecer ruido, los dispositivos pueden cambiar.
  - Continuo porque las entradas de interacción van cambiando, el volumen de voz, el acento, el idioma, tiempo, etc. Son condiciones variables
  - Conocido porque el agente conoce que puede hacer, sabe que puede escuchar, responder por voz, interactuar con apps y con dispositivos.

- **A**: Responder por voz, conexión a internet, interacción con otras aplicaciones, interacción con otros dispositivos, mostrar texto o imágenes en pantalla si es el caso.
- **S**: Micrófono, idioma detectado, ubicación aproximada o GPS, hora actual y memoria del contexto del usuario.

### 2. Robot aspirador doméstico

- **P**: Tiempo que un espacio pasa limpio, tiempo promedio en limpiar un espacio, ratio en el uso de batería y el espacio que se limpió, porcentaje del espacio cubierto.
- **E**: Una casa, pero pueden ser varios tipos de estructuras, muebles paredes, animales, personas, tipos de suelos, escalones, etc:
  - Parcialmente observable, porque el robot no puede ver todo desde su lugar, puede construir el mapa pero es un ambiente que puede cambiar, se mueve un mueble, hay algo en el suelo. etc.
  - Es principalmente de agente único, aunque puede volverse multiagente si hay otros robots moviéndose en la casa.
  - Estocástico, lo que tiene que limpiar siempre puede ser diferente para el robot
  - Secuencial, tiene que recordar dónde empezó y que ya limpió.
  - Es dinámico, el ambiente puede cambiar mientras limpia.
  - Es continuo, el movimiento, las distancias y la posición de cosas en el ambiente puede cambiar.
  - Es conocido, porque el robot conoce que puede hacer y que es lo que sucederá en el entorno con sus acciones.

- **A**: Activar aspiradora, activar cepillos, moverse hacia adelante y girar.
- **S**: Algún tipo de cámara/lidar para mapear el entorno, sensores de proximidad, desnivel y para detectar suciedad.

### 3. Sistema de recomendación de streaming

- **P**: Porcentaje de recomendaciones agradables para el usuario, cantidad de recomendaciones seleccionadas, tiempo de reproducción, si la calificó y si fueron positivas
- **E**: La plataforma de streaming, la ubicación del dispositivo, el tipo de usuario, niño, adolescente, adulto, adulto mayor.
  - Parcialmente observable, pues no sabe los gustos desde el principio
  - Es multiagente porque interactúa con usuarios y sus decisiones modifican la información que usa el recomendador.
  - Estocástico pues los usuarios no se comportan de la misma manera y las preferencias pueden cambiar.
  - Es secuencial porque los siguientes pasos son afectados por el estado actual, pues son recomendaciones cada vez más personalizadas construidas a través del uso del usuario.
  - Es dinámico porque los gustos, las opciones disponibles y las tendencias pueden ir cambiando.
  - Es discreto, porque las recomendaciones se eligen de un catálogo finito, aunque existan muchas combinaciones posibles.
  - Es conocido, porque el agente sabe que acciones puede hacer y cómo presentar recomendaciones.

- **A**: Mostrar listas de recomendaciones, ocultar opciones poco relevantes, pedir feedback al usuario.
- **S**: Búsquedas del usuario, historial de reproducción del usuario, feedback hecho por el usuario, los clicks en más información del usuario en las opciones (muestra lo que le va interesando), contenido que no le gustó

### 4. Vehículo autónomo en ciudad

- **P**: Seguridad, eficiencia, calidad de manejo, cumplimiento con las normas de tránsito, intervención humana
- **E**: Carreteras, autopistas, peatones, otros vehículos. semáforos y señales:
  - Es parcialmente observable, el vehículo puede ver su entorno pero no sabe lo que los otros actores van a hacer
  - Es multiagente porque comparte entorno con otros vehículos, peatones y otras personas alrededor.
  - Estocástico porque el ambiente y los actores nunca van a comportarse de la misma manera.
  - Es secuencial porque las acciones pasadas del agente afectan el entorno y las decisiones futuras.
  - Es dinámico porque el ambiente siempre va a cambiar mientras el agente está pensando.
  - Es continuo porque la cantidad de estados diferentes del ambiente es infinito.
  - Es parcialmente conocido porque aunque conoce las reglas generales de manejo, puede haber excepciones y situaciones peculiares, como por ejemplo reglas especiales en rotondas, que pueden variar de país o ciudad.

- **A**: El volante, freno, acelerador, intermitentes, señales para doblar, claxon, pantalla del carro, sistemas de sonido
- **S**: Cámaras, acelerómetros, GPS, sensores típicos del carro para detectar fallas de las piezas, sensores para checar el motor, micrófonos, pantalla dentro del carro

### 5. Agente de trading algorítmico en bolsa

- **P**: Profit, porcentaje de operaciones positivas, pérdidas evitadas, control de riesgo y rendimiento de la inversión

- **E**: Servicio/app de trading:
  - Parcialmente observable, puede saber cómo vender pero no lo que los demás van a hacer
  - Es multiagente porque participa en un mercado con otros compradores, y vendedores
  - Estocástico, porque no se puede predecir con certeza cómo cambiarán los precios ni cómo actuarán los demás participantes del mercado.
  - Es secuencial porque las decisiones del agente van a afectar directamente al ambiente y las decisiones futuras
  - Es dinámico porque el trading está en constante cambio mientras se analiza la decisión
  - Es continuo, las percepciones del agente respecto al trading son finitas el número de estados y significados es continuo
  - Es parcialmente conocido, porque el agente conoce las reglas para comprar y vender, pero no conoce completamente cómo se comportará el mercado.

- **A**: Comprar, vender, mantener posiciones, cancelar acciones y ajustar límites de compra o venta.
- **S**: Precio de las acciones respecto al tiempo, volumen de acciones de una empresa, historial de precios

### 6. Sistema de diagnóstico médico asistido por IA

- **P**: Recuperación del paciente, precisión del diagnóstico y tiempo para dar una recomendación.
- **E**: Clínica, consultorio, hospital laboratorio, paciente, doctor, enfermero, otras personas:
  - Es parcialmente observable porque el agente al principio no tiene contexto del paciente, tiene que pasar por varios procesos para obtener información
  - Es multiagente porque intervienen paciente, médico, enfermeros y otros especialistas y dispositivos/robots.
  - Estocástico, porque los mismos síntomas pueden venir de enfermedades distintas, y la misma enfermedad puede verse diferente entre pacientes.
  - Es secuencial porque el diagnóstico requiere de pasos secuenciales a seguir para recopilar información
  - Es dinámico, el paciente puede presentar nuevos síntomas mientras se piensa el siguiente paso
  - Mixto (?): hay datos discretos como categorías de enfermedades y otros continuos, como temperatura y otros datos numéricos.
  - Es parcialmente conocido porque el agente conoce reglas médicas generales, pero no conoce con certeza toda la condición real del paciente.

- **A**: Mostrar el resultado por voz o en texto, hacer preguntas, recomendar pasos a seguir, como estudios u otras cosas
- **S**: Escuchar los síntomas, respuestas a preguntas, historial médico, chequeos de signos del paciente, ver estudios como imágenes.

### 7. Dron de inspección de infraestructura

- **P**: Porcentaje del total del área cubierto, porcentaje de detección de errores
- **E**: Diferentes ambientes, lugares, climas, terrenos, materiales, maquinaria, otro tipo de estructuras y personas:
  - Es parcialmente observable, el dron solo puede ver superficialmente la estructura
  - Es principalmente de agente único, aunque puede volverse multiagente si hay personas, maquinaria u otros drones en la zona.
  - Es estocástico porque el clima, la iluminación, obstáculos o condiciones del lugar pueden cambiar y afectar la inspección.
  - Es secuencial porque la inspección sucede en partes secuenciales hasta cubrir la totalidad del área conocida
  - Es dinámico porque durante la inspección puede cambiar cosas que afectan al ambiente como la iluminación, la maquinaria o el movimiento de personas en la zona.
  - Es continuo porque trabajas con medidas y porcentajes
  - Es parcialmente conocido porque el agente puede dar una inspección general sin saber realmente real de la estructura

- **A**: Subir, bajar, dar vuelta, quedarse estático, tomar fotos, grabar video y enviar métricas.
- **S**: LiDAR/cámara, GPS, sensores de proximidad y altura

### 8. Agente jugador de ajedrez

- **P**: Movimientos mínimos para ganar, porcentajes de partidas ganadas/perdidas, ELO,
- **E**: Tablero, jugador contrario:
  - Es observable, al agente puede ver completo al tablero y lo que hace el adversario
  - Es multiagente porque juega contra un adversario que también toma decisiones.
  - Es determinista, porque si el agente hace una jugada desde un estado específico del tablero, el resultado siempre será el mismo.
  - Es secuencial pues es un juego de turnos
  - Es estático por lo mismo que es un juego de turnos, el ambiente no va a cambiar hasta que haga su turno (a menos que haya tiempo de por medio).
  - Es discreto, hay un número finito de estados posibles del tablero
  - Es conocido porque el agente sabe las reglas y puede ver lo que hace el adversario.

- **A**: Elegir una jugada legal, mover piezas, capturar piezas, hacer enroque y subir peones a otras piezas.
- **S**: Estado del tablero, posición de las piezas, última jugada del adversario y tiempo disponible.
