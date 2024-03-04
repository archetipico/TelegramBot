from cv2 import circle, COLOR_BGR2GRAY, cvtColor, FILLED, FONT_HERSHEY_SIMPLEX, getTextSize, putText, rectangle
from cv2.dnn import blobFromImage, NMSBoxes
from numpy import argmax
from io import BytesIO
from PIL import Image
from requests import get as req
from skimage import io as ski


class Detect:
    def __init__(self, msg, key, deep_nn, classifiers):
        self.msg = msg
        self.key = key
        self.net, self.classes = deep_nn
        self.face_classifier, self.eye_classifier = classifiers

        try:
            self.file_id = msg.reply_to_message.photo[-1].file_id
        except Exception:
            self.file_id = None

        self.args = msg.text.split(' ', 1)
        self.result = {
            'type': 'photo',
            'send': None,
            'caption': None,
            'filename': None,
            'msg_id': msg.message_id,
            'destroy': False,
            'privacy': False,
            'status': True,
            'err': ''
        }

    # Return object detection
    def get(self) -> dict:
        if self.file_id is None:
            self.result['type'] = 'text'
            self.result['send'] = 'Answer to a photo with <code>detect</code>'
            self.result['status'] = False
            return self.result

        try:
            path_req = 'https://api.telegram.org/bot{}/getfile?file_id={}'.format(self.key, self.file_id)
            r = req(path_req, stream=True)
            path = r.json()['result']['file_path']
            path_req = 'https://api.telegram.org/file/bot{}/{}'.format(self.key, path)

            img = ski.imread(path_req)[:, :]
            height, width = img.shape[:2]

            # Create a blob from the image and perform use the YOLO object detector
            blob = blobFromImage(img, 1/255.0, (416, 416), swapRB=True, crop=False)
            self.net.setInput(blob)
            layer_names = self.net.getLayerNames()
            output_layers = [layer_names[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]
            outs = self.net.forward(output_layers)

            # Loop over each detection
            boxes = []
            confidences = []
            class_ids = []
            for out in outs:
                for detection in out:
                    scores = detection[5:]
                    class_id = argmax(scores)
                    confidence = scores[class_id]

                    # Consider only detections with high confidence
                    if confidence > 0.01:
                        center_x = int(detection[0] * width)
                        center_y = int(detection[1] * height)
                        w = int(detection[2] * width)
                        h = int(detection[3] * height)
                        x = int(center_x - w / 2)
                        y = int(center_y - h / 2)

                        boxes.append([x, y, w, h])
                        confidences.append(float(confidence))
                        class_ids.append(class_id)

            # Apply Non-Maximum Suppression to suppress weak overlapping bounding boxes
            indices = NMSBoxes(boxes, confidences, score_threshold=0.01, nms_threshold=0.3)

            # Draw the bounding boxes and labels on the image
            for i in indices:
                i = i[0]
                box = boxes[i]
                x, y, w, h = box
                # Draw object detection box
                rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                # Prepare text
                label = '{}% - {}'.format(round(confidences[i] * 100, 1), self.classes[class_ids[i]])
                label_size = getTextSize(label, FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                label_x = x + w - label_size[0] - 5
                label_y = y + 15
                # Draw text background
                rectangle(
                    img,
                    (int(label_x - 2), int(label_y - label_size[1] - 2)),
                    (int(label_x + label_size[0] + 2), int(label_y + 2)),
                    (255, 255, 255),
                    FILLED
                )
                # Draw text
                putText(img, label, (int(label_x), int(label_y)), FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

            gray = cvtColor(img, COLOR_BGR2GRAY)

            eyes = self.eye_classifier.detectMultiScale(gray)
            faces = self.face_classifier.detectMultiScale(gray)

            # If eyes are detected outside of face, ignore them
            for (x_face, y_face, w_face, h_face) in faces:
                rectangle(img, (x_face, y_face), (x_face + w_face, y_face + h_face), (0, 255, 0), 3)
                for (x_eye, y_eye, w_eye, h_eye) in eyes:
                    if (x_face < (x_eye + w_eye / 2)) and ((x_eye + w_eye / 2) < (x_face + w_face)):
                        if (y_face < (y_eye + h_eye / 2)) and ((y_eye + h_eye / 2) < (y_face + h_face)):
                            w_half = int(w_eye / 2)
                            circle(img, (x_eye + w_half, y_eye + w_half), w_half, (0, 255, 0), 3)

            # Image to bytes
            try:
                img = Image.fromarray(img)
                output = BytesIO()
                img.save(output, format='PNG')
                data = output.getvalue()
            except Exception as e:
                self.result['type'] = 'text'
                self.result['send'] = 'Something went wrong'
                self.result['status'] = False
                self.result['err'] = str(e)
                return self.result

            self.result['send'] = data
            self.result['caption'] = '<i>Any green detection is either a face or an eye</i>'
        except Exception as e:
            self.result['type'] = 'text'
            self.result['send'] = 'Connection error'
            self.result['status'] = False
            self.result['err'] = str(e)

        return self.result
