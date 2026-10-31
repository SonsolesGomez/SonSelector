# Son Selector Alumnos

Programa para clase: elige al azar a qué alumno dirigir una pregunta, con una animación rápida que se detiene en un nombre.

## Uso local (PC)

1. Haz doble clic en `iniciar.bat`.
2. Se abre el navegador (normalmente http://localhost:8501).

Sin secrets, los datos van a `data/grupos.json`.

## Google Sheets (móvil / nube)

Los **nombres de grupos y alumnos** se guardan en una hoja de Google. Así no se pierden al usar la app en el móvil.

### 1. Crear la hoja

1. Crea un [Google Sheet](https://sheets.google.com) vacío.
2. Copia el **ID** de la URL:  
   `https://docs.google.com/spreadsheets/d/`**`ESTE_ID`**`/edit`

La app creará sola las pestañas `grupos` y `alumnos` con estas columnas:

- `grupos`: `id`, `nombre`
- `alumnos`: `id`, `grupo_id`, `nombre`, `veces`

### 2. Cuenta de servicio (Google Cloud)

1. En [Google Cloud Console](https://console.cloud.google.com/) crea un proyecto (o usa uno).
2. Activa **Google Sheets API** y **Google Drive API**.
3. Crea una **cuenta de servicio** → descarga el JSON de clave.
4. Comparte tu hoja con el `client_email` del JSON (permiso **Editor**).

### 3. Secrets

Copia `.streamlit/secrets.toml.example` a `.streamlit/secrets.toml` y rellénalo:

- `sheets.spreadsheet_id` = ID de la hoja
- `[gcp_service_account]` = contenido del JSON (campo a campo; en `private_key` respeta los `\n`)

En **Streamlit Community Cloud**: App settings → Secrets → pega el mismo TOML.

### 4. Migrar listas que ya tenías en el PC

Con secrets configurados, en **Grupos y alumnos** → **Subir JSON local a Google Sheets**.

### 5. Desplegar para el móvil

1. Sube el proyecto a GitHub (sin `.streamlit/secrets.toml` ni `.venv`).
2. Entra en [share.streamlit.io](https://share.streamlit.io), conecta el repo y despliega `streamlit_app.py`.
3. Pega los secrets en la nube.
4. Abre la URL de la app en el navegador del móvil.

## Uso en clase

1. En **Grupos y alumnos**, crea grupos y añade nombres (o pega una lista).
2. En **Selector**, elige el grupo y **pulsa el cuadro** para seleccionar.
3. **No repetir últimos** (0–15): `0` = sin repetición en la sesión; `1–15` = evita los últimos N.
4. El registro de veces se guarda en la hoja (`veces`); puedes resetearlo por grupo.
