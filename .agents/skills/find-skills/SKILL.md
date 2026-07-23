---
name: find-skills
description: Ayuda a los usuarios y agentes a descubrir e instalar habilidades de agente desde el repositorio vercel-labs/skills y el ecosistema skills.sh cuando se requieran capacidades extendidas.
---

# Find Skills

Esta habilidad permite descubrir e instalar habilidades operativas utilizando el gestor de paquetes de habilidades del ecosistema abierto (`npx skills`) mantenido por Vercel Labs.

---

## 🛠️ ¿Qué es el CLI de Skills (`npx skills`)?

El CLI `npx skills` es el gestor de paquetes para habilidades de agentes. Permite buscar, instalar y mantener actualizadas las habilidades provenientes del repositorio de GitHub [vercel-labs/skills](https://github.com/vercel-labs/skills) y del directorio público [skills.sh](https://skills.sh/).

### Comandos Clave:

- **Buscar habilidades:**
  ```bash
  npx skills find [búsqueda] [--owner <owner>]
  ```
- **Instalar una habilidad:**
  ```bash
  npx skills add <paquete>
  ```
- **Verificar actualizaciones:**
  ```bash
  npx skills check
  ```
- **Actualizar todas las habilidades instaladas:**
  ```bash
  npx skills update
  ```

---

## 🔍 Flujo para Buscar e Instalar Skills

1. **Identificar la necesidad:** Identificar si la tarea del usuario (ej. documentación, scraping, testing, optimización) puede beneficiarse de una skill existente en la comunidad.
2. **Buscar en el ecosistema:** Ejecutar `npx skills find <término>` o explorar `https://skills.sh/`.
3. **Verificar Calidad:**
   - Preferir repositorios oficiales (`vercel-labs`, `anthropics`, `microsoft`).
   - Priorizar habilidades con alto número de instalaciones ($>1,000$).
4. **Instalar en el proyecto:** Ejecutar `npx skills add <autor/repo@habilidad>` para integrar la skill en la carpeta `.agents/skills/` del repositorio.
