#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage 
from std_msgs.msg import String
# from geometry_msgs.msg import PoseWithCovarianceStamped # 🌟 AMCL 리셋은 새 노드가 담당
import cv2
from pyzbar import pyzbar
import numpy as np
from ament_index_python.packages import get_package_share_directory
# from tf_transformations import quaternion_from_euler # 🌟 AMCL 리셋은 새 노드가 담당
import os
import yaml

# ... (기존 QR_COMMAND_TOPIC 정의 생략) ...
QR_COMMAND_TOPIC = "/qr_check_command"

# 🌟 AMCL 리셋 명령을 보낼 토픽 정의
AMCL_RESET_COMMAND_TOPIC = "/amcl_reset_command"

# 목표 명령과 기대 QR 데이터 매핑 딕셔너리
COMMAND_TO_QR_MAP = {
    "go_room501": "501",
    "go_home": "home",  
    "go_room502": "502",
    "go_room503": "503",
}

# QR 데이터에 해당하는 좌표 딕셔너리 (새 노드와 공유되지만, 일단 이 노드에도 유지)
QR_DATA_TO_POSE = {}


class QrDetector(Node):
    def __init__(self):
        super().__init__('qr_detector_node')
        
        self.load_room_coordinates()
        
        self.expected_qr_data = None  
        self.is_qr_detected = False 
        
        # 1. 카메라 구독
        self.camera_subscription = self.create_subscription(
            CompressedImage,
            '/image_raw/compressed',  
            self.image_callback,
            10)
        
        # 2. 목표 명령 구독 (RoomNavigator -> QR Detector)
        self.command_subscription = self.create_subscription(
            String,
            QR_COMMAND_TOPIC, 
            self.command_callback,
            10
        )
        
        # 3. 🌟 AMCL 리셋 명령 발행 (QR Detector -> AMCL Reset Node)
        self.amcl_reset_pub = self.create_publisher(
            String,
            AMCL_RESET_COMMAND_TOPIC,
            10
        )
        
        self.get_logger().info(f'QR Detector Node started. Publishing AMCL reset commands on {AMCL_RESET_COMMAND_TOPIC}...')

    # ... (load_room_coordinates, command_callback 함수는 기존과 동일) ...
    def load_room_coordinates(self):
        """rooms.yaml 파일을 읽어 QR 코드에 해당하는 좌표를 로드합니다."""
        # ... (기존 로직 유지) ...
        global QR_DATA_TO_POSE
        package_share = get_package_share_directory('scout_robot')
        yaml_path = os.path.join(package_share, 'rooms.yaml')
        
        try:
            with open(yaml_path, 'r') as f:
                rooms_data = yaml.safe_load(f)['rooms']
                
            for cmd, qr_data in COMMAND_TO_QR_MAP.items():
                room_name = cmd.replace("go_", "")
                if room_name in rooms_data:
                    QR_DATA_TO_POSE[qr_data] = rooms_data[room_name]
                    
            self.get_logger().info("✅ rooms.yaml에서 QR 목표 좌표 로드 완료.")
        
        except FileNotFoundError:
            self.get_logger().error(f"rooms.yaml 파일을 찾을 수 없습니다: {yaml_path}")
            
    def command_callback(self, msg: String):
        """/qr_check_command 토픽을 구독하여 기대 QR 코드를 동적으로 설정"""
        command = msg.data.strip()
        
        if command in COMMAND_TO_QR_MAP:
            self.expected_qr_data = COMMAND_TO_QR_MAP[command]
            self.is_qr_detected = False  # 새 목표 설정 시 감지 상태 초기화
            self.get_logger().info(f"✅ QR 검사 명령 수신: '{command}'. 기대 QR 코드가 '{self.expected_qr_data}'(으)로 설정되었습니다. QR 스캔 모드 활성화.")
        else:
            self.get_logger().warn(f"⚠️ 알 수 없는 QR 명령 수신: {command}.")


    def image_callback(self, data: CompressedImage):
        """
        QR 코드를 감지하고 성공 시 AMCL 재설정 명령을 발행합니다.
        """
        
        if self.expected_qr_data is None or self.is_qr_detected:
            # ... (비활성화 상태 디버그 뷰 로직 유지) ...
            try:
                np_arr = np.frombuffer(data.data, dtype=np.uint8)
                current_frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                if current_frame is not None:
                    status_text = f"Target: {self.expected_qr_data if self.expected_qr_data else 'None'}. Scanning {'ON' if self.expected_qr_data else 'OFF'}"
                    cv2.putText(current_frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                    cv2.imshow(f"QR Detector View", current_frame)
                    cv2.waitKey(1)
            except Exception as e:
                self.get_logger().error(f'Image data decoding/display failed: {e}')
            return
            
        try:
            np_arr = np.frombuffer(data.data, dtype=np.uint8)
            current_frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if current_frame is None: return

            decoded_objects = pyzbar.decode(current_frame)
            
            for obj in decoded_objects:
                decoded_data = obj.data.decode("utf-8")
                
                if decoded_data == self.expected_qr_data:
                    
                    if not self.is_qr_detected:
                        self.is_qr_detected = True # 감지 상태로 변경
                        
                        self.get_logger().warn(f"✅✅✅ QR 코드 '{self.expected_qr_data}' 인식했습니다! AMCL 재설정을 요청합니다. ✅✅✅")
                        
                        # 🌟🌟🌟 AMCL Reset Node에게 명령 발행 🌟🌟🌟
                        reset_msg = String()
                        # QR 데이터 자체를 명령으로 보냅니다. (예: "501", "home")
                        reset_msg.data = decoded_data 
                        self.amcl_reset_pub.publish(reset_msg)
                        
                        # QR 코드 감지 성공 후 스캔 중지
                        self.expected_qr_data = None
                        
                # ... (기타 QR 코드 표시 로직 생략) ...
                (x, y, w, h) = obj.rect
                color = (0, 255, 0) if decoded_data == self.expected_qr_data else (0, 0, 255)
                cv2.rectangle(current_frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(current_frame, decoded_data, (x, y - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            cv2.imshow(f"QR Detector View", current_frame)
            cv2.waitKey(1)

        except Exception as e:
            self.get_logger().error(f'Image processing failed: {e}')

# ... (main 함수는 기존과 동일) ...
def main(args=None):
    rclpy.init(args=args)
    qr_detector = QrDetector()
    
    try:
        rclpy.spin(qr_detector)
    except KeyboardInterrupt:
        pass
    
    qr_detector.destroy_node()
    rclpy.shutdown()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
