import base64
import json
from typing import Optional
from pathlib import Path
from typing import Protocol
from datetime import datetime
import numpy as np
import cv2

class Subscriber(Protocol):
    def receive_binary(self) -> bytes:
        ...
    def send(self, message: dict) -> None:
        ...

class Image:
    def __init__(self, subscriber: Subscriber, topic: str = "/camera/image_raw"):
        self.subscriber = subscriber
        self.topic = topic

    def subscribe(self, save_path: Optional[str] = None) -> Optional[bytes]:
        try:
            subscribe_msg = {
                "op": "subscribe",
                "topic": self.topic,
                "type": "sensor_msgs/Image"
            }
            self.subscriber.send(subscribe_msg)

            raw = self.subscriber.receive_binary()
            if not raw:
                print("[Image] No data received from subscriber")
                return None

            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")

            msg = json.loads(raw)
            msg = msg["msg"]

            # Extract metadata
            height = msg["height"]
            width = msg["width"]
            encoding = msg["encoding"]
            data_b64 = msg["data"]

            # Decode base64 to raw bytes
            image_bytes = base64.b64decode(data_b64)
            img_np = np.frombuffer(image_bytes, dtype=np.uint8)

            # Handle encoding
            if encoding == "rgb8":
                img_np = img_np.reshape((height, width, 3))
                img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)  # convert to BGR for OpenCV
            elif encoding == "bgr8":
                img_cv = img_np.reshape((height, width, 3))
            elif encoding == "mono8":
                img_cv = img_np.reshape((height, width))
            else:
                print(f"[Image] Unsupported encoding: {encoding}")
                return None

            # Save image
            if save_path is None:
                downloads_dir = Path(__file__).resolve().parents[2] / "screenshots"
                if not downloads_dir.exists():
                    downloads_dir.mkdir(parents=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = downloads_dir / f"{timestamp}.png"

            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(save_path), img_cv)
            print(f"[Image] Saved to {save_path}")
            return img_cv

        except Exception as e:
            print(f"[Image] Failed to receive or decode: {e}")
            return None

    def subscribe_as_base64(self, max_size_kb: int = 800, quality: int = 85) -> Optional[dict]:
        """画像をBase64形式で取得（サイズ制限付き）"""
        import base64
        
        try:
            subscribe_msg = {
                "op": "subscribe",
                "topic": self.topic,
                "type": "sensor_msgs/Image"
            }
            self.subscriber.send(subscribe_msg)

            raw = self.subscriber.receive_binary()
            if not raw:
                print("[Image] No data received from subscriber")
                return None

            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")

            msg = json.loads(raw)
            msg = msg["msg"]

            # メタデータ抽出
            height = msg["height"]
            width = msg["width"]
            encoding = msg["encoding"]
            data_b64 = msg["data"]

            # Base64をデコードして画像データに変換
            image_bytes = base64.b64decode(data_b64)
            img_np = np.frombuffer(image_bytes, dtype=np.uint8)

            # エンコーディング処理
            if encoding == "rgb8":
                img_np = img_np.reshape((height, width, 3))
                img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            elif encoding == "bgr8":
                img_cv = img_np.reshape((height, width, 3))
            elif encoding == "mono8":
                img_cv = img_np.reshape((height, width))
            else:
                print(f"[Image] Unsupported encoding: {encoding}")
                return None

            # 画像を圧縮
            compressed_base64 = self._compress_image_to_base64(
                img_cv, max_size_kb, quality
            )
            
            # Unsubscribe
            unsubscribe_msg = {
                "op": "unsubscribe",
                "topic": self.topic
            }
            self.subscriber.send(unsubscribe_msg)
            
            return compressed_base64

        except Exception as e:
            print(f"[Image] Failed to receive or decode: {e}")
            return None

    def _compress_image_to_base64(self, img, max_size_kb: int, initial_quality: int) -> dict:
        """画像を指定サイズ以下に圧縮してBase64エンコード"""
        import base64
        
        original_height, original_width = img.shape[:2]
        
        # 段階的に圧縮を試みる
        widths = [original_width, 1280, 960, 640, 480, 320]
        qualities = [initial_quality, 70, 50, 30]
        
        for target_width in widths:
            if target_width > original_width:
                continue
                
            # リサイズ
            scale = target_width / original_width
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)
            
            if scale < 1:
                resized_img = cv2.resize(img, (new_width, new_height), 
                                        interpolation=cv2.INTER_AREA)
            else:
                resized_img = img
            
            for quality in qualities:
                # JPEG圧縮
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
                _, buffer = cv2.imencode('.jpg', resized_img, encode_param)
                img_base64 = base64.b64encode(buffer).decode('utf-8')
                
                # サイズチェック
                size_kb = len(img_base64) / 1024
                
                if size_kb <= max_size_kb:
                    return {
                        "image_base64": img_base64,
                        "mime_type": "image/jpeg",
                        "original_size": f"{original_width}x{original_height}",
                        "compressed_size": f"{new_width}x{new_height}",
                        "quality": quality,
                        "size_kb": round(size_kb, 2)
                    }
        
        # 最小サイズでも大きすぎる場合
        return None
