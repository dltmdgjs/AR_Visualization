import numpy as np
import cv2 as cv
from svg.path import parse_path
import xml.etree.ElementTree as ET

def load_svg_path_points(svg_path, scale=1.0, offset=(0.075, 0.075, 0)):
    # SVG 파일 파싱
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 첫 번째 path 요소 찾기
    svg_ns = {'svg': 'http://www.w3.org/2000/svg'}
    path_elem = root.find('.//svg:path', svg_ns)
    if path_elem is None:
        raise ValueError('SVG path not found.')

    # path 데이터 파싱
    d_attr = path_elem.attrib['d']
    path = parse_path(d_attr)

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


if __name__ == '__main__':
    video_file = 'chessboard.avi'
    board_pattern = (10, 7)
    board_cellsize = 0.025
    board_criteria = cv.CALIB_CB_ADAPTIVE_THRESH + cv.CALIB_CB_NORMALIZE_IMAGE + cv.CALIB_CB_FAST_CHECK

    # calibration을 통해 얻은 K, dist_coeff
    K = np.array([[882.44317706, 0, 958.24968432],
         [0, 886.56454061, 530.29022322],
         [0, 0, 1]])    
    dist_coeff = np.array([-0.00648738, 0.02964965, -0.00309162, 0.00061245, -0.02367378])


    # SVG 이미지
    svg_path = 'ex.svg'
    svg_points = load_svg_path_points(svg_path, scale=0.0005) 

    
    # Open a video
    video = cv.VideoCapture(video_file)
    assert video.isOpened(), 'Cannot read the given input, ' + video_file

    # Prepare 3D points on a chessboard
    obj_points = board_cellsize * np.array([[c, r, 0] for r in range(board_pattern[1]) for c in range(board_pattern[0])])

    # Run pose estimation
    while True:
        # Read an image from the video
        valid, img = video.read()
        if not valid:
            break

        # Estimate the camera pose
        success, img_points = cv.findChessboardCorners(img, board_pattern, board_criteria)
        if success:
            ret, rvec, tvec = cv.solvePnP(obj_points, img_points, K, dist_coeff)

            # 투영 후 SVG 모양 그리기
            projected, _ = cv.projectPoints(svg_points, rvec, tvec, K, dist_coeff)
            projected = np.int32(projected).reshape(-1, 2)
            cv.polylines(img, [projected], isClosed=True, color=(0, 0, 255), thickness=2)

            # Print the camera position
            R, _ = cv.Rodrigues(rvec)  
            p = (-R.T @ tvec).flatten()
            info = f'XYZ: [{p[0]:.3f} {p[1]:.3f} {p[2]:.3f}]'
            cv.putText(img, info, (10, 25), cv.FONT_HERSHEY_DUPLEX, 0.6, (0, 255, 0))

        # Show the image and process the key event
        cv.imshow('AR Object Visualization', img)
        key = cv.waitKey(10)
        if key == ord(' '):
            key = cv.waitKey()
        if key == 27: # ESC
            break

    video.release()
    cv.destroyAllWindows()
