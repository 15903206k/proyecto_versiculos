# Diccionario bíblico para el chatbot

Estructura esperada en `diccionario_biblico.json`:

- Cada **tema** es una clave (ej: `amor`).
- Debe contener:
  - `keywords`: lista de palabras/variantes para detectar el tema en el mensaje.
  - `versiculos`: lista de objetos `{ "texto": "...", "cita": "Libro X:Y" }`.

Ejemplo:
```json
{
  "amor": {
    "keywords": ["amor", "amar", "caridad"],
    "versiculos": [
      {"texto": "...", "cita": "1 Juan 4:8"}
    ]
  }
}
```

## Cómo añadir más temas
1) Abre el JSON.
2) Agrega una nueva clave con `keywords` y `versiculos`.
3) Recarga la app.

