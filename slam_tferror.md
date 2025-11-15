아래는 **리드미(README) 형식**으로 정리한 내용이며, 마지막에 **상황 / 문제 / 원인 / 해결 단답 요약**도 포함했어.

---

# 라이다 SLAM 진행 시 `Global Status: frame 'map' does not exist` 에러 분석

## 📌 개요

SLAM을 실행하기 위해 RViz2를 실행했을 때, `Global Status: frame 'map' does not exist` 오류가 발생하였다. 이는 SLAM 패키지가 정상적으로 `map` 프레임을 생성하지 못한 상태에서 발생하는 대표적인 문제다. 본 문서는 문제 원인 분석 과정과 해결 과정을 정리한다.

---

## 🔍 문제 발견 과정

### 1. **RViz2에서 map 관련 토픽이 표시되지 않음 확인**

SLAM을 실행하면 보통 `/map` 토픽이 생성되지만, RViz2에 `/map` 토픽이 나타나지 않았다. 이는 SLAM이 내부적으로 **map → odom → base_link** 변환을 생성하지 못했다는 신호다.

### 2. **TF 트리에서 frame 변환이 이루어지지 않는 것 확인**

`ros2 run tf2_tools view_frames` 또는 `ros2 topic echo /tf_static` 등을 통해 TF 트리를 확인한 결과,

* **laser → base_link** 변환이 존재하지 않음
  즉, SLAM이 라이다 데이터를 로봇 기준 좌표계(base_link)로 변환할 수 없는 상태였다.

### 3. **라이다 프레임과 로봇 베이스 프레임 불일치 확인**

라이다 드라이버에서 발행하는 LaserScan 메시지 확인:

```bash
ros2 topic echo /scan
```

출력 예:

```
header:
  frame_id: "laser"
```

로봇 TF 기준 프레임 확인:

```
base_link
```

라이다의 `frame_id`가 **laser**, 베이스 링크 프레임이 **base_link**로 서로 다르며, 둘 사이에 TF 변환이 없기 때문에 SLAM이 각 데이터를 이어 붙일 수 없었다.

### 4. **왜 map 프레임이 생성되지 않는가**

SLAM 알고리즘은 다음 기본 구조를 필요로 한다:

```
laser → base_link → odom → map
```

라이다의 좌표를 base_link로 변환할 수 없으면
➡ SLAM이 로봇의 위치 변화를 계산할 수 없음
➡ odom ↔ map 관계를 만들 수 없음
➡ 결국 **map 프레임 자체가 생성되지 않음**

즉, **레이저 스캔의 기준 좌표를 로봇 기본 프레임으로 변환할 수 없으면 SLAM의 출력(map)이 생성되지 않는 구조적 문제**다.

---

## ✔ 해결 과정

1. **map 토픽 출력 여부 확인**

   * `/map` 토픽이 생성되지 않는다는 점에서 SLAM 내부가 정상 동작하지 않는다는 것을 파악.

2. **TF Tree 및 tf_static 확인**

   * `view_frames` 및 `/tf_static`을 분석하여 **laser ↔ base_link** 변환이 존재하지 않음을 최종적으로 확인.
   * 이 문제는 SLAM이 레이저 데이터를 base_link 기준으로 해석할 수 없어 발생한 문제임을 확정.

3. **laser → base_link 변환 추가**

   * `robot_state_publisher`, URDF, 또는 `static_transform_publisher`로 변환 관계를 추가
   * 이후 SLAM이 정상적으로 `map` 프레임을 생성하며 RViz에서 오류 해결됨

---

---

# 📌 단답 요약

### ✔ **상황**

SLAM 실행 시 RViz에서 `map` 프레임 에러가 발생

### ✔ **문제**

라이다 프레임과 로봇 베이스 프레임 사이의 변환(TF)이 존재하지 않음.

### ✔ **원인**

LaserScan 메시지의 frame_id는 `laser`, 로봇의 기준 프레임은 `base_link`인데 둘 사이의 TF 변환이 없어서 SLAM이 지도 생성을 못함.

### ✔ **해결**

map 토픽 확인 후 TF Tree와 tf_static을 확인하여 **laser → base_link 변환이 존재하지 않음을 확인**, 해당 TF를 추가하여 문제 해결.
