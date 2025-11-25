<svg xmlns="http://www.w3.org/2000/svg" width="1700" height="400">

  <!-- 표 1: 센서 -->
  <g transform="translate(0,0)">
    <rect x="0" y="0" width="320" height="300" fill="none" stroke="black"/>
    <text x="160" y="20" text-anchor="middle" font-size="14" font-weight="bold">센서</text>
    
    <!-- 헤더 -->
    <text x="20" y="50" font-size="12">구분</text>
    <text x="90" y="50" font-size="12">사진</text>
    <text x="160" y="50" font-size="12">이름</text>
    <text x="240" y="50" font-size="12">역할</text>
    
    <!-- 데이터 행 -->
    <text x="20" y="80" font-size="12">LIDAR</text>
    <rect x="80" y="65" width="60" height="60" fill="#eee" stroke="black"/> <!-- 이미지 자리 -->
    <text x="160" y="100" font-size="12">RPLIDAR A1</text>
    <text x="240" y="100" font-size="12">지도 작성 (벽, 장애물)</text>
    
    <text x="20" y="150" font-size="12">IMU</text>
    <rect x="80" y="135" width="60" height="60" fill="#eee" stroke="black"/>
    <text x="160" y="165" font-size="12">CH10X</text>
    <text x="240" y="165" font-size="12">로봇 이동 궤적 작성</text>
    
    <text x="20" y="220" font-size="12">ENCODER</text>
    <rect x="80" y="205" width="60" height="60" fill="#eee" stroke="black"/>
    <text x="160" y="235" font-size="12">HALL ENCODER</text>
    <text x="240" y="235" font-size="12">로봇 이동 궤적 작성</text>
  </g>

  <!-- 표 2: 개발환경 -->
  <g transform="translate(340,0)">
    <rect x="0" y="0" width="320" height="300" fill="none" stroke="black"/>
    <text x="160" y="20" text-anchor="middle" font-size="14" font-weight="bold">개발환경</text>

    <!-- 헤더 -->
    <text x="10" y="50" font-size="12">참고 이미지</text>
    <text x="120" y="50" font-size="12">노드 실행 및 토픽발행</text>
    <text x="250" y="50" font-size="12">참고 링크</text>

    <!-- 예시 데이터 행 1 -->
    <rect x="10" y="60" width="60" height="60" fill="#eee" stroke="black"/>
    <text x="120" y="95" font-size="12">ROS2 Humble 설치</text>
    <text x="250" y="95" font-size="12">https://docs.ros.org/en/humble/index.html</text>

    <!-- 예시 데이터 행 2 -->
    <rect x="10" y="130" width="60" height="60" fill="#eee" stroke="black"/>
    <text x="120" y="165" font-size="12">SLAM Toolbox 설치</text>
    <text x="250" y="165" font-size="12">https://wiki.ros.org/slam_toolbox</text>

    <!-- 예시 데이터 행 3 -->
    <rect x="10" y="200" width="60" height="60" fill="#eee" stroke="black"/>
    <text x="120" y="235" font-size="12">Agilex scout_ros2 패키지 빌드</text>
    <text x="250" y="235" font-size="12">https://github.com/agilexrobotics/scout_ros2.git</text>
  </g>

  <!-- 표 3: 빈 자리 -->
  <g transform="translate(680,0)">
    <rect x="0" y="0" width="320" height="300" fill="none" stroke="black"/>
    <text x="160" y="20" text-anchor="middle" font-size="14" font-weight="bold">표 3 (빈 자리)</text>
  </g>

  <!-- 표 4: TF Tree -->
  <g transform="translate(1020,0)">
    <rect x="0" y="0" width="320" height="300" fill="none" stroke="black"/>
    <text x="160" y="20" text-anchor="middle" font-size="14" font-weight="bold">프레임 연결 및 TF Tree 구성</text>
    <rect x="110" y="80" width="100" height="100" fill="#eee" stroke="black"/> <!-- 이미지 자리 -->
  </g>

  <!-- 표 5: 빈 자리 -->
  <g transform="translate(1360,0)">
    <rect x="0" y="0" width="320" height="300" fill="none" stroke="black"/>
    <text x="160" y="20" text-anchor="middle" font-size="14" font-weight="bold">표 5 (빈 자리)</text>
  </g>

</svg>
