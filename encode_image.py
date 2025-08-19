import cv2

def encrypt():

    img1 = cv2.imread('1.jpg')
    img2 = cv2.imread('2.jpg')

    for i in range(img2.shape[0]):
        for j in range(img2.shape[1]):
            for l in range(3):

                v1 = format(img1[i][j][l], '08b')
                v2 = format(img2[i][j][l], '08b')

                v3 = v1[:4] + v2[:4]

                img1[i][j][l] = int(v3, 2)

    cv2.imwrite('3.png', img1)
encrypt()