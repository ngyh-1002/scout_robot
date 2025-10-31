#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from std_msgs.msg import String
import cv2
from pyzbar import pyzbar
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped
from tf_transformations import quaternion_from_euler, euler_from_quaternion
import os
import yaml
import math
from geometry_msgs.msg import PoseWithCovarianceStamped
import numpy as np

# Nav2 노드와의 통신 토픽
ROOM_COMMAND_TOPIC = "/room_command"
ARRIVED_COMMAND = "goal_reached"

class RoomNavigator(Node):
    def __init__(self):
        super().__init__('room_navigator')
        self.navigator = BasicNavigator()
        self.bridge = CvBridge()
        self.qr_detected = False
        self.current_goal_name = None # 현재 이동 중인 목표 이름
        self.initial_pose_set = False

        # --- rooms.yaml 경로 설정 ---
        package_share = get_package_share_directory('scout_robot')
        yaml_path = os.path.join(package_share, 'rooms.yaml')

        if not os.path.exists(yaml_path):
            self.get_logger().error(f"rooms.yaml 파일을 찾을 수 없습니다: {yaml_path}")
            raise FileNotFoundError(yaml_path)

        # --- 좌표 읽기 ---
        with open(yaml_path, 'r') as f:
            self.all_rooms_data = yaml.safe_load(f)['rooms'] # 전체 룸 데이터 로드

        # --- 목표 변수 로드 ---
        self.start_pose = [self.all_rooms_data['start']['x'], self.all_rooms_data['start']['y'], self.all_rooms_data['start']['theta']]
        self.room501_pose = [self.all_rooms_data['room501']['x'], self.all_rooms_data['room501']['y'], self.all_rooms_data['room501']['theta']]
        self.home_pose = [self.all_rooms_data['home']['x'], self.all_rooms_data['home']['y'], self.all_rooms_data['home']['theta']]
        self.room502_pose = [self.all_rooms_data['room502']['x'], self.all_rooms_data['room502']['y'], self.all_rooms_data['room502']['theta']]
        self.room503_pose = [self.all_rooms_data['room503']['x'], self.all_rooms_data['room503']['y'], self.all_rooms_data['room503']['theta']]
        self.start_pose_coords = self.all_rooms_data['start']
        
        # start 좌표를 제외한 모든 QR 필요 목표 좌표 딕셔너리
        self.qr_target_poses = {
            "room501": self.room501_pose,
            "home": self.home_pose,
            "room502": self.room502_pose,
            "room503": self.room503_pose,
        }

        # --- 초기 위치 PoseStamped 생성 ---
        initial_pose = PoseStamped()
        initial_pose.header.frame_id = "map"
        initial_pose.pose.position.x = self.start_pose_coords['x']
        initial_pose.pose.position.y = self.start_pose_coords['y']
        initial_pose.pose.position.z = 0.0

        q = quaternion_from_euler(0, 0, self.start_pose_coords['theta'])
        initial_pose.pose.orientation.x = q[0]
        initial_pose.pose.orientation.y = q[1]
        initial_pose.pose.orientation.z = q[2]
        initial_pose.pose.orientation.w = q[3]

        # --- Nav2 초기 위치 설정 및 활성화 대기 ---
        self.navigator.setInitialPose(initial_pose)
        self.get_logger().info("Nav2 활성화 대기 중...")
        self.navigator.waitUntilNav2Active()
        self.get_logger().info("Nav2 활성화 완료!")
        self.initial_pose_set = True

        # --- 명령 구독 ---
        self.command_sub = self.create_subscription(
            String,
            ROOM_COMMAND_TOPIC,
            self.command_callback,
            10
        )
        
        # --- QR 코드 감지 노드로부터의 '도착 확인' 구독 ---
        self.qr_ack_sub = self.create_subscription(
            String,
            ROOM_COMMAND_TOPIC,
            self.qr_acknowledgement_callback,
            10
        )
        
        # 로봇의 현재 위치를 구독하기 위한 변수 및 구독 설정
        self.current_pose = None
        self.pose_sub = self.create_subscription(
            PoseWithCovarianceStamped,
            '/amcl_pose', # AMCL이 발행하는 로봇의 위치 토픽
            self.pose_callback,
            10
        )
        
        # QR 코드 확인 상태를 추적하는 타이머 (QR Detector가 응답했는지 확인)
        self.qr_check_timer = None
        self.qr_check_timeout_sec = 10.0 # QR 코드 확인 타임아웃
        self.qr_check_in_progress = False

    def pose_callback(self, msg: PoseWithCovarianceStamped):
        """로봇의 현재 위치(PoseWithCovarianceStamped)를 업데이트합니다."""
        self.current_pose = msg.pose.pose

    def qr_acknowledgement_callback(self, msg: String):
        """QR Detector 노드로부터 도착 확인 명령을 수신합니다."""
        if msg.data.strip() == ARRIVED_COMMAND:
            if self.qr_check_in_progress:
                self.get_logger().info("✅ QR Detector로부터 도착 확인 메시지 수신!")
                self.qr_detected = True
            
    def command_callback(self, msg: String):
        """명령어 콜백 함수"""
        command = msg.data.strip()
        
        # 도착 확인 명령은 무시 (qr_acknowledgement_callback에서 처리)
        if command == ARRIVED_COMMAND:
            return 
            
        target_pose = None
        name = ""
        
        if command == "go_room501":
            target_pose, name = self.room501_pose, "room501"
        elif command == "go_home":
            target_pose, name = self.home_pose, "home"
        elif command == "go_room502":
            target_pose, name = self.room502_pose, "room502"
        elif command == "go_room503":
            target_pose, name = self.room503_pose, "room503"
        elif command == "go_start":
            target_pose, name = self.start_pose, "start" # start는 QR 확인 제외
            
        if target_pose:
            self.current_goal_name = name
            self.move_to_target(target_pose, name)
        else:
            self.get_logger().warn(f"알 수 없는 명령 수신: {command}")


    def move_to_target(self, target_pose, name):
        """목표 좌표로 이동"""
        x, y, theta = target_pose
        is_qr_target = name != "start" # start 좌표는 QR 확인 안 함

        pose = PoseStamped()
        pose.header.frame_id = "map"
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = 0.0

        qx, qy, qz, qw = quaternion_from_euler(0, 0, theta)
        pose.pose.orientation.x = qx
        pose.pose.orientation.y = qy
        pose.pose.orientation.z = qz
        pose.pose.orientation.w = qw

        self.get_logger().info(f"{name}으로 이동 중...")
        self.navigator.goToPose(pose)

        # 이동 완료 대기
        while not self.navigator.isTaskComplete():
            rclpy.spin_once(self, timeout_sec=0.5)

        result = self.navigator.getResult()
        if result == TaskResult.SUCCEEDED:
            self.get_logger().info(f"{name} 도착 완료!")
            
            if is_qr_target:
                # 🌟 QR 코드 확인 및 재정렬 로직 시작
                success = self.verify_and_realign_with_qr(name)
                
                # QR 확인에 최종적으로 실패했다면 가장 가까운 다른 목표로 이동 시도
                if not success:
                    self.get_logger().warn(f"⚠️ {name}에서 QR 코드 확인에 최종 실패. 가장 가까운 목표로 재이동 시도.")
                    self.move_to_closest_target()
                    
            else:
                self.get_logger().info(f"'{name}'은 QR 확인 목표가 아닙니다.")
                
        elif result == TaskResult.CANCELED:
            self.get_logger().warn(f"{name} 이동이 취소되었습니다.")
        elif result == TaskResult.FAILED:
            self.get_logger().error(f"{name} 이동 실패. 로봇의 위치나 지도를 확인하세요.")
        else:
            self.get_logger().warn(f"{name} 이동 결과: {result}")
            
        self.current_goal_name = None # 목표 이동이 끝나면 초기화


    def verify_and_realign_with_qr(self, target_name: str) -> bool:
        """
        목표 지점에서 QR 코드를 확인하고, 실패 시 90도씩 회전하며 재탐색합니다.
        성공 시 QR Detector가 위치 재설정 메시지를 발행합니다.
        :param target_name: 이동을 완료한 목표 이름 (예: 'room501')
        :return: QR 코드 확인 및 재정렬 성공 여부
        """
        self.qr_detected = False # 상태 초기화
        self.qr_check_in_progress = True
        
        # QR Detector에게 목표를 알림
        self.publish_command(f"go_{target_name}")
        self.get_logger().info(f"QR Detector에게 '{target_name}' QR 코드 확인 명령을 전송했습니다.")
        
        # 현재 로봇의 초기 자세 (Map 기준)
        if self.current_pose is None:
            self.get_logger().error("로봇의 현재 위치(amcl_pose)를 수신할 수 없습니다. QR 확인을 건너뜁니다.")
            self.qr_check_in_progress = False
            return False

        # 쿼터니언을 오일러 각으로 변환하여 현재 yaw를 얻습니다.
        _, _, initial_yaw = euler_from_quaternion([
            self.current_pose.orientation.x, 
            self.current_pose.orientation.y, 
            self.current_pose.orientation.z, 
            self.current_pose.orientation.w
        ])
        
        # 90도씩 4회 회전 (0, 90, 180, 270도)
        for i in range(4):
            if self.qr_detected:
                break # 이미 QR 코드를 찾았으면 회전 중지

            # 현재 회전 각도 (라디안) 계산
            # i=0: initial_yaw, i=1: initial_yaw + 90도, i=2: initial_yaw + 180도, i=3: initial_yaw + 270도
            target_yaw = initial_yaw + math.radians(i * 90)
            target_yaw = math.atan2(math.sin(target_yaw), math.cos(target_yaw)) # [-pi, pi] 범위로 정규화
            
            # 🌟 회전하여 QR 코드를 찾습니다.
            self.get_logger().info(f"QR 탐색 중: {i*90}도 회전 ({target_yaw:.2f} rad)")
            
            # 목표 자세 PoseStamped 생성
            target_pose = PoseStamped()
            target_pose.header.frame_id = "map"
            target_pose.header.stamp = self.get_clock().now().to_msg()
            target_pose.pose.position.x = self.current_pose.position.x
            target_pose.pose.position.y = self.current_pose.position.y
            target_pose.pose.position.z = 0.0
            
            qx, qy, qz, qw = quaternion_from_euler(0, 0, target_yaw)
            target_pose.pose.orientation.x = qx
            target_pose.pose.orientation.y = qy
            target_pose.pose.orientation.z = qz
            target_pose.pose.orientation.w = qw

            self.navigator.goToPose(target_pose)
            
            # 회전 완료 대기 (최대 5초)
            timeout_counter = 0
            while not self.navigator.isTaskComplete():
                rclpy.spin_once(self, timeout_sec=0.5)
                timeout_counter += 1
                if timeout_counter > 10: # 5초 타임아웃
                    self.get_logger().warn("회전 중 Nav2 타임아웃 발생.")
                    break 

            # QR 코드 감지 대기 (최대 5초)
            # 회전 후 바로 QR 코드 감지를 위해 잠시 대기
            wait_time = 0.0
            while wait_time < self.qr_check_timeout_sec and not self.qr_detected:
                rclpy.spin_once(self, timeout_sec=0.5)
                wait_time += 0.5
                
            if self.qr_detected:
                self.get_logger().info(f"✅ {i*90}도 회전 후 QR 코드 발견! 위치 재설정 명령을 기다립니다.")
                # QR Detector에서 발행한 재설정 메시지(ARRIVED_COMMAND)를 수신하면 
                # QrDetector 노드의 로직에 따라 amcl_pose가 재설정됩니다.
                
                # --- Map 절대 좌표 재지정 요청 ---
                # QR Detector가 ARRIVED_COMMAND를 발행하면, 해당 노드에서 이미
                # 로봇의 위치(amcl_pose)를 QR 코드가 위치한 Map 절대 좌표로 재설정했다고 가정합니다.
                # 'RoomsNavigator'는 별도의 재지정 로직 없이, QR Detector의 재설정 성공을 기다립니다.
                
                self.qr_check_in_progress = False
                return True # 성공

        self.qr_check_in_progress = False
        return False # 4회 회전 후에도 QR 코드를 찾지 못함


    def move_to_closest_target(self):
        """
        현재 로봇의 위치에서 'start'를 제외한 목표 지점들 중 가장 가까운 좌표로 재이동 시도합니다.
        """
        if self.current_pose is None:
            self.get_logger().error("현재 위치를 알 수 없어 가장 가까운 목표로 재이동할 수 없습니다.")
            return

        current_x = self.current_pose.position.x
        current_y = self.current_pose.position.y
        
        min_distance = float('inf')
        closest_target_name = None
        closest_target_pose = None
        
        # 'start' 좌표를 제외한 QR 필요 목표만 확인
        for name, pose in self.qr_target_poses.items():
            target_x, target_y, _ = pose
            distance = math.sqrt((current_x - target_x)**2 + (current_y - target_y)**2)
            
            if distance < min_distance and name != self.current_goal_name:
                min_distance = distance
                closest_target_name = name
                closest_target_pose = pose
                
        if closest_target_name:
            self.get_logger().info(f"가장 가까운 목표 지점 '{closest_target_name}'(거리: {min_distance:.2f}m)으로 다시 이동합니다.")
            self.current_goal_name = closest_target_name
            # 재이동 후 QR 확인 로직을 다시 실행합니다.
            self.move_to_target(closest_target_pose, closest_target_name)
        else:
            self.get_logger().error("재이동할 수 있는 다른 QR 목표 지점이 없습니다.")
            self.current_goal_name = None

    def publish_command(self, command: str):
        """명령 토픽을 발행하는 헬퍼 함수"""
        msg = String()
        msg.data = command
        self.command_sub.publish(msg)


def main():
    rclpy.init()
    node = RoomNavigator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
