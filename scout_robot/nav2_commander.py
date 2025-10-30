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
from tf_transformations import quaternion_from_euler
import os
import yaml


class RoomNavigator(Node):
    def __init__(self):
        super().__init__('room_navigator')
        self.navigator = BasicNavigator()
        self.bridge = CvBridge()
        self.qr_detected = False

        # --- rooms.yaml 경로 설정 ---
        package_share = get_package_share_directory('scout_robot')
        yaml_path = os.path.join(package_share, 'rooms.yaml')

        if not os.path.exists(yaml_path):
            self.get_logger().error(f"rooms.yaml 파일을 찾을 수 없습니다: {yaml_path}")
            raise FileNotFoundError(yaml_path)

        # --- 좌표 읽기 ---
        with open(yaml_path, 'r') as f:
            rooms = yaml.safe_load(f)['rooms']

        self.start_pose = [rooms['start']['x'], rooms['start']['y'], rooms['start']['theta']]
        self.room501_pose = [rooms['room501']['x'], rooms['room501']['y'], rooms['room501']['theta']]
        self.start_pose_coords = rooms['start']

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

        # --- 명령 구독 ---
        self.command_sub = self.create_subscription(
            String,
            '/room_command',
            self.command_callback,
            10
        )

        # --- QR 코드 구독 (추후 사용 가능) ---
        # self.image_sub = self.create_subscription(
        #     Image,
        #     '/camera/image_raw',
        #     self.image_callback,
        #     10
        # )


    def command_callback(self, msg):
        """명령어 콜백 함수"""
        command = msg.data.strip()
        if command == "go_room501":
            self.move_to_target(self.room501_pose, "room501")
        elif command == "go_home":
            self.move_to_target(self.start_pose, "출발점")
        else:
            self.get_logger().warn(f"알 수 없는 명령 수신: {command}")


    def move_to_target(self, target_pose, name):
        """목표 좌표로 이동"""
        x, y, theta = target_pose

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
        elif result == TaskResult.CANCELED:
            self.get_logger().warn(f"{name} 이동이 취소되었습니다.")
        elif result == TaskResult.FAILED:
            self.get_logger().error(f"{name} 이동 실패.")
        else:
            self.get_logger().warn(f"{name} 이동 결과: {result}")


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
