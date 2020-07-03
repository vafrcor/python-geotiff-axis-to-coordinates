import os
import numpy as np
import matplotlib.pyplot as plt
import cv2

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
img = cv2.imread(os.path.join(BASE_DIR, 'data/edge-detection/shapes_and_colors.jpg'))
edge = cv2.Canny(img, 100, 200)

print(edge.shape)
ans = []
for y in range(0, edge.shape[0]):
    for x in range(0, edge.shape[1]):
        if edge[y, x] != 0:
            ans = ans + [[x, y]]
ans = np.array(ans)

print(ans.shape)
print(ans[0:10, :])
# print(ans)
