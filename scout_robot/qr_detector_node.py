import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage 
from std_msgs.msg import String
from geometry_msgs.msg import PoseWithCovarianceStamped
import cv2
from pyzbar import pyzbar
import numpy as np
from ament_index_python.packages import get_package_share_directory
from tf_transformations import quaternion_from_euler
import os
import yaml


# Nav2 노드와의 통신 토픽
ROOM_COMMAND_TOPIC = "/room_command" 
# 목표 도착을 알리는 명령어 (Nav2 노드에서 처리해야 함)
ARRIVED_COMMAND = "goal_reached" 

# 목표 명령과 기대 QR 데이터 매핑 딕셔너리
COMMAND_TO_QR_MAP = {
    "go_room501": "501",
    "go_home": "home",  
    "go_room502": "502",
    "go_room503": "503",
}

# QR 데이터에 해당하는 좌표 딕셔너리 (동적으로 로드됨)
QR_DATA_TO_POSE = {}


class QrDetector(Node):
    def __init__(self):
        super().__init__('qr_detector_node')
        
        # --- rooms.yaml 경로 및 좌표 로드 ---
        self.load_room_coordinates()
        
        # ⚠️ 동적으로 인식해야 할 QR 코드 데이터
        self.expected_qr_data = None 
        
        # 1. 카메라 구독 (Subscription) 설정
        self.camera_subscription = self.create_subscription(
            CompressedImage,
            '/image_raw/compressed',  
            self.image_callback,
            10)
        
        # 2. 목표 명령 구독 (Subscription) 설정
        self.command_subscription = self.create_subscription(
            String,
            ROOM_COMMAND_TOPIC,
            self.command_callback,
            10
        )
        
        # 3. 도착 발행 (Publisher) 설정 (RoomNavigator에게 QR 인식 성공 알림)
        self.publisher_ = self.create_publisher(
            String, 
            ROOM_COMMAND_TOPIC, 
            10
        )
        
        # 4. 초기 위치 재설정 발행 (Publisher) 설정 (AMCL에게 위치 재설정 요청)
        self.initial_pose_pub = self.create_publisher(
            PoseWithCovarianceStamped,
            '/initialpose', # AMCL의 위치 재설정 토픽
            10
        )
        
        self.is_qr_detected = False
        self.get_logger().info(f'QR Detector Node started. Waiting for commands on {ROOM_COMMAND_TOPIC}...')

    def load_room_coordinates(self):
        """rooms.yaml 파일을 읽어 QR 코드에 해당하는 좌표를 로드합니다."""
        global QR_DATA_TO_POSE
        package_share = get_package_share_directory('scout_robot')
        yaml_path = os.path.join(package_share, 'rooms.yaml')
        
        try:
            with open(yaml_path, 'r') as f:
                rooms_data = yaml.safe_load(f)['rooms']
                
            # QR 코드와 목표 좌표 매핑
            for cmd, qr_data in COMMAND_TO_QR_MAP.items():
                room_name = cmd.replace("go_", "")
                if room_name in rooms_data:
                    QR_DATA_TO_POSE[qr_data] = rooms_data[room_name]
                    
            self.get_logger().info("✅ rooms.yaml에서 QR 목표 좌표 로드 완료.")
        
        except FileNotFoundError:
            self.get_logger().error(f"rooms.yaml 파일을 찾을 수 없습니다: {yaml_path}")
            # QR_DATA_TO_POSE가 비어 있으면 위치 재설정은 불가능
            
            
    def publish_initial_pose(self, pose_data):
        """
        AMCL에 현재 로봇의 위치(Map 절대 좌표)를 재설정하도록 명령합니다.
        """
        x, y, theta = pose_data['x'], pose_data['y'], pose_data['theta']
        
        initial_pose_msg = PoseWithCovarianceStamped()
        initial_pose_msg.header.frame_id = "map"
        initial_pose_msg.header.stamp = self.get_clock().now().to_msg()

        initial_pose_msg.pose.pose.position.x = x
        initial_pose_msg.pose.pose.position.y = y
        initial_pose_msg.pose.pose.position.z = 0.0

        # Yaw 각도(theta)를 쿼터니언으로 변환
        q = quaternion_from_euler(0, 0, theta)
        initial_pose_msg.pose.pose.orientation.x = q[0]
        initial_pose_msg.pose.pose.orientation.y = q[1]
        initial_pose_msg.pose.pose.orientation.z = q[2]
        initial_pose_msg.pose.pose.orientation.w = q[3]

        # 공분산은 일반적으로 큰 값으로 설정하여 위치가 불확실함을 알립니다.
        # (AMCL이 주변 환경을 기반으로 위치를 다시 결정하게 함)
        initial_pose_msg.pose.covariance = np.diag([
            0.5*0.5, 0.5*0.5, 0.0, 0.0, 0.0, np.radians(30.0)*np.radians(30.0)
        ]).flatten().tolist()
        
        self.initial_pose_pub.publish(initial_pose_msg)
        self.get_logger().warn(f"🌟🌟 위치 재설정 명령 발행: ({x:.2f}, {y:.2f}, {theta:.2f} rad) 🌟🌟")


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
        
        # --- 기대 QR 데이터가 설정되지 않았거나 QR_DATA_TO_POSE에 없으면 스캔하지 않음 ---
        if self.expected_qr_data is None or self.expected_qr_data not in QR_DATA_TO_POSE:
            self.get_logger().debug("기대 QR 코드가 설정되지 않았거나 좌표가 없어 스캔을 건너뜁니다.")
            # ... (영상 표시 로직 생략 가능, 필요하면 주석 해제)
            return

        # --- 이미지 디코딩 ---
        try:
            np_arr = np.frombuffer(data.data, dtype=np.uint8)
            current_frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if current_frame is None:
                # self.get_logger().error("Image decoding failed.")
                return

        except Exception as e:
            self.get_logger().error(f'Image data decoding failed: {e}')
            return
        
        # --- QR 코드 감지 및 디코딩 ---
        decoded_objects = pyzbar.decode(current_frame)
        qr_detected_in_frame = False
        
        for obj in decoded_objects:
            decoded_data = obj.data.decode("utf-8")
            
            # 1. 기대하는 QR 코드와 일치하는지 확인 (성공)
            if decoded_data == self.expected_qr_data:
                qr_detected_in_frame = True
                
                # 중복 발행 방지 체크
                if not self.is_qr_detected:
                    self.is_qr_detected = True # 감지 상태로 변경
                    
                    # 1. 위치 재설정 명령 발행 (AMCL)
                    pose_data = QR_DATA_TO_POSE[decoded_data]
                    self.publish_initial_pose(pose_data)
                    
                    # 2. 도착 확인 메시지 생성 및 발행 (RoomNavigator에게 알림)
                    msg = String()
                    msg.data = ARRIVED_COMMAND 
                    self.publisher_.publish(msg)
                    
                    # 🌟 콘솔 메시지 출력 (도착 및 재설정 확인)
                    self.get_logger().warn(f"🌟🌟 목표 QR 코드 '{self.expected_qr_data}' 감지! 위치 재설정 및 도착 알림 메시지 발행 완료! 🌟🌟")
                    
                    # ✅ QR 코드 감지 성공 후 기대 QR 데이터 초기화 (핵심 수정)
                    self.expected_qr_data = None 
                    
            
            # 2. 🚫 기대하는 QR 코드가 아닌 다른 목표 QR 코드인 경우 (경고)
            elif decoded_data in COMMAND_TO_QR_MAP.values(): 
                self.get_logger().warn(f"🚫 예상치 못한 QR 코드 감지! 기대 QR: '{self.expected_qr_data}', 감지된 QR: '{decoded_data}' (무시)")
            
            # 3. ℹ️ Nav2 목표와 관련 없는 기타 QR 코드인 경우 (정보)
            else:
                self.get_logger().info(f"다른 정보성 QR 코드 감지: {decoded_data} (Nav2 명령과 무관하여 무시)")

            # --- 영상 표시를 위한 바운딩 박스 및 텍스트 ---
            (x, y, w, h) = obj.rect
            color = (0, 255, 0) if decoded_data == self.expected_qr_data else (0, 0, 255)
            cv2.rectangle(current_frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(current_frame, decoded_data, (x, y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # 프레임에서 QR 코드가 사라졌을 경우 상태 초기화
        if not qr_detected_in_frame and self.is_qr_detected:
            # 이 로직은 재설정 후 다시 명령이 들어올 때까지 QR 인식을 막기 위해 주석 처리하거나 제거
            # self.is_qr_detected = False
            pass

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
