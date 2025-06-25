import cv2
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ultralytics import YOLO
import os
from tempfile import NamedTemporaryFile
from django.conf import settings
from custom_auth.models import DetectionRecord
from custom_auth.views import generate_report
import uuid
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from PIL import Image
import io
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.files.uploadedfile import InMemoryUploadedFile


def upload_image(request):
    return render(request, 'front_end_test.html')


# Load the YOLO model
model = YOLO(r"best.pt")


@csrf_exempt
@login_required
def detect_objects_from_image(request):
    if request.method == 'POST':
        image_file = request.FILES['image']
        with NamedTemporaryFile(delete=False) as temp_image:
            for chunk in image_file.chunks():
                temp_image.write(chunk)
            temp_image_path = temp_image.name

        # Open the image file
        image = cv2.imread(temp_image_path)
        if image is None:
            return JsonResponse({'error': 'Failed to read image.'}, status=500)

        # Perform object detection on the image
        results = model.predict(image, conf=0.25, iou=0.85)
        print(f"Image detection results: {results}")  # 打印图像检测结果

        labels = []
        conf_values = []
        # Draw bounding boxes and labels on the image if needed
        for box in results[0].boxes:
            conf_values.append(box.conf.item())
            x_min, y_min, x_max, y_max = map(int, box.xyxy[0])
            label = model.names[int(box.cls)]
            labels.append(label)
            cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (0, 255, 255), 2)
            cv2.putText(image, label, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            print(f"Detected label in image: {label}")  # 打印检测到的图像标签

        # Save the processed image
        processed_image_filename = str(uuid.uuid4()) + '.jpg'
        processed_image_path = os.path.join(settings.MEDIA_ROOT, processed_image_filename)
        cv2.imwrite(processed_image_path, image)

        # Determine the return value based on labels
        if len(labels) == 0:
            return_value = 'No labels detected'
        elif len(labels) == 1:
            return_value = labels[0]
        elif 'FakeFace' in labels:
            return_value = 'Fake faces'
        else:
            return_value = 'Real faces'

        # Return the URL of the processed image
        image_url = os.path.join(settings.MEDIA_URL, processed_image_filename).replace('\\', '/')

        # 添加调试日志
        print(f"Creating detection record...")
        detection_record = DetectionRecord.objects.create(
            user=request.user,
            result=return_value,
            probability=round(sum(conf_values) / len(conf_values), 2) if conf_values else 0.0,
            media_path=image_url,
            detection_type='image',
            report_path=''
        )
        
        print(f"Generating report...")
        report_path = generate_report(detection_record)
        print(f"Generated report path: {report_path}")
        
        detection_record.report_path = report_path
        detection_record.save()
        print(f"Saved detection record with report path: {detection_record.report_path}")

        # 构建完整的URL
        full_report_url = request.build_absolute_uri(settings.MEDIA_URL + report_path)
        print(f"Full report URL: {full_report_url}")

        response = JsonResponse({
            'image_url': image_url,
            'result': return_value,
            'labels': labels,
            'detected_label': return_value,
            'report_path': full_report_url  # 使用完整URL
        })
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response


@login_required
def upload_video(request):
    return render(request, 'front_end_test.html')


# Load the YOLO model
model = YOLO(r"best.pt")


@csrf_exempt
@login_required
def detect_objects_from_video(request):
    if request.method == 'POST':
        video_file = request.FILES['video']
        with NamedTemporaryFile(delete=False) as temp_video:
            for chunk in video_file.chunks():
                temp_video.write(chunk)
            temp_video_path = temp_video.name

        # Open the video file
        cap = cv2.VideoCapture(temp_video_path)
        video_output_filename = str(uuid.uuid4()) + '.mp4'
        video_output_path = os.path.join(settings.MEDIA_ROOT, video_output_filename)

        # Ensure the media directory exists
        if not os.path.exists(settings.MEDIA_ROOT):
            os.makedirs(settings.MEDIA_ROOT)

        # 保证分辨率为偶数
        width = int(cap.get(3)) // 2 * 2
        height = int(cap.get(4)) // 2 * 2
        print(f"VideoWriter output path: {video_output_path}, width: {width}, height: {height}, codec: mp4v")
        out = cv2.VideoWriter(video_output_path, cv2.VideoWriter_fourcc(*'H264'), 30, (width, height))

        if not out.isOpened():
            response = JsonResponse({'error': 'VideoWriter failed to open.'}, status=500)
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            return response

        labels = []
        conf_values = []
        frame_issues = []  # 记录有FakeFace的帧
        all_labels = set()
        frame_idx = 0
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Perform object detection on the frame
            results = model.predict(frame, conf=0.25, iou=0.85)
            print(f"Video frame detection results: {results}")  # 打印视频帧检测结果

            # Draw bounding boxes and labels on the frame if needed
            frame_labels = []
            for box in results[0].boxes:
                x_min, y_min, x_max, y_max = map(int, box.xyxy[0])
                label = model.names[int(box.cls)]
                conf_values.append(box.conf.item())
                labels.append(label)
                frame_labels.append(label)
                all_labels.add(label)
                cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 255), 2)
                cv2.putText(frame, label, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                print(f"Detected label in video frame: {label}")  # 打印检测到的视频帧标签
            # 记录有FakeFace的帧
            if 'FakeFace' in frame_labels:
                frame_time = round(frame_idx / fps, 2)
                frame_issues.append({'frame': frame_idx, 'time': frame_time, 'label': ','.join(frame_labels)})
            out.write(frame)
            frame_idx += 1

        cap.release()
        out.release()

        # print('labels:',labels)
        # Determine the return value based on labels
        if len(labels) == 0:
            return_value = 'No labels detected'
        elif len(labels) == 1:
            return_value = labels[0]
        elif 'FakeFace' in labels:
            return_value = 'Fake faces exist!!!'
        else:
            return_value = 'All faces are real.'

        # Return the URL of the processed video
        video_url = os.path.join(settings.MEDIA_URL, video_output_filename).replace('\\', '/')

        # 详细检测内容
        result_detail = {
            'labels': list(all_labels),
            'issues': frame_issues,
            'total_frames': frame_idx,
            'summary': return_value
        }

        # 创建检测记录
        detection_record = DetectionRecord.objects.create(
            user=request.user,
            result=json.dumps(result_detail, ensure_ascii=False),
            probability=round(sum(conf_values) / len(conf_values), 2) if conf_values else 0.0,
            media_path=video_url,
            detection_type='video',
            report_path=''
        )
        
        # Generate report and get the path
        print(f"Generating video report...")
        report_path = generate_report(detection_record)
        print(f"Generated video report path: {report_path}")
        
        # Save the report path
        detection_record.report_path = report_path
        detection_record.save()
        print(f"Saved video detection record with report path: {detection_record.report_path}")

        # Build full report URL
        full_report_url = request.build_absolute_uri(settings.MEDIA_URL + report_path)
        print(f"Full video report URL: {full_report_url}")

        # Include report_path in the response
        response = JsonResponse({
            'video_url': video_url, 
            'result': return_value, 
            'labels': labels, 
            'detected_label': return_value,
            'report_path': full_report_url  # Add the report path to response
        })
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response


# --- API for Android App ---
class DetectImageAPI(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, format=None):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            image = Image.open(file_obj).convert("RGB")
            results = model(image)
            detections = []
            for r in results:
                for box in r.boxes:
                    detections.append({
                        "class": int(box.cls[0]),
                        "confidence": float(box.conf[0]),
                        "box": [float(x) for x in box.xyxy[0].tolist()]
                    })
            return Response({"detections": detections})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@login_required
def realtime_detection(request):
    return render(request, 'realtime_detection.html')

@csrf_exempt
@login_required
@require_POST
def realtime_detect(request):
    image = request.FILES.get('image')
    if not image:
        return JsonResponse({'error': 'No image uploaded'}, status=400)
    try:
        # 保存临时图片
        with NamedTemporaryFile(delete=False) as temp_image:
            for chunk in image.chunks():
                temp_image.write(chunk)
            temp_image_path = temp_image.name
        # 读取图片
        img = cv2.imread(temp_image_path)
        if img is None:
            return JsonResponse({'error': 'Failed to read image.'}, status=500)
        # 模型推理
        results = model.predict(img, conf=0.25, iou=0.85)
        labels = []
        conf_values = []
        for box in results[0].boxes:
            conf_values.append(box.conf.item())
            x_min, y_min, x_max, y_max = map(int, box.xyxy[0])
            label = model.names[int(box.cls)]
            labels.append(label)
            cv2.rectangle(img, (x_min, y_min), (x_max, y_max), (0, 255, 255), 2)
            cv2.putText(img, label, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        if len(labels) == 0:
            return_value = '未检测到伪造内容'
        elif 'FakeFace' in labels:
            return_value = '检测到伪造人脸'
        else:
            return_value = '未检测到伪造人脸'
        return JsonResponse({'result': return_value, 'labels': labels})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

