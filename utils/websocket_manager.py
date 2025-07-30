import socket
import json
import websocket._core as websocket
import base64

class WebSocketManager:
    def __init__(self, ip: str, port: int, local_ip: str):
        self.ip = ip
        self.port = port
        self.local_ip = local_ip
        self.ws = None

    def connect(self):
        if self.ws is None or not self.ws.connected:
            try:
                # Use websocket.create_connection instead of manual socket management
                url = f"ws://{self.ip}:{self.port}"
                self.ws = websocket.create_connection(url)
                print("[WebSocket] Connected")
            except Exception as e:
                print(f"[WebSocket] Connection error: {e}")
                self.ws = None

    def send(self, message: dict):
        self.connect()
        if self.ws:
            try:
                # Ensure message is JSON serializable
                json_msg = json.dumps(message)
                self.ws.send(json_msg)
            except TypeError as e:
                print(f"[WebSocket] JSON serialization error: {e}")
                self.close()
            except Exception as e:
                print(f"[WebSocket] Send error: {e}")
                self.close()


    def receive_binary(self) -> bytes:
        self.connect()
        if self.ws:
            try:
                raw = self.ws.recv()  # raw is JSON string (type: str)
                return raw
            except Exception as e:
                print(f"Receive error: {e}")
                self.close()
        return b""
    
    def get_topics(self) -> list[tuple[str, str]]:
        self.connect()
        if self.ws:
            try:
                self.send({
                    "op": "call_service",
                    "service": "/rosapi/topics",
                    "id": "get_topics_request_1"
                })
                response = self.receive_binary()
                print(f"[WebSocket] Received response: {response}")
                if response:
                    data = json.loads(response)
                    if "values" in data:
                        topics = data["values"].get("topics", [])
                        types = data["values"].get("types", [])
                        if topics and types and len(topics) == len(types):
                            return list(zip(topics, types))
                        else:
                            print("[WebSocket] Mismatch in topics and types length")
            except json.JSONDecodeError as e:
                print(f"[WebSocket] JSON decode error: {e}")
            except Exception as e:
                print(f"[WebSocket] Error: {e}")
        return []

    def close(self):
        if self.ws and self.ws.connected:
            try:
                self.ws.close()
                print("[WebSocket] Closed")
            except Exception as e:
                print(f"[WebSocket] Close error: {e}")
            finally:
                self.ws = None

    # utils/websocket_manager.py に追加
    def receive_with_timeout(self, timeout=2.0):
        """タイムアウト付きでメッセージを受信"""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                self.ws.settimeout(0.1)  # 100msのタイムアウト
                raw = self.ws.recv()
                if raw:
                    return raw
            except websocket._exceptions.WebSocketTimeoutException:
                continue
            except Exception as e:
                print(f"[WebSocket] Receive error: {e}")
                return None
        
        return None

    def subscribe_once(self, topic, timeout=2.0):
        """トピックを一度だけ購読してメッセージを取得"""
        self.connect()
        if not self.ws:
            return None
        
        # IDを生成（一意性のため）
        import uuid
        sub_id = str(uuid.uuid4())
        
        try:
            # Subscribe
            self.send({
                "op": "subscribe",
                "id": sub_id,
                "topic": topic
            })
            
            # メッセージを待つ
            raw = self.receive_with_timeout(timeout)
            
            # Unsubscribe
            self.send({
                "op": "unsubscribe",
                "id": sub_id,
                "topic": topic
            })
            
            if raw:
                return json.loads(raw)
            
        except Exception as e:
            print(f"[WebSocket] Subscribe error: {e}")
        
        return None