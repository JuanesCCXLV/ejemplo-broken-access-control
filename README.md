# Demo: Broken Access Control (OWASP A01)

## Instalación

```bash
python -m venv venv
source venv/bin/activate        
pip install flask pyjwt requests
```

## Ejecución

Terminal 1 (servicio vulnerable):
```bash
MODE=vulnerable python app.py   
```

Terminal 2 (ataque):
```bash
python attack.py
```

Para mostrar la versión corregida, reinicia el servicio con `MODE=secure`
y vuelve a correr `python attack.py`: los pasos 2, 3, 4 y 5 deben devolver 403.

## Qué muestra cada paso

| Paso | Qué pasa en modo vulnerable | Qué pasa en modo seguro |
|------|-----------------------------|-------------------------|
| 1 | Ana ve su pedido (legítimo) | Igual |
| 2 | Ana ve el pedido de Beto (IDOR) | 403 |
| 3 | Ana recorre pedidos ajenos por enumeración | 403 en los ajenos |
| 4 | Ana se convierte en ADMIN | 403 |
| 5 | Ana lista todos los usuarios | 403 |

