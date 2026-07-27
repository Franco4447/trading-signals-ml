"""
MLOps Environment Validator Script.
Audits required environment variables for Dev, QA, and Production profiles
without printing sensitive API secrets to console logs.
"""
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

import argparse
import os
from pathlib import Path
from typing import Dict, List, Tuple


REQUIRED_KEYS = [
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "EXCHANGE_API_KEY",
    "EXCHANGE_API_SECRET",
    "EXCHANGE_TESTNET",
    "HARD_MAX_LEVERAGE",
    "DAILY_LOSS_LIMIT_PCT",
    "MAX_DRAWDOWN_LIMIT_PCT",
]


def _mask_secret(val: str) -> str:
    if not val or val == "None" or len(val) < 8:
        return "********"
    return f"{val[:4]}...{val[-4:]}"


def parse_env_file(filepath: Path) -> Dict[str, str]:
    env_vars = {}
    if not filepath.exists():
        return env_vars

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            env_vars[key] = val
    return env_vars


def validate_environment(env_path: str) -> bool:
    path_obj = Path(env_path)
    print(f"\n============================================================")
    print(f" 🔍 AUDITORÍA DE ENTORNO MLOPS: '{env_path}'")
    print(f"============================================================")

    if not path_obj.exists():
        print(f" ⚠️ ADVERTENCIA: No se encontró el archivo '{env_path}'. Se auditarán variables del sistema (os.environ).")
        env_map = {k: os.environ.get(k, "") for k in REQUIRED_KEYS}
    else:
        env_map = parse_env_file(path_obj)

    missing_keys: List[str] = []
    print(f" 📋 Estado de parámetros clave:")
    for key in REQUIRED_KEYS:
        val = env_map.get(key, os.environ.get(key, ""))
        if not val:
            missing_keys.append(key)
            print(f"   ❌ {key:<26}: [FALTA / NO CONFIGURADA]")
        else:
            if "SECRET" in key or "TOKEN" in key or "KEY" in key:
                display_val = _mask_secret(val)
            else:
                display_val = val
            print(f"   ✅ {key:<26}: {display_val}")

    # Security check for Testnet flag
    is_testnet = str(env_map.get("EXCHANGE_TESTNET", os.environ.get("EXCHANGE_TESTNET", ""))).lower() in ("true", "1", "yes")
    if "prod" in env_path.lower():
        if is_testnet:
            print(f"\n ⚠️ ALERTA DE SEGURIDAD EN PROD: EXCHANGE_TESTNET está habilitado (true) en un archivo de producción.")
        else:
            print(f"\n 🛡️ BLINDAJE PROD VERIFICADO: Modo LIVE activo (EXCHANGE_TESTNET=false).")
    elif "qa" in env_path.lower() or "dev" in env_path.lower():
        if not is_testnet:
            print(f"\n ⚠️ ALERTA EN STAGING: EXCHANGE_TESTNET está en false en un perfil de desarrollo/QA.")
        else:
            print(f"\n 🧪 STAGING VERIFICADO: Modo Testnet/Paper Trading seguro (EXCHANGE_TESTNET=true).")

    print(f"============================================================")
    if missing_keys:
        print(f" ❌ AUDITORÍA FALLIDA: Faltan {len(missing_keys)} variables obligatorias.")
        return False
    else:
        print(f" 🟢 AUDITORÍA COMPLETADA EXITOSAMENTE: Entorno 100% íntegro.")
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate trading signals environment credentials.")
    parser.add_argument("--env", "-e", default=".env.example", help="Path to .env file to audit")
    args = parser.parse_args()

    success = validate_environment(args.env)
    if not success and args.env != ".env.example":
        exit(1)
