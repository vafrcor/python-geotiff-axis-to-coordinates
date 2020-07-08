import cv2, os
import numpy as np
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import hsv_to_rgb
import argparse, pprint

# Argument Parsing
ap = argparse.ArgumentParser()
ap.add_argument("-sr", "--show_result", required=False, help="whether need to show result or not", default=False, type=str)
ap.add_argument("-i", "--image", required=False, help="image source", default=None, type=str)
ap.add_argument("-dbg", "--debug", required=False, help="whether need to show debug or not", default="False", type=str)
args = vars(ap.parse_args())
show_result= True if args['show_result'] == "True" else False
show_debug= True if args['debug'] == "True" else False

# Get images
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
img_path= args['image'] if args['image'] is not None else 'data/edge-detection/sample-04.png'
img_extension = os.path.splitext(img_path)[1]

# BGR code color for Building in OpenStreetMaps is (224,217,211)
light_brown = np.uint8([[[202,208,216 ]]]) 
# print('light_brown: ', light_brown);

#Convert BGR to HSV for masking
color_codes=[]
hsv_light_brown = cv2.cvtColor(light_brown,cv2.COLOR_BGR2HSV)

for index in hsv_light_brown:
  color_codes=index[0]

# Start masking the image here
image= cv2.imread(os.path.join(BASE_DIR, img_path), 1)
maps= cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

gray= cv2.cvtColor(maps, cv2.COLOR_RGB2HSV)
brown = (float(color_codes[0]), float(color_codes[1]), float(color_codes[2]))
darker_brown = (float(color_codes[0])+30, float(color_codes[1])+30, float(color_codes[2])+30)

# cream= (13, 17, 216)
# brown = (100, 100, 226)

mask = cv2.inRange(gray, brown, darker_brown)
hsv= cv2.bitwise_and(image, image, mask=mask)

# save images
cv2.imwrite(os.path.join(BASE_DIR, img_path.replace(img_extension,'-method-3-hsv-light-color'+img_extension)), hsv_light_brown)
cv2.imwrite(os.path.join(BASE_DIR, img_path.replace(img_extension,'-method-3-hsv'+img_extension)), hsv)


# show the final image
if show_result:
  cv2.imshow("Result - HSV Light Color", hsv_light_brown)
  cv2.imshow("Result - HSV", hsv)
  cv2.waitKey(0)
  cv2.destroyAllWindows()

  # plt.subplot(1,2,1)
  # plt.imshow(hsv, cmap="gray")
  # plt.title('OSM Image')
  # plt.xticks([]), plt.yticks([])
  # plt.show()
