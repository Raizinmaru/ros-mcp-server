from typing import List, Any, Protocol


class Publisher(Protocol):
    def send(self, message: dict) -> None:
        ...


def to_float(value: Any) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid float value: {value}")


class Twist:
    def __init__(self, publisher: Publisher, topic: str = "/cmd_vel"):
        self.publisher = publisher
        self.topic = topic

    def publish(self, linear: List[Any], angular: List[Any]):
        linear_f = [to_float(val) for val in linear]
        angular_f = [to_float(val) for val in angular]

        msg = {
            "op": "publish",
            "topic": self.topic,
            "msg": {
                "linear": {"x": linear_f[0], "y": 0, "z": 0},
                "angular": {"x": 0, "y": 0, "z": angular_f[2]}
            }
        }
        self.publisher.send(msg)
        
        return msg

    def publish_sequence(self, linear_seq: List[Any], angular_seq: List[Any], duration_seq: List[Any]):
        import time
        
        # 入力データの形式を判定して適切に処理
        if linear_seq and isinstance(linear_seq[0], (int, float)):
            # 既に1次元配列の場合（[x, y, z]形式）
            linear_list = [[linear_seq[0], linear_seq[1], linear_seq[2]]]
            angular_list = [[angular_seq[0], angular_seq[1], angular_seq[2]]]
        else:
            # 2次元配列の場合（[[x, y, z], [x, y, z]]形式）
            linear_list = linear_seq
            angular_list = angular_seq
        
        duration_f = [to_float(val) for val in duration_seq]
        
        # 送信周期（Hz）- 通常10Hzくらいが適切
        publish_rate = 10  # 1秒間に10回送信
        sleep_time = 1.0 / publish_rate
        
        for i, duration in enumerate(duration_f):
            if i < len(linear_list) and i < len(angular_list):
                l = [to_float(val) for val in linear_list[i]]
                a = [to_float(val) for val in angular_list[i]]
                
                # 指定時間中、継続的にコマンドを送信
                start_time = time.time()
                while time.time() - start_time < duration:
                    self.publish(l, a)
                    time.sleep(sleep_time)
    
        # 最後に停止コマンドを送信
        self.publish([0, 0, 0], [0, 0, 0])

    '''def publish_sequence(self, linear_seq: List[Any], angular_seq: List[Any], duration_seq: List[Any]):
        import time
        linear_flat = [to_float(val) for sublist in linear_seq for val in sublist]
        angular_flat = [to_float(val) for sublist in angular_seq for val in sublist]
        duration_f = [to_float(val) for val in duration_seq]

        for i in range(len(duration_f)):
            l = linear_flat[i*3:(i+1)*3]
            a = angular_flat[i*3:(i+1)*3]
            self.publish(l, a)
            time.sleep(duration_f[i])
    '''
