# Scout Mini SLAM 개요

로봇에서 사용된 센서와 역할:

| 구분    | 사진 | 이름        | 역할                  |
|--------|------|------------|---------------------|
| LIDAR  | <img src="https://github.com/user-attachments/assets/acfdf681-28d3-42b4-a783-15d3527c0cef" width="200" height="200"/> | RPLIDAR A1 | 지도 작성 (벽, 장애물) |
| IMU    | <img src="https://github.com/user-attachments/assets/3f73ad06-e3b8-46ef-b53c-08cde9cc9c95" width="200" height="200"/> | CH10X | 로봇 이동 궤적 작성   |
| ENCODER | <img src="https://github.com/user-attachments/assets/dfc7f4ef-bcf7-4b9a-8914-4a041f65c856" width="200" height="200"/> | HALL ENCODER | 로봇 이동 궤적 작성   |

## 🛠 개발환경 구축 정리

<table>
  <tr>
    <th>참고 이미지</th>
    <th>노드 실행 및 토픽발행</th>
    <th>참고 링크</th>
  </tr>

  <tr>
    <td>
      <div style="width:80px;height:80px;overflow:hidden;">
        <img src="https://github.com/user-attachments/assets/26c7f88c-59d5-4919-8ce9-36dffa83e4d6"
             style="width:80px;height:80px;object-fit:cover;display:block;" />
      </div>
    </td>
    <td>ROS2 Humble 설치</td>
    <td>https://docs.ros.org/en/humble/index.html</td>
  </tr>

  <tr>
    <td>
      <div style="width:80px;height:80px;overflow:hidden;">
        <img src="https://github.com/user-attachments/assets/9317e4fd-b81e-41cf-8263-e188a706e977"
             style="width:80px;height:80px;object-fit:cover;display:block;" />
      </div>
    </td>
    <td>SLAM Toolbox 설치</td>
    <td>https://wiki.ros.org/slam_toolbox</td>
  </tr>

  <tr>
    <td>
      <div style="width:80px;height:80px;overflow:hidden;">
        <img src="https://github.com/user-attachments/assets/c0954e22-2943-4deb-83d1-25959c3fd16e"
             style="width:80px;height:80px;object-fit:cover;display:block;" />
      </div>
    </td>
    <td>Agilex 공식 GitHub <b>scout_ros2</b> 패키지 빌드</td>
    <td>https://github.com/agilexrobotics/scout_ros2.git</td>
  </tr>

  <tr>
    <td>
      <div style="width:80px;height:80px;overflow:hidden;">
        <img src="https://github.com/user-attachments/assets/c8954346-2abc-42f4-9d16-791e47160700"
             style="width:80px;height:80px;object-fit:cover;display:block;" />
      </div>
    </td>
    <td>Rviz2 설치</td>
    <td>https://docs.ros.org/en/humble/Tutorials/Intermediate/RViz/RViz-User-Guide/RViz-User-Guide.html</td>
  </tr>

  <tr>
    <td>
      <div style="width:80px;height:80px;overflow:hidden;">
        <img src="https://github.com/user-attachments/assets/bb4b9fa2-7c34-4641-b1d7-e0b1dae3e125"
             style="width:80px;height:80px;object-fit:cover;display:block;" />
      </div>
    </td>
    <td>SLAMTEC RPLIDAR A1 패키지 빌드</td>
    <td>https://github.com/Slamtec/rplidar_ros.git</td>
  </tr>

</table>
