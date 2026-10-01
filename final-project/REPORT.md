# RAG sobre catálogos de agitadores Autmix — reporte

## Dominio y corpus

El corpus son 11 catálogos públicos de agitadores industriales de Autmix, uno
por serie (ancla, compactos, horizontales, rotor y verticales). En total
suman 33 páginas y 3,213 palabras. Al omitir las 11 portadas, quedan 22
páginas que producen **35 chunks**, incrustados con **`gemini-embedding-001`**
de Google AI (3,072 dimensiones).

Los catálogos son fichas técnicas con una misma plantilla: los mismos
encabezados (diámetro de hélice, materiales, motor, reductor…) con valores
distintos. Eso los vuelve difíciles de distinguir para un modelo de
embeddings, y condicionó casi todo el diseño.

## Particionado

Todos los catálogos tienen la misma estructura: una portada con solo el
título (11–16 palabras), una página de especificaciones (127–198 palabras) y
una de opciones (110–130 palabras) que termina en un bloque de contacto
idéntico.

- **Se omiten las portadas** (menos de 20 palabras). Un chunk con solo el
  título se parece un poco a casi cualquier pregunta y desplaza evidencia
  real del top-k.
- **Se elimina el pie de contacto.** Aparecía palabra por palabra en los 11
  catálogos y hacía que sus últimas páginas se parecieran entre sí.
- **Ventanas de 100 palabras con 25 de solape.** El curso sugiere 200–400
  palabras, pero con ese tamaño cada página sería un solo chunk y el
  particionado nunca dividiría nada. Con 100 palabras, las páginas de
  especificaciones se dividen en 2–3 chunks, cada uno centrado en pocas
  especificaciones, y el solape de 25 palabras mantiene completos los datos
  cortos cercanos a un corte (p. ej. *MOTOR 230 - 460 V Trifásico*) en al
  menos un chunk.
- **Se antepone el nombre del modelo a cada chunk antes de incrustarlo**
  (*Agitadores Verticales RT-RTG. …*). Sin él, las listas de materiales de
  distintos modelos son casi idénticas. Con él, una pregunta sobre el RT-RTG
  devolvió solo chunks del RT-RTG en el top 3, entre 11 catálogos parecidos.

La extracción de texto separa algunas palabras (*DIÁ METRO*). Se dejaron así,
porque una heurística para unirlas también uniría palabras que sí van
separadas; el prompt le indica al modelo cómo leerlas.

## Abstención

El sistema se abstiene en dos capas, más una verificación de seguridad:

1. **Umbral de recuperación.** Si el mejor chunk tiene un score menor a
   **0.65**, no se llama a Gemini.
2. **Gemini.** El prompt exige responder solo con los pasajes numerados y
   contestar con una frase fija cuando no contienen la respuesta.
3. **Sin cita no hay respuesta.** Se descarta una respuesta que no cite un
   `[n]` válido.

El umbral se fijó a partir de scores medidos, y las mediciones muestran por
qué una sola capa no basta:

| Pregunta | Mejor score | Resultado | Decide |
|---|---|---|---|
| Materiales del RT-RTG | 0.796 | responde | — |
| Diámetro de hélice RT-RTG vs RT-RTN | 0.777 | responde | — |
| Características de los agitadores ancla | 0.775 | responde | — |
| Potencia de los agitadores compactos | 0.755 | responde | — |
| Precio del RT-RTG | 0.764 | se abstiene | Gemini |
| Recomendación para un proceso de yogur | 0.715 | se abstiene | Gemini |
| Garantía de Autmix | 0.643 | se abstiene | umbral |
| ¿Quién ganó el mundial de 2022? | 0.535 | se abstiene | umbral |

Las preguntas fuera de dominio quedan muy por debajo del umbral, pero la del
precio obtiene un score **mayor que una pregunta real** (0.764 frente a
0.755): menciona un modelo real, así que sus chunks se parecen aunque ninguno
contenga un precio. Ningún umbral separa ambos casos, por eso la segunda capa
es necesaria. Las 8 preguntas se comportan correctamente.

Un ajuste pesó más de lo esperado. Con el razonamiento (*thinking*) de Gemini
desactivado, el modelo se abstenía en preguntas amplias pero respondibles
(*características de los agitadores ancla*, *potencia de los compactos*) y
acertaba 6 de 8. Con un presupuesto de razonamiento de 1,024 tokens acertó
8 de 8.

## Qué hace Google AI y qué hace Chroma

- **Google AI, embeddings:** convierte cada chunk (`RETRIEVAL_DOCUMENT`) y
  cada pregunta (`RETRIEVAL_QUERY`) en un vector, con el mismo modelo.
- **Google AI, generación:** `gemini-3.5-flash` redacta la respuesta en
  español solo con los chunks recuperados, citándolos como `[n]`.
- **Chroma:** guarda en disco los chunks, sus vectores y sus metadatos
  (archivo, página, modelo), y devuelve los `top_k` chunks más cercanos por
  distancia coseno. Nunca calcula embeddings: su embedder por defecto está
  desactivado.

## Limitaciones

- **Las preguntas sobre todo el catálogo** (*¿qué agitadores maneja Autmix?*)
  reciben una respuesta parcial: el top-k devuelve 3 chunks, no uno por
  catálogo.
- **Las recomendaciones de aplicación no están en el texto.** Los catálogos
  muestran las industrias como íconos, así que *¿qué agitador para yogur?* se
  abstiene, correctamente.
- **Los cortes entre chunks pueden partir listas.** La lista de materiales del
  NC-NCS ocupa dos chunks, y una respuesta que solo recuperó el segundo omitió
  304 y 316L.
- **Los ids de los chunks vienen del nombre del archivo**, así que el mismo
  PDF subido con otro nombre se indexa dos veces.
