# Guía Asistencial Paso a Paso para la Interfaz Web de GitHub.com

Este documento es el **manual interactivo de asistencia** que utilizaremos para realizar la **Parte 2** del Plan SDD de Configuración de GitHub. En pantalla y en vivo, configuraremos las reglas de protección de ramas y los entornos nativos en tu cuenta de GitHub.com para activar el blindaje de seguridad.

---

## 🧭 Checklist de Configuración Web (Asistido por el Agente)

### 1️⃣ Paso 1: Proteger la Rama `main` (Producción Live)
La rama `main` es sagrada: solo albergará código evaluado y rentable en QA para operar con dinero real en el VPS 2.

*   [ ] Abre tu navegador y ve a: [https://github.com/Franco4447/trading-signals-ml/settings/branches](https://github.com/Franco4447/trading-signals-ml/settings/branches)
*   [ ] Haz clic en el botón **Add branch protection rule** (o **Add rule**).
*   [ ] En el campo **Branch name pattern**, escribe exactamente: `main`
*   [ ] Activa la casilla ☑️ **Require a pull request before merging**.
*   [ ] Activa la casilla ☑️ **Require status checks to pass before merging**.
    *   En la barra de búsqueda de *status checks*, busca y selecciona: `test-and-validate` (de nuestro pipeline de CI cuantitativo).
    *   Busca y selecciona: `docker-validation` (de nuestro compilador Docker).
*   [ ] Activa la casilla ☑️ **Do not allow bypass the above settings** (ni siquiera los administradores podrán saltarse las pruebas de seguridad).
*   [ ] Haz clic en **Create** (o **Save changes**).

---

### 2️⃣ Paso 2: Proteger la Rama `qa` (Staging Forward Test)
La rama `qa` es donde se realizarán los días de prueba empírica en tiempo real con Paper Trading y Telegram.

*   [ ] En la misma página (*Settings > Branches*), haz clic en **Add branch protection rule** nuevamente.
*   [ ] En el campo **Branch name pattern**, escribe: `qa`
*   [ ] Activa ☑️ **Require status checks to pass before merging** y selecciona los mismos dos checks: `test-and-validate` y `docker-validation`.
*   [ ] Haz clic en **Create** (o **Save changes**).

---

### 3️⃣ Paso 3: Configurar los Entornos y el candado "Required Reviewers"
El entorno `production` tendrá un candado manual: impedirá físicamente que un bot o script lance un pase a producción si tú no haces clic en *"Approve"*.

*   [ ] En el menú izquierdo de Settings, haz clic en **Environments** (o ve a [https://github.com/Franco4447/trading-signals-ml/settings/environments](https://github.com/Franco4447/trading-signals-ml/settings/environments)).
*   [ ] Haz clic en **New environment**, escribe `development` y guarda.
*   [ ] Haz clic en **New environment**, escribe `qa` y guarda.
    *   *(Opcional)*: En `qa`, puedes hacer clic en **Add secret** para agregar variables como `TELEGRAM_BOT_TOKEN_QA`.
*   [ ] Haz clic en **New environment**, escribe `production` y guarda.
    *   [ ] Dentro de la configuración de `production`, activa la casilla ☑️ **Required reviewers**.
    *   [ ] Busca tu nombre de usuario en GitHub (`Franco4447`) y selecciónalo.
    *   [ ] Haz clic en **Save protection rules**.

---

### 4️⃣ Paso 4: Simulacro y Validación con un Pull Request de Prueba
Para comprobar que toda esta automatización funciona en vivo y en la nube:

1.  Abriremos un Pull Request de prueba en la pestaña **Pull requests** desde la rama `dev` hacia `qa`.
2.  Verificaremos visualmente en la pestaña **Actions** cómo los servidores virtuales de GitHub levantan los contenedores, ejecutan el *Gatekeeper* cuantitativo y auditan el código automáticamente.
3.  Comprobaremos que aparezca el escudo verde autorizando la fusión sin romper la invariante antifuga ni las matemáticas financieras.
