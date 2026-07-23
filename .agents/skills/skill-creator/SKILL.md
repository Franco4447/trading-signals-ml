---
name: skill-creator
description: Creación, formateo y validación de nuevas habilidades de agente con el estándar SKILL.md.
---

# Skill Creator Skill

Guía para estructurar y empaquetar nuevas habilidades de agente en `.agents/skills/`.

---

## 📋 Estructura Estándar
1. **Frontmatter YAML obligatorio:**
   ```yaml
   ---
   name: nombre-de-skill
   description: Descripción concisa de la habilidad y cuándo aplicarla.
   ---
   ```
2. **Encabezado principal Markdown:** `# Nombre Skill`
3. **Sección Teórica:** Enlaces a `docs/theory/` si aplica.
4. **Sección Práctica:** Ejemplos de código o comandos explicativos.
