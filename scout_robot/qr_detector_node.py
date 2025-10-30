import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage 
from std_msgs.msg import String
import cv2
from pyzbar import pyzbar
import numpy as np
import time # 디버깅을 위해 time 모듈 추가 가능 (여기서는 사용하지 않음)


# Nav2 노드와의 통신 토픽
ROOM_COMMAND_TOPIC = "/room_command" 
# 목표 도착을 알리는 명령어 (Nav2 노드에서 처리해야 함)
ARRIVED_COMMAND = "goal_reached" 

# 목표 명령과 기대 QR 데이터 매핑 딕셔너리
# 예: "go_room501" 명령을 받으면 "501" QR 코드를 기대합니다.
COMMAND_TO_QR_MAP = {
    "go_room501": "501",
    "go_home": "home",  # 'go_home' 명령을 받았을 때 'home' QR 코드를 기대
    "go_room502": "502",
    "go_room503": "503",
}

class QrDetector(Node):
    def __init__(self):
        super().__init__('qr_detector_node')
        
        # ⚠️ 동적으로 인식해야 할 QR 코드 데이터
        self.expected_qr_data = None 
        
        # 1. 카메라 구독 (Subscription) 설정
        self.camera_subscription = self.create_subscription(
            CompressedImage,
            '/image_raw/compressed',  
            self.image_callback,
            10)
        
        # 2. 목표 명령 구독 (Subscription) 설정 (추가됨)
        # /room_command 토픽을 구독하여 목표 명령이 바뀔 때마다 expected_qr_data를 업데이트
        self.command_subscription = self.create_subscription(
            String,
            ROOM_COMMAND_TOPIC,
            self.command_callback,
            10
        )
        
        # 3. 도착 발행 (Publisher) 설정
        self.publisher_ = self.create_publisher(
            String, 
            ROOM_COMMAND_TOPIC, 
            10
        )
        
        self.is_qr_detected = False
        self.get_logger().info(f'QR Detector Node started. Waiting for commands on {ROOM_COMMAND_TOPIC}...')


    def command_callback(self, msg: String):
        """/room_command 토픽을 구독하여 기대 QR 코드를 동적으로 설정"""
        command = msg.data.strip()
        
        if command in COMMAND_TO_QR_MAP:
            # 기대하는 QR 코드 데이터 설정
            self.expected_qr_data = COMMAND_TO_QR_MAP[command]
            self.is_qr_detected = False  # 새 목표 설정 시 감지 상태 초기화
            self.get_logger().info(f"✅ 새 목표 명령 수신: '{command}'. 기대 QR 코드가 '{self.expected_qr_data}'(으)로 설정되었습니다.")
        else:
            # goal_reached와 같은 명령은 무시하고, 알 수 없는 명령에 대해서만 경고
            if command != ARRIVED_COMMAND:
                 self.get_logger().warn(f"⚠️ 알 수 없는 명령 수신: {command}. 기대 QR 코드를 업데이트하지 않습니다.")


    def image_callback(self, data: CompressedImage):
        """
        ROS CompressedImage 메시지를 디코딩하고 QR 코드를 감지합니다.
        """
        
        # --- 기대 QR 데이터가 설정되지 않았으면 스캔하지 않음 ---
        if self.expected_qr_data is None:
            self.get_logger().debug("기대 QR 코드가 설정되지 않아 스캔을 건너뜁니다.")
            # 디코딩된 이미지가 필요할 수 있으므로, 이미지를 디코딩하여 표시합니다.
            try:
                current_frame = cv2.imdecode(np.frombuffer(data.data, dtype=np.uint8), cv2.IMREAD_COLOR)
                if current_frame is not None:
                    cv2.imshow(f"QR Detector (Target: None)", current_frame)
                    cv2.waitKey(1)
            except Exception:
                pass # 디코딩 실패 시 무시하고 반환
            return

        # --- 이미지 디코딩 ---
        try:
            np_arr = np.frombuffer(data.data, dtype=np.uint8)
            current_frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if current_frame is None:
                self.get_logger().error("Image decoding failed.")
                return

        except Exception as e:
            self.get_logger().error(f'Image data decoding failed: {e}')
            return
        
        # --- QR 코드 감지 및 디코딩 ---
        decoded_objects = pyzbar.decode(current_frame)
        qr_detected_in_frame = False
        
        # ⚠️ 디버깅용: 감지된 객체가 없을 경우
        if not decoded_objects:
             self.get_logger().debug(f"카메라에서 QR 코드를 찾을 수 없습니다. (기대: {self.expected_qr_data})")


        for obj in decoded_objects:
            decoded_data = obj.data.decode("utf-8")
            
            # 1. 기대하는 QR 코드와 일치하는지 확인 (성공)
            if decoded_data == self.expected_qr_data:
                qr_detected_in_frame = True
                
                # 중복 발행 방지 체크
                if not self.is_qr_detected:
                    self.is_qr_detected = True # 감지 상태로 변경
                    
                    # 도착 확인 메시지 생성 및 발행
                    msg = String()
                    msg.data = ARRIVED_COMMAND 
                    self.publisher_.publish(msg)
                    
                    # 🌟 요청하신 콘솔 메시지 출력 (도착 확인)
                    self.get_logger().warn(f"🌟🌟 목표 QR 코드 '{self.expected_qr_data}' 감지! '{ROOM_COMMAND_TOPIC}'에 '{ARRIVED_COMMAND}' 메시지 발행 완료! 🌟🌟")
                    
                    # ✅ QR 코드 감지 성공 후 기대 QR 데이터 초기화 (핵심 수정)
                    # 다음 명령을 받기 전까지 QR 인식을 중지하여 중복 발행을 확실히 막습니다.
                    self.expected_qr_data = None 
                    
            
            # 2. 🚫 기대하는 QR 코드가 아닌 다른 목표 QR 코드인 경우 (경고)
            elif decoded_data in COMMAND_TO_QR_MAP.values(): 
                self.get_logger().warn(f"🚫 예상치 못한 QR 코드 감지! 기대 QR: '{self.expected_qr_data}', 감지된 QR: '{decoded_data}' (무시)")
            
            # 3. ℹ️ Nav2 목표와 관련 없는 기타 QR 코드인 경우 (정보)
            else:
                self.get_logger().info(f"다른 정보성 QR 코드 감지: {decoded_data} (Nav2 명령과 무관하여 무시)")

            # --- 영상 표시를 위한 바운딩 박스 및 텍스트 ---
            (x, y, w, h) = obj.rect
            # 기대 QR과 일치하면 녹색, 아니면 빨간색 (다른 목표 QR 포함)
            color = (0, 255, 0) if decoded_data == self.expected_qr_data else (0, 0, 255)
            cv2.rectangle(current_frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(current_frame, decoded_data, (x, y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # 프레임에서 QR 코드가 사라졌을 경우 상태 초기화
        if not qr_detected_in_frame and self.is_qr_detected:
            self.is_qr_detected = False

        # --- 영상 표시 ---
        cv2.imshow(f"QR Detector (Target: {self.expected_qr_data if self.expected_qr_data else 'None'})", current_frame)
        cv2.waitKey(1) 

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
