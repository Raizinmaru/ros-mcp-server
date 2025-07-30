from mcp.server.fastmcp import FastMCP
from typing import List, Any, Optional
from pathlib import Path
import json
from utils.websocket_manager import WebSocketManager
from msgs.geometry_msgs import Twist
from msgs.sensor_msgs import Image, JointState

import base64
from io import BytesIO
import cv2

LOCAL_IP = "127.0.0.1"  # Replace with your local IP address
ROSBRIDGE_IP = "127.0.0.1"  # Replace with your rosbridge server IP address
ROSBRIDGE_PORT = 9090

mcp = FastMCP("ros-mcp-server")
ws_manager = WebSocketManager(ROSBRIDGE_IP, ROSBRIDGE_PORT, LOCAL_IP)

#twist = Twist(ws_manager, topic="/cmd_vel")
#image = Image(ws_manager, topic="/camera/image_raw")
#jointstate = JointState(ws_manager, topic="/joint_states")

twist = Twist(ws_manager, topic="/kachaka/manual_control/cmd_vel")
front_camera = Image(ws_manager, topic="/kachaka/front_camera/image_raw")
back_camera = Image(ws_manager, topic="/kachaka/back_camera/image_raw")
jointstate = JointState(ws_manager, topic="/kachaka/joint_states")

@mcp.tool()
def get_topics():
    topic_info = ws_manager.get_topics()
    ws_manager.close()

    if topic_info:
        topics, types = zip(*topic_info)
        return {
            "topics": list(topics),
            "types": list(types)
        }
    else:
        return "No topics found"

@mcp.tool()
def pub_twist(linear: List[Any], angular: List[Any]):
    msg = twist.publish(linear, angular)
    ws_manager.close()
    
    if msg is not None:
        return "Twist message published successfully"
    else:
        return "No message published"

@mcp.tool()
def pub_twist_seq(linear: List[Any], angular: List[Any], duration: List[Any]):
    twist.publish_sequence(linear, angular, duration)
    ws_manager.close()
    return "Twist sequence message published successfully"

@mcp.tool()
def sub_front_camera():
    """Kachakaのフロントカメラ画像を取得"""
    msg = front_camera.subscribe()
    ws_manager.close()
    
    if msg is not None:
        return "フロントカメラ画像を正常に取得・保存しました"
    else:
        return "カメラ画像の取得に失敗しました"

@mcp.tool()
def sub_back_camera():
    """Kachakaのバックカメラ画像を取得"""
    msg = back_camera.subscribe()
    ws_manager.close()
    
    if msg is not None:
        return "バックカメラ画像を正常に取得・保存しました"
    else:
        return "カメラ画像の取得に失敗しました"

'''
@mcp.tool()
def get_locations():
    """Kachakaの登録場所リストを取得"""
    data = ws_manager.subscribe_once("/kachaka/layout/locations/list", timeout=3.0)
    ws_manager.close()
    
    if data and "msg" in data:
        locations = data["msg"]["locations"]
        return {
            "locations": [
                {
                    "id": loc["id"],
                    "name": loc["name"],
                    "pose": loc["pose"]
                } for loc in locations
            ]
        }
    return "場所リストの取得に失敗しました"

@mcp.tool()
def get_battery_state():
    """Kachakaのバッテリー状態を取得"""
    data = ws_manager.subscribe_once("/kachaka/robot_info/battery_state", timeout=3.0)
    ws_manager.close()
    
    if data and "msg" in data:
        return {
            "battery_percentage": data["msg"].get("percentage", "不明"),
            "charging": data["msg"].get("charging", False)
        }
    return "バッテリー状態の取得に失敗しました"

@mcp.tool()
def move_to_location(x: float, y: float, theta: float):
    """Kachakaを指定座標に移動"""
    msg = {
        "op": "publish",
        "topic": "/kachaka/goal_pose",
        "msg": {
            "header": {
                "frame_id": "map"
            },
            "pose": {
                "position": {
                    "x": x,
                    "y": y,
                    "z": 0.0
                },
                "orientation": {
                    "x": 0.0,
                    "y": 0.0,
                    "z": 0.0,
                    "w": 1.0
                }
            }
        }
    }
    ws_manager.connect()
    ws_manager.send(msg)
    ws_manager.close()
    return f"座標 ({x}, {y}) への移動コマンドを送信しました"
'''

@mcp.tool()
def get_camera_image_base64(camera_type: str = "front", max_size_kb: int = 700):
    """カメラ画像をBase64形式で取得（Claude Desktopで表示可能）
    
    Args:
        camera_type: "front" または "back"
        max_size_kb: 最大サイズ（KB）。デフォルトは700KB
    """
    camera = front_camera if camera_type == "front" else back_camera
    
    # Base64形式で画像を取得
    result = camera.subscribe_as_base64(max_size_kb=max_size_kb)
    ws_manager.close()
    
    if result:
        return {
            "status": "success",
            "camera": camera_type,
            **result  # image_base64, mime_type, sizes, etc.
        }
    else:
        return {
            "status": "error", 
            "message": "画像取得または圧縮に失敗しました"
        }

@mcp.tool()
def get_both_cameras_base64(max_size_kb: int = 400):
    """前後両方のカメラ画像を取得
    
    Args:
        max_size_kb: 各画像の最大サイズ（KB）
    """
    results = {}
    
    # フロントカメラ
    front_result = front_camera.subscribe_as_base64(max_size_kb=max_size_kb)
    if front_result:
        results["front"] = front_result
    
    # バックカメラ
    back_result = back_camera.subscribe_as_base64(max_size_kb=max_size_kb)
    if back_result:
        results["back"] = back_result
    
    ws_manager.close()
    
    if results:
        return {
            "status": "success",
            "cameras": results
        }
    else:
        return {
            "status": "error",
            "message": "カメラ画像の取得に失敗しました"
        }

'''
@mcp.tool()
def sub_image():
    msg = image.subscribe()
    ws_manager.close()
    
    if msg is not None:
        return "Image data received and downloaded successfully"
    else:
        return "No image data received"

@mcp.tool()
def pub_jointstate(name: list[str], position: list[float], velocity: list[float], effort: list[float]):
    msg = jointstate.publish(name, position, velocity, effort)
    ws_manager.close()
    if msg is not None:
        return "JointState message published successfully"
    else:
        return "No message published"

@mcp.tool()
def sub_jointstate():
    msg = jointstate.subscribe()
    ws_manager.close()
    if msg is not None:
        return msg
    else:
        return "No JointState data received"
'''

if __name__ == "__main__":
    mcp.run(transport="stdio")
