import cv2
import numpy as np
import face_recognition
import os
import pickle
import requests
import json

path = "C:/Users/HP/OneDrive/Desktop/image"
serverToken = 'AAAAQV4yUpw:APA91bGmnNhW6Neie0I3FJoRIxxOxXB312lxLn1HVBrQ2_91-4uHliUNVnUVslDDio_O084g-pqZHbwqYEr_p_rQV_Ue8ozRdStMXSWPDM_LqHXX3i0tnpWBtjUNauIMdgzfSsvIB22i'
# deviceToken = 'dp547aP5RSeGzn0y0pMWxj:APA91bEQQ7PigdmJ3UDLO13zifixNg7vxc_fgGfPaYqXrQF25fa440-yriFp-3StAaHlgcR-yv8SdEMTcC8q5S_XPBpO5ZhwlFVtSXSfumu-xMJIqD2PvJe-jfChVGxnamFoyUauX5z1'
deviceToken = 'c69qEdr0RUeC7sRaj11oht:APA91bEonmf1MiD56GarUSAjH555JE6paikgx1WuiVZA5sbbqP7ty0eujquCP-2GwHuyGUbjzoJQMcNd-SEMxs2K7X5PFbmU6x6PjurD_JJj3ZR748pzfkn2rPMfjJJ5wAjMPmtkaIhN'

headers = {
        'Content-Type': 'application/json',
        'Authorization': 'key=' + serverToken,
      }

body = {
          'notification': {'title': 'Alert',
                            'body': 'Unknown person detected...'
                            },
          'to':
              deviceToken,
          'priority': 'high',
        #   'data': dataPayLoad,
        }



images = os.listdir(path)
loadedImages = []
names = []
encodingsList = []

print(images)

# a function to capture image
def captureImage(name):
    # To capture a image using webcam
    cam = cv2.VideoCapture(0)
    result, image = cam.read()

    # to save the image in appropriate location along with the name 
    if result == True:
        cv2.imshow("Captured image",image)
        cv2.imwrite(path+'/'+name+'.png', image)
        cv2.waitKey(0)
        cv2.destroyWindow("Captured image")


# To load the images in proper format required to encode
def loadImages():
    images = os.listdir(path)
    for img in images:
        curImg = face_recognition.load_image_file(path+'/'+img)
        loadedImages.append(curImg)
        names.append(img.split(".")[0])

# To encode each image in file and saving the encodings for future use
def encodeImage(name):
    loadImages()
    for img in loadedImages:
        # convert image in RGB format
        img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodingsList.append(encode)

    encodingDic = {}
    with open('encodings', 'wb') as f:
        for i in range(0,len(encodingsList)):
            encodingDic[names[i]]=encodingsList[i]
        pickle.dump(encodingDic,f)
    

def loadEncodings():
    with open('encodings', 'rb') as fl:
        encodingDic = pickle.load(fl)
        encodingDic = dict(encodingDic)

    for name, encodings in encodingDic.items():
        names.append(name)
        encodingsList.append(encodings)

    del encodingDic


# if no images found. We need to train our first image
if len(images)==0:
    print("Enter your name :- ")
    name = input()  
    captureImage(name)
    encodeImage(names)


loadEncodings()
cap = cv2.VideoCapture(0)

arrivalList = {}
i=0

while True:
    success, img = cap.read()
    imgS = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)

    # Detecting all faces in curret faces
    facesCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)


    if encodeCurFrame and facesCurFrame:
        matches = face_recognition.compare_faces(encodingsList, encodeCurFrame[0])
        faceDis = face_recognition.face_distance(encodingsList, encodeCurFrame[0])
        matchIndex = np.argmin(faceDis)

        y1,x2,y2,x1 = facesCurFrame[0]
        flag = 0

        if(faceDis[matchIndex] > 0.45):
            print('Unknown person is waiting at door')
            response = requests.post("https://fcm.googleapis.com/fcm/send",headers = headers, data=json.dumps(body))
            print(response.status_code)
            print(response.json())
            flag = 1

        else :
            if matches[matchIndex]:
                name = names[matchIndex].upper()
                if name not in arrivalList.keys() or arrivalList[name]==-1:
                    body1 = {
                                'notification': {'title': 'Alert',
                                'body': (name)+' arrived..'
                                },
                            'to':
                                    deviceToken,
                                'priority': 'high',
                                    #   'data': dataPayLoad,
                            }
                    response1 = requests.post("https://fcm.googleapis.com/fcm/send",headers = headers, data=json.dumps(body1))
                    print(response1.status_code)
                    print(response1.json())
                print(name)
                print(faceDis[matchIndex])

                i = (i+1)%100
                if name not in arrivalList.keys() or arrivalList[name] == -1:
                    arrivalList[name] = i

                for n in arrivalList.keys():
                    if arrivalList[name] == i+1:
                        arrivalList[n] = -1

                y1,x2,y2,x1 = facesCurFrame[0]

                cv2.rectangle(img,(x1,y1),(x2,y2),(0,255,0),2)
                cv2.rectangle(img,(x1,y2-35),(x2,y2),(0,255,0),cv2.FILLED)
                cv2.putText(img,name,(x1+6,y2-6),cv2.FONT_HERSHEY_COMPLEX,1,(255,255,255),)
        if(flag == 1):
            cv2.imshow('UnknownPerson',img)
            print('Do you know this person? y/n')
            cv2.waitKey(1000)
            inp = input()

            if inp == 'y' or inp == 'Y':
                print('Enter name:- ')
                name = input()
                cv2.imwrite(path+'/'+name+'.png', img)
                encodeImage(names)
                loadEncodings()
            elif inp == 'n' or inp == 'N':
                continue
            else:
                print('invalid input')
            cv2.destroyAllWindows()
                
        else:
            cv2.imshow('WebCam', img)
            cv2.waitKey(1)