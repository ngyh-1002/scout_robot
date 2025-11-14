
---

# 🚀 Nav2 경로 생성 실패 문제 분석 및 해결방안

## 📌 1. 문제 상황 개요
---

### 1️⃣ `global_costmap.global_costmap`: Received request to clear entirely

```
[INFO] [global_costmap.global_costmap]: Received request to clear entirely the global_costmap
```

* 의미: 글로벌 코스트맵(global costmap)이 “완전히 초기화(clear)” 요청을 받았다는 뜻.
* 이유: 보통 장애물이 갑자기 바뀌거나 로봇이 경로를 다시 계산해야 할 때, 맵을 새로 그리려고 함.

---

### 2️⃣ `planner_server` 관련 경고

```
[WARN] [planner_server]: GridBased: failed to create plan with tolerance 0.50
[WARN] [planner_server]: Planning algorithm GridBased failed to generate a valid path to (0.38, -0.04)
[WARN] [planner_server]: [compute_path_to_pose] [ActionServer] Aborting handle
```

* 의미:

  * **GridBased Planner**가 목표 위치 `(0.38, -0.04)`까지 경로를 만들지 못했다.
  * `tolerance 0.50` → 목표에서 0.5m 내에서 도달 가능하면 허용하겠다는 설정인데, 이 범위 내에서도 유효 경로를 찾지 못했다.
  * 결국 경로 계산이 실패해서 ActionServer에서 **Abort 처리** 됨.
* 원인 가능성:

  * 장애물이 경로를 막고 있음.
  * 로봇 초기 위치와 목표 사이에 **연결된 경로가 없음**.
  * 코스트맵이나 SLAM 정보가 잘못됨.

---

### 3️⃣ `behavior_server` 관련 경고

```
[INFO] [behavior_server]: Running spin
[WARN] [behavior_server]: Collision Ahead - Exiting Spin
[WARN] [behavior_server]: spin failed
```

* 의미:

  * **Spin behavior**: 로봇이 제자리에서 360도 회전해서 주변 상황을 확인하는 동작.
  * `Collision Ahead` → 회전 중 전방에 충돌 위험이 감지되어 동작 종료.
* Backup behavior도 실패:

```
[WARN] [behavior_server]: Collision Ahead - Exiting DriveOnHeading
```

* 이유: 로봇이 후진하려 했지만 뒤쪽에도 장애물이 있어서 실패.

---

### 4️⃣ `bt_navigator` 관련

```
[WARN] [bt_navigator]: [navigate_to_pose] [ActionServer] Aborting handle
[ERROR] [bt_navigator]: Goal failed
```

* 의미:

  * Behavior Tree Navigator가 목표 Pose 이동을 처리하다가 **실패**.
  * 결국 Goal 자체가 실패로 종료됨.

---

### 5️⃣ 전체적으로 요약하면

* 로봇이 목표 위치 `(0.38, -0.04)`로 가려고 시도했지만:

  1. 글로벌/로컬 코스트맵에 장애물 또는 데이터 이상으로 경로 생성 실패
  2. 회전(spin) 및 후진(backup) 행동 시도했지만 충돌 위험 때문에 모두 실패
  3. Nav2 BT Navigator가 최종적으로 Goal을 실패 처리

* 즉 **현재 맵/환경에서 목표까지 안전하게 도달할 경로가 없다는 뜻**.

---

### 🔹 원인과 체크리스트

1. **코스트맵 확인**

   * `ros2 topic echo /global_costmap/costmap` 확인 → 장애물이 너무 많거나 로봇 주변에 데이터를 잘못 인식했는지 확인.
2. **SLAM / AMCL 위치 확인**

   * 로봇의 `pose`가 실제 위치와 맞는지 확인.
3. **목표 위치 유효성**

   * 목표가 로봇 주변에 지나갈 수 없는 위치는 아닌지 확인.
4. **로봇 크기 / footprint**

   * 로봇 footprint가 실제 맵의 통로보다 커서 경로 생성이 불가능할 수 있음.
5. **Nav2 planner 설정**

   * GridBased planner tolerance, inflation radius, obstacle range 등 매개변수 확인.

---


ROS2 Nav2 환경에서 스카우트 미니 로봇(폭 58cm, 길이 62cm)을 사용해 네비게이션을 수행하는 과정에서, 특정 목표 지점으로 이동하려고 할 때 글로벌 플래너가 반복적으로 경로 생성에 실패하고 다양한 Behavior(Spin, Backup 등)까지 실패하는 로그가 발생하였다.

