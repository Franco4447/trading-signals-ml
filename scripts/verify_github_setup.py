#!/usr/bin/env python3
"""
Auditor y Diagnóstico del Ecosistema GitHub (verify_github_setup.py)
====================================================================
Verifica el estado de las ramas locales y remotas (main, dev, qa), la
existencia de los flujos de trabajo en .github/workflows y la integración
de la skill github-deploy-monitor.

Uso:
    python scripts/verify_github_setup.py
"""
import os
import subprocess
import sys
from pathlib import Path

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def run_git_cmd(args):
    try:
        res = subprocess.run(
            ["git"] + args,
            capture_output=True, text=True, check=False, encoding="utf-8", errors="replace"
        )
        return res.stdout.strip(), res.returncode
    except Exception as e:
        return str(e), 1


def check_branches():
    print("\n[1/3] 🌿 Auditando estructura de ramas Git (local y remoto)...")
    branches_out, code = run_git_cmd(["branch", "-a"])
    if code != 0:
        print(f"  ❌ ERROR al consultar git: {branches_out}")
        return False

    lines = [l.strip() for l in branches_out.splitlines()]
    required = ["main", "dev", "qa"]
    all_ok = True
    for b in required:
        has_local = b in lines or f"* {b}" in lines or f"*{b}" in lines
        has_remote = f"remotes/origin/{b}" in lines or f"origin/{b}" in lines
        
        status_local = "✅ Local" if has_local else "❌ Local ausente"
        status_remote = "✅ Remoto (origin)" if has_remote else "❌ Remoto ausente"
        
        print(f"  • Rama [{b:<4}]: {status_local:<18} | {status_remote}")
        if not (has_local and has_remote):
            all_ok = False

    return all_ok


def check_workflows():
    print("\n[2/3] 🤖 Verificando flujos CI/CD (.github/workflows/)...")
    wf_dir = Path(".github/workflows")
    if not wf_dir.exists():
        print("  ❌ ERROR: Directorio .github/workflows/ no existe.")
        return False

    required_wfs = ["ci-gatekeeper.yml", "docker-build.yml"]
    all_ok = True
    for wf in required_wfs:
        wf_path = wf_dir / wf
        if wf_path.exists():
            print(f"  ✅ Workflow encontrando: {wf} ({wf_path.stat().st_size} bytes)")
        else:
            print(f"  ❌ Workflow ausente: {wf}")
            all_ok = False

    return all_ok


def check_skill_integration():
    print("\n[3/3] 🧠 Comprobando integración de la skill 'github-deploy-monitor'...")
    skill_path = Path(".agents/skills/github-deploy-monitor/SKILL.md")
    script_path = Path(".agents/skills/github-deploy-monitor/scripts/monitor_deploy_health.py")
    
    if skill_path.exists() and script_path.exists():
        print(f"  ✅ Skill SKILL.md presente ({skill_path.stat().st_size} bytes).")
        print(f"  ✅ Script operativo monitor_deploy_health.py presente.")
        return True
    else:
        print(f"  ❌ ERROR: Faltan componentes en .agents/skills/github-deploy-monitor/")
        return False


def main():
    print("="*70)
    print("🔍 AUDITOR DE INFRAESTRUCTURA GITHUB - TRADING SIGNALS ML")
    print("="*70)

    b_ok = check_branches()
    w_ok = check_workflows()
    s_ok = check_skill_integration()

    print("\n" + "="*70)
    if b_ok and w_ok and s_ok:
        print("🏆 VERIFICACIÓN COMPLETADA: La infraestructura de GitHub está 100% lista.")
        print("   Las ramas, workflows y la skill operativa se encuentran sincronizados.")
        print("="*70)
        sys.exit(0)
    else:
        print("❌ VERIFICACIÓN FALLIDA: Se detectaron inconsistencias en ramas o flujos.")
        print("="*70)
        sys.exit(1)


if __name__ == "__main__":
    main()
