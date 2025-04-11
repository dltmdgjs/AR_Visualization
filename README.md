# AR Visualization

### 설명
- camera calibration한 결과를 이용하여 체스판에 AR 물체를 띄움
- AR 물체는 svg 파일을 이용함

### svg 파일 사용 
#### 사용 방법 설명
- svg파일의 경로 데이터를 읽어서 점으로 변환.
1. SVG 파일을 파싱하여 첫 번째 <path> 요소의 경로 데이터를 가져옵니다.
2. 경로를 일정 간격으로 나누어 2D 좌표 점들을 생성합니다.
3. 경로의 바닥을 기준으로 y축을 정렬하여 바닥에 붙입니다.
4. 2D 좌표 (x, y)를 3D 좌표 (x, 0, y)로 변환하여 수직으로 세웁니다.
5. 지정한 offset 값을 더해, 체스보드 위 적절한 위치로 이동시킵니다.
```python
def load_svg_path_points(svg_path, scale=1.0, offset=(0.075, 0.075, 0)):
    # SVG 파일 파싱
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 첫 번째 path 요소 찾기
    svg_ns = {'svg': 'http://www.w3.org/2000/svg'}
    path_elem = root.find('.//svg:path', svg_ns)
    if path_elem is None:
        raise ValueError('SVG path not found.')

    # path 데이터 파싱 -> 경로 데이터를 가져옴.
    d_attr = path_elem.attrib['d']
    path = parse_path(d_attr)

    # 점으로 저장
    points = []
    for segment in path:
        num_points = 20
        for t in np.linspace(0, 1, num_points):
            pt = segment.point(t)
            points.append((pt.real * scale, pt.imag * scale))

    points = np.array(points, dtype=np.float32)

    # === 바닥 맞춤 ===
    max_y = np.max(points[:, 1])      # 바닥은 y의 최대값
    points[:, 1] -= max_y             # 바닥을 y=0으로 이동 

    # 수직으로 세움
    points_3d = np.array([[x, 0, y] for x, y in points], dtype=np.float32)

    # 위치 이동 (보드 위로 이동)
    offset = np.array(offset, dtype=np.float32)
    points_3d += offset

    return points_3d
```
  
- 체스판에 SVG 파일 그리기
```python
...
...
            # 카메라의 각도 및 위치 추정
            ret, rvec, tvec = cv.solvePnP(obj_points, img_points, K, dist_coeff)

            # 3D 점을 2D 점으로 투영 후 SVG 모양 그리기
            projected, _ = cv.projectPoints(svg_points, rvec, tvec, K, dist_coeff)

            # 점을 연결해 선을 시각화
            projected = np.int32(projected).reshape(-1, 2)
            cv.polylines(img, [projected], isClosed=True, color=(0, 0, 255), thickness=2)
...
...
```

### AR 결과
- AR 확인을 위해 다양한 각도에서 촬영
<img width="700" alt="스크린샷 2025-04-11 오후 10 45 54" src="https://github.com/user-attachments/assets/63c09644-52c8-41aa-8166-7fbcb1739f0c" />
<img width="700" alt="스크린샷 2025-04-11 오후 10 46 12" src="https://github.com/user-attachments/assets/1745e547-69ea-4ef9-9f7a-72d79cc81156" />
<img width="700" alt="스크린샷 2025-04-11 오후 10 46 32" src="https://github.com/user-attachments/assets/75ba5340-6cfc-40ac-8035-072d7d1d4103" />





