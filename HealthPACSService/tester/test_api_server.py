# tester/test_api_server.py

import sys
import json
import asyncio
import requests
import websockets
from pathlib import Path

# Path root del progetto
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from library.logger import logger


def test_rest_api(base_url: str, token: str):
    """Testa le rotte REST sul server HealthPACS attivo."""
    logger.info("=== INIZIO TEST REST API ===")

    headers = {"Authorization": f"Bearer {token}"}

    # 1. Health check base
    res = requests.get(f"{base_url}/")
    logger.info(f"REST Health Check [{res.status_code}]: {res.json()}")

    # 2. GET /api/v1/studies/1
    res = requests.get(f"{base_url}/api/v1/studies/1", headers=headers)
    logger.info(f"REST Get Study ID 1 [{res.status_code}]: {res.json()}")

    # 3. Test senza token (Atteso HTTP 401)
    res_no_auth = requests.get(f"{base_url}/api/v1/studies/1")
    logger.info(f"REST Senza Token [{res_no_auth.status_code}]: {res_no_auth.json()}")


async def test_websocket_api(ws_url: str, token: str):
    """Testa le chiamate WebSocket sul server HealthPACS attivo."""
    logger.info("=== INIZIO TEST WEBSOCKET API ===")

    async with websockets.connect(ws_url) as ws:
        # 1. Test Azione GET_BY_ID
        payload = {
            "token": token,
            "action": "GET_BY_ID",
            "params": {"study_id": 1}
        }
        await ws.send(json.dumps(payload))
        response = await ws.recv()
        logger.info(f"WS Risposta GET_BY_ID: {response}")

        # 2. Test Azione Errata
        bad_payload = {
            "token": token,
            "action": "ACTION_ERRATA",
            "params": {}
        }
        await ws.send(json.dumps(bad_payload))
        bad_response = await ws.recv()
        logger.info(f"WS Risposta Azione Errata: {bad_response}")


def run_tests():
    dummy_token = "test_session_token_123"
    base_http_url = "http://127.0.0.1:8000"
    base_ws_url = "ws://127.0.0.1:8000/ws/studies"

    try:
        test_rest_api(base_http_url, dummy_token)
        asyncio.run(test_websocket_api(base_ws_url, dummy_token))
        logger.info("=== TUTTI I TEST COMPLETATI CON SUCCESSO ===")

    except requests.exceptions.ConnectionError:
        logger.error("Impossibile connettersi. Assicurati che 'python HealthPACS.py' sia avviato nell'altro terminale!")
    except Exception as e:
        logger.error(f"Errore durante l'esecuzione dei test: {e}")


if __name__ == "__main__":
    run_tests()