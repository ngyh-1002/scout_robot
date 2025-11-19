<div style="display:flex; align-items:flex-start; gap:10px;">

  <!-- 1번 표: 센서 -->
  <div style="flex-shrink:0; width:320px;">
    <table border="1" style="width:100%; table-layout:fixed; font-size:12px;">
      <tr>
        <th>구분</th><th>사진</th><th>이름</th><th>역할</th>
      </tr>
      <tr>
        <td>LIDAR</td>
        <td><img src="https://github.com/user-attachments/assets/acfdf681-28d3-42b4-a783-15d3527c0cef" width="100" height="100" style="object-fit:cover;"/></td>
        <td>RPLIDAR A1</td>
        <td>지도 작성 (벽, 장애물)</td>
      </tr>
      <tr>
        <td>IMU</td>
        <td><img src="https://github.com/user-attachments/assets/3f73ad06-e3b8-46ef-b53c-08cde9cc9c95" width="100" height="100" style="object-fit:cover;"/></td>
        <td>CH10X</td>
        <td>로봇 이동 궤적 작성</td>
      </tr>
      <tr>
        <td>ENCODER</td>
        <td><img src="https://github.com/user-attachments/assets/dfc7f4ef-bcf7-4b9a-8914-4a041f65c856" width="100" height="100" style="object-fit:cover;"/></td>
        <td>HALL ENCODER</td>
        <td>로봇 이동 궤적 작성</td>
      </tr>
    </table>
  </div>

  <!-- 2번 표: 센서 사용 개발환경-->
  <div style="flex-shrink:0; width:320px;">
    <table border="1" style="width:100%; table-layout:fixed; font-size:12px;">
      <tr>
        <th>참고 이미지</th>
        <th>패키지 설치</th>
        <th>참고 링크</th>
      </tr>
      <tr>
        <td><img src="https://github.com/user-attachments/assets/26c7f88c-59d5-4919-8ce9-36dffa83e4d6" width="100" height="100" style="object-fit:cover;"/></td>
        <td>ROS2 Humble 설치</td>
        <td>https://docs.ros.org/en/humble/index.html</td>
      </tr>
      <tr>
        <td><img src="https://github.com/user-attachments/assets/9317e4fd-b81e-41cf-8263-e188a706e977" width="100" height="100" style="object-fit:cover;"/></td>
        <td>SLAM Toolbox 설치</td>
        <td>[슬램 툴박스 공식문서](https://wiki.ros.org/slam_toolbox)</td>
      </tr>
      <tr>
        <td><img src="https://github.com/user-attachments/assets/c0954e22-2943-4deb-83d1-25959c3fd16e" width="100" height="100" style="object-fit:cover;"/></td>
        <td>Agilex 공식 GitHub <b>scout_ros2</b> 패키지 빌드</td>
        <td>[Agilex공식 깃허브](https://github.com/agilexrobotics/scout_ros2.git)</td>
      </tr>
      <tr>
        <td><img src="https://github.com/user-attachments/assets/c8954346-2abc-42f4-9d16-791e47160700" width="100" height="100" style="object-fit:cover;"/></td>
        <td>Rviz2 설치</td>
        <td>[RVIZ 공식문서](https://docs.ros.org/en/humble/Tutorials/Intermediate/RViz/RViz-User-Guide/RViz-User-Guide.html)</td>
      </tr>
      <tr>
        <td><img src="https://github.com/user-attachments/assets/bb4b9fa2-7c34-4641-b1d7-e0b1dae3e125" width="100" height="100" style="object-fit:cover;"/></td>
        <td>SLAMTEC RPLIDAR A1 패키지 빌드</td>
        <td>[SLAMTEC 공식 깃허브](https://github.com/Slamtec/rplidar_ros.git)</td>
      </tr>
    </table>
  </div>

  <!-- 3번 표: TF Tree -->
  <div style="flex-shrink:0; width:320px;">
    <table border="1" style="width:100%; table-layout:fixed; font-size:12px;">
      <tr><td style="text-align:center;">프레임 연결 및 TF Tree 구성</td></tr>
      <tr><td style="text-align:center;"><img src="사진_경로" width="100" height="100" style="object-fit:cover;"/></td></tr>
    </table>
  </div>

