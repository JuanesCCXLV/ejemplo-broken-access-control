"""
Demo OWASP A01 - Broken Access Control (orders-service)

Uso:
    MODE=vulnerable python app.py   # versión con fallas (mi parte: Ejemplificar)
    MODE=secure     python app.py   # versión corregida (para la parte de soluciones)

SOLO PARA FINES EDUCATIVOS: datos en memoria, contraseñas en texto plano y
secreto JWT fijo. No usar nada de esto en producción.
"""
import os
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import Flask, g, jsonify, request

MODE = os.getenv("MODE", "vulnerable").lower()
SECRET = "demo-secret-no-usar-en-produccion"

app = Flask(__name__)

# ----------------------------------------------------------------------------
# "Base de datos" en memoria
# ----------------------------------------------------------------------------
USERS = {
    1:   {"id": 1,   "username": "admin", "password": "admin123", "role": "ADMIN", "email": "admin@demo.com"},
    101: {"id": 101, "username": "ana",   "password": "ana123",   "role": "USER",  "email": "ana@demo.com"},
    102: {"id": 102, "username": "beto",  "password": "beto123",  "role": "USER",  "email": "beto@demo.com"},
}

ORDERS = {
    5001: {"id": 5001, "owner_id": 101, "items": ["Teclado mecánico"],
           "address": "Calle 5 #10-20, Cali", "card": "**** 1111"},
    5002: {"id": 5002, "owner_id": 102, "items": ["Monitor 27\""],
           "address": "Carrera 100 #15-30, Cali", "card": "**** 2222"},
    5003: {"id": 5003, "owner_id": 102, "items": ["Mouse", "Webcam"],
           "address": "Carrera 100 #15-30, Cali", "card": "**** 2222"},
}


# ----------------------------------------------------------------------------
# Autenticación (esto SÍ está bien implementado en ambos modos)
# ----------------------------------------------------------------------------
def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify(error="Token requerido"), 401
        try:
            claims = jwt.decode(header[7:], SECRET, algorithms=["HS256"])
        except jwt.InvalidTokenError:
            return jsonify(error="Token inválido o expirado"), 401
        g.user_id = int(claims["sub"])
        g.role = USERS[g.user_id]["role"]  # rol actual, leído de la "BD"
        return f(*args, **kwargs)
    return wrapper


@app.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    for user in USERS.values():
        if user["username"] == data.get("username") and user["password"] == data.get("password"):
            token = jwt.encode(
                {"sub": str(user["id"]),
                 "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
                SECRET, algorithm="HS256",
            )
            return jsonify(token=token, user_id=user["id"])
    return jsonify(error="Credenciales incorrectas"), 401


# ----------------------------------------------------------------------------
# FALLA 1: IDOR / BOLA (acceso a objetos de otros usuarios)
# ----------------------------------------------------------------------------
@app.get("/api/orders/<int:order_id>")
@token_required
def get_order(order_id):
    order = ORDERS.get(order_id)
    if order is None:
        return jsonify(error="Pedido no encontrado"), 404

    # FIX (solo en modo seguro): verificar que el pedido pertenece al usuario
    if MODE == "secure":
        if order["owner_id"] != g.user_id and g.role != "ADMIN":
            return jsonify(error="No tienes permiso para ver este pedido"), 403

    return jsonify(order)


# ----------------------------------------------------------------------------
# FALLA 2: falta de control de acceso a nivel de función
# ----------------------------------------------------------------------------
def admin_required():
    """Devuelve una respuesta 403 si el usuario no es ADMIN (solo modo seguro)."""
    if MODE == "secure" and g.role != "ADMIN":
        return jsonify(error="Se requiere rol ADMIN"), 403
    return None


@app.put("/api/admin/users/<int:user_id>/role")
@token_required
def change_role(user_id):
    denied = admin_required()
    if denied:
        return denied

    user = USERS.get(user_id)
    if user is None:
        return jsonify(error="Usuario no encontrado"), 404
    new_role = (request.get_json(silent=True) or {}).get("role")
    if new_role not in ("USER", "ADMIN"):
        return jsonify(error="Rol inválido"), 400
    user["role"] = new_role
    return jsonify(id=user["id"], username=user["username"], role=user["role"])


@app.get("/api/admin/users")
@token_required
def list_users():
    denied = admin_required()
    if denied:
        return denied
    return jsonify([{k: v for k, v in u.items() if k != "password"} for u in USERS.values()])


if __name__ == "__main__":
    print(f"\n>>> orders-service corriendo en modo: {MODE.upper()}\n")
    app.run(port=8000)
