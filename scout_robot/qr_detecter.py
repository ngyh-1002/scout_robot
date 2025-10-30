import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage 
from std_msgs.msg import String # ⚠️ String 메시지 타입 추가
import cv2
from pyzbar import pyzbar
import numpy as np

# 특정 QR 코드 데이터를 정의합니다.
TARGET_QR_DATA = "501" 
ARRIVED_COMMAND = "goal_reached" # QR 코드가 감지되었을 때 보낼 명령
ROOM_COMMAND_TOPIC = "/room_command" # Nav2 노드가 구독하는 토픽

class QrDetector(Node):
    def __init__(self):
        super().__init__('qr_detector_node')
        
        # 1. 구독 (Subscription) 설정 (기존과 동일)
        self.subscription = self.create_subscription(
            CompressedImage,
            '/image_raw/compressed',  
            self.listener_callback,
            10)
        
        # 2. 발행 (Publisher) 설정 (추가됨)
        # Nav2 연동을 위해 /room_command 토픽에 String 메시지를 발행합니다.
        self.publisher_ = self.create_publisher(
            String, 
            ROOM_COMMAND_TOPIC, 
            10
        )
        
        # QR 코드 감지 상태를 추적하는 변수
        self.is_qr_detected = False
        self.get_logger().info(f'QR Detector Node started, publishing to {ROOM_COMMAND_TOPIC} and subscribing to /image_raw/compressed...')

    def listener_callback(self, data: CompressedImage):
        """
        ROS CompressedImage 메시지를 디코딩하고 QR 코드를 감지합니다.
        """
        # --- 이미지 디코딩 (기존과 동일) ---
        try:
            np_arr = np.frombuffer(data.data, dtype=np.uint8)
            current_frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if current_frame is None:
                self.get_logger().error("Image decoding failed (cv2.imdecode returned None).")
                return

        except Exception as e:
            self.get_logger().error(f'Image data decoding failed: {e}')
            return
        
        # --- QR 코드 감지 및 디코딩 ---
        decoded_objects = pyzbar.decode(current_frame)
        qr_detected_in_frame = False

        for obj in decoded_objects:
            decoded_data = obj.data.decode("utf-8")
            
            self.get_logger().info(f'Detected QR Code: {decoded_data}')
            
            (x, y, w, h) = obj.rect
            cv2.rectangle(current_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(current_frame, decoded_data, (x, y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # 3. 특정 QR 코드 감지 시 메시지 발행 (수정된 핵심 로직)
            if decoded_data == TARGET_QR_DATA:
                qr_detected_in_frame = True
                
                # 중복 발행 방지를 위해 상태를 확인
                if not self.is_qr_detected:
                    self.is_qr_detected = True # 감지 상태로 변경
                    
                    # 도착 확인 메시지 생성 및 발행
                    msg = String()
                    msg.data = ARRIVED_COMMAND 
                    self.publisher_.publish(msg)
                    
                    # ⚠️ 요청하신 콘솔 메시지 출력
                    self.get_logger().warn(f"🌟🌟 QR코드 '{TARGET_QR_DATA}' 감지! '{ROOM_COMMAND_TOPIC}'에 '{ARRIVED_COMMAND}' 메시지 발행 완료! 🌟🌟")
            
        # 프레임에서 QR 코드가 사라졌을 경우 상태 초기화
        if not qr_detected_in_frame and self.is_qr_detected:
            self.is_qr_detected = False

        # --- 영상 표시 (기존과 동일) ---
        cv2.imshow("QR Code Detector Feed (Compressed)", current_frame)
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