대표 로그:

```
GridBased: failed to create plan with tolerance 0.50.
Planning algorithm GridBased failed to generate a valid path
Collision Ahead - Exiting Spin
backup failed
Goal failed
```

---

## 📌 2. 증상 상세 분석

### 🔸 글로벌 플래너 경로 생성 실패

* GridBased Planner가 목표 지점까지 유효한 경로를 만들지 못함
* tolerance 0.50m 이내에서도 경로가 형성되지 않음
* 이후 BT Navigator가 Goal을 실패로 마무리함

### 🔸 Behavior 서버의 행동 실패

* Spin behavior 도중 전방 충돌 위험 감지 → 즉시 중지
* Backup behavior 역시 충돌 위험으로 실패

### 🔸 글로벌/로컬 costmap 반복 초기화

* Costmap clear 요청이 여러 번 발생
  → 로봇이 경로를 못 찾고 실패 루프에 들어간 전형적인 패턴

---

## 📌 3. 원인 분석

### 🔸 실제 원인: **글로벌 costmap 설정과 좁은 통로 문제**

* 글로벌 costmap의 **인플레이션이 30**으로 매우 높음
* 로봇 footprint는 폭 58cm, 길이 62cm
* 실제 통로 폭은 78cm로 극히 좁은 편

➡ 글로벌 플래너 입장에서는
“로봇 + 인플레이션 + 안전거리”
가 합쳐져 **통로가 지나갈 수 없는 곳처럼 인식됨**

즉, 로봇이 통로를 지나갈 충분한 공간이 현실에는 있지만, costmap 상에서는 불가능한 환경으로 계산됨.

➡ 그 결과

* 글로벌 플래너 → 경로 없음 → 실패
* Behavior(Spin, Backup) → costmap 상에서 충돌 위험 → 실패
* BT Navigator → Goal 실패

---

## 📌 4. 제안된 해결방안

### 💡 핵심 아이디어

**글로벌 플래너에서는 로봇 크기를 작게 잡고,
로컬 플래너에서는 실제 로봇 크기로 충돌 회피를 담당하게 한다.**

이는 Nav2에서 널리 쓰는 기법이고 실제 로봇 주행에서 매우 유효하다.

---

## 📌 5. 최적 설정 전략

### ✔ Global Planner

| 설정 항목            | 추천 값                    | 설명                |
| ---------------- | ----------------------- | ----------------- |
| footprint        | 실제보다 작게(예: 50cm × 50cm) | 좁은 구간에서도 경로 생성 가능 |
| inflation_radius | 기존처럼 크게 유지              | 경로를 중앙에 두게 함      |
| role             | “경로 생성 담당”              | 안전보다는 전체 경로 계산 중심 |

### ✔ Local Planner (DWB / Teb)

| 설정 항목            | 추천 값               | 설명              |
| ---------------- | ------------------ | --------------- |
| footprint        | 실제 크기(58cm × 62cm) | 실제 충돌 방지        |
| inflation_radius | 실제 안전거리 기준         | 현장에서 장애물 피하기 담당 |

결과적으로,

* 글로벌 플래너는 “작은 로봇”이라고 가정하여 경로를 만들고
* 로컬 플래너는 “진짜 로봇 크기”로 충돌을 실제로 회피하여 안전하게 통과한다.

---

## 📌 6. 기대 효과

* 글로벌 플래너 경로 끊김 문제 해결
* 좁은 통로에서도 경로 생성 가능
* 로컬 플래너가 실제 로봇 크기로 충돌을 방지하므로 안전 확보
* 반복적인 Spin/Backup 실패 루프 해소
* BT Navigator Goal 실패 방지

---

# ✅ 단답 요약

* **상황:** 좁은 통로(78cm)에서 Nav2가 경로를 생성하지 못함
* **문제:** 글로벌 플래너가 로봇 크기 + 큰 인플레이션으로 인해 경로 생성 실패
* **원인:** costmap 계산상 로봇이 통로를 지나갈 수 없다고 판단됨
* **해결방안:** 글로벌 플래너 로봇 크기를 줄이고, 로컬 플래너에서 실제 footprint로 충돌 회피 담당시키기
