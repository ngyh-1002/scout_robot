# scout_robot


-----

# 🤖 Scout Robot Navigation System 

## 📌 1. 프로젝트 개요

이 프로젝트는 ROS 2 (Robot Operating System 2) 및 Nav2 스택을 활용하여 자율 이동 로봇인 Scout가 지정된 목표 지점(방 또는 홈)에 도착했음을 **QR 코드 인식**을 통해 최종적으로 검증하는 시스템입니다.

| 항목 | 설명 |
| :--- | :--- |
| **목표** | Nav2를 이용한 자율 주행 후, 목표 지점의 QR 코드를 인식하여 도착을 확정하고 다음 동작을 준비 |
| **주요 기능** | `/room_command` 토픽을 통한 동적 목표 설정 및 QR 코드 기반 목표 달성 확인 |
| **ROS 버전** | ROS 2 Humble/Iron (작업 환경에 맞게 기재) |

-----

## 🛠️ 2. 빌드 매뉴얼 (Build Manual)

이 패키지는 ROS 2 워크스페이스 (`ros2_ws`) 내에서 `colcon`을 사용하여 빌드됩니다.

### 2.1. 코드 클론 및 워크스페이스 이동

터미널을 열고 워크스페이스의 `src` 디렉토리로 이동한 후, 프로젝트 저장소를 클론합니다.

```bash
# 1. src 디렉토리로 이동
cd ~/ros2_ws/src

# 2. 프로젝트 저장소 클론
git clone https://github.com/ngyh-1002/scout_robot.git
```

### 2.2. 패키지 빌드

워크스페이스 루트 디렉토리로 돌아가 `colcon build` 명령을 사용하여 `scout_robot` 패키지만 빌드합니다.

```bash
# 3. 워크스페이스 루트로 이동
cd ~/ros2_ws

# 4. 패키지 빌드 및 설치 경로 심볼릭 링크 생성
colcon build --packages-select scout_robot --symlink-install
```

### 2.3. 환경 설정 반영 (Source)

빌드된 패키지를 실행 환경에 반영합니다. 이는 새로운 터미널을 열 때마다 실행해야 합니다.

```bash
# 5. 환경 설정 반영
source ~/ros2_ws/install/setup.bash
```

-----

## 🚀 3. 노드 실행 명령어

**주의:** 네비게이션을 실행하기 전에 ROS 2 환경과 로봇 시뮬레이션 환경(Gazebo, Rviz 등)이 먼저 실행되어 있어야 합니다.

### 3.1. QR 인식 노드 실행

카메라 토픽 (`/image_raw/compressed`)을 구독하여 QR 코드를 감지하고, `/room_command` 토픽을 구독하여 기대 QR 코드를 동적으로 설정하는 노드를 실행합니다.

```bash
ros2 run scout_robot qr_detector
```

### 3.2. 네비게이션 명령 노드 실행

Nav2 Goal Action을 사용하여 목표 지점 이동 명령을 내리고, `/room_command` 토픽을 구독하여 QR 인식 노드로부터의 도착 확인 피드백을 처리하는 노드를 실행합니다.

```bash
ros2 run scout_robot nav2_commander
```

### 3.3. 명령 발행 (예시)

`nav2_commander` 노드가 실행 중일 때, 새로운 터미널에서 아래 명령을 통해 로봇에게 이동 목표를 지정할 수 있습니다.

```bash
# 로봇에게 501호로 이동 명령 (QR 코드로 '501'을 기대함)
ros2 topic pub --once /room_command std_msgs/String "data: 'go_room501'" --qos-reliability reliable
```

-----
