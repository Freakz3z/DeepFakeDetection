from django.conf import settings
from django.shortcuts import render, redirect
from django.http import FileResponse, HttpResponseForbidden, HttpResponseRedirect
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import os
from datetime import datetime
from .models import DetectionRecord
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegisterForm
from .models import User
from django.contrib.auth.decorators import login_required
import json
from django.urls import reverse


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '注册成功！请登录')
            return redirect('login')  # 改为重定向到登录页面
        else:
            messages.error(request, '注册信息有误')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


def generate_report(detection_record):
    font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'SimHei.ttf')
    pdfmetrics.registerFont(TTFont('SimHei', font_path))
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    p.setFont('SimHei', 14)
    
    # 报告标题
    p.setFont('SimHei', 16)
    p.drawString(100, 780, '深度伪造检测报告')
    
    # 检测时间为报告生成时间
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 基本信息表（中文）
    data = [
        ['检测类型:', '视频检测' if detection_record.detection_type == 'video' else '图片检测'],
        ['报告生成时间:', now_str],
        ['检测结果:', '见下方详细内容'],
        ['置信度:', f'{detection_record.probability*100:.2f}%'],
    ]
    
    table = Table(data, colWidths=[100, 320])
    table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'SimHei'),
        ('FONTSIZE', (0,0), (-1,-1), 12),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('GRID', (0,0), (-1,-1), 1, colors.lightgrey),
    ]))
    
    table.wrapOn(p, 400, 600)
    table.drawOn(p, 100, 650)
    
    # 详细检测内容（中文）
    p.setFont('SimHei', 13)
    p.drawString(100, 620, '检测详情:')
    p.setFont('SimHei', 12)
    y = 600
    max_width = 420  # 控制内容最大宽度
    def wrap_text(text, max_width, canvas_obj):
        from reportlab.pdfbase.pdfmetrics import stringWidth
        lines = []
        current = ''
        for char in text:
            if stringWidth(current + char, canvas_obj._fontname, canvas_obj._fontsize) > max_width:
                lines.append(current)
                current = char
            else:
                current += char
        if current:
            lines.append(current)
        return lines
    def check_page_and_renew(p, y, fontname='SimHei', fontsize=12, margin=100, reset_y=780):
        if y < margin:
            p.showPage()
            p.setFont(fontname, fontsize)
            return reset_y
        return y
    try:
        if detection_record.detection_type == 'video':
            try:
                details = json.loads(detection_record.result)
            except Exception:
                details = None
            if details and isinstance(details, dict):
                labels = details.get('labels', [])
                issues = details.get('issues', [])
                total_frames = details.get('total_frames', None)
                if total_frames:
                    p.drawString(110, y, f'总帧数: {total_frames}')
                    y -= 18
                    y = check_page_and_renew(p, y)
                if labels:
                    label_str = '所有检测标签: ' + ', '.join(labels)
                    for line in wrap_text(label_str, max_width, p):
                        p.drawString(110, y, line)
                        y -= 16
                        y = check_page_and_renew(p, y)
                if issues:
                    p.drawString(110, y, '检测到伪造人脸的帧:')
                    y -= 18
                    y = check_page_and_renew(p, y)
                    for issue in issues:
                        issue_str = f"帧号 {issue['frame']} (时间: {issue['time']}秒): {issue['label']}"
                        for line in wrap_text(issue_str, max_width-20, p):
                            p.drawString(120, y, line)
                            y -= 15
                            y = check_page_and_renew(p, y)
                else:
                    p.drawString(110, y, '未在任何帧检测到伪造人脸。')
                    y -= 18
                    y = check_page_and_renew(p, y)
            else:
                p.drawString(110, y, '无详细帧信息。')
                y -= 18
                y = check_page_and_renew(p, y)
        else:
            label_str = f"检测标签: {detection_record.result}"
            for line in wrap_text(label_str, max_width, p):
                p.drawString(110, y, line)
                y -= 16
                y = check_page_and_renew(p, y)
    except Exception as e:
        p.drawString(110, y, f'检测详情解析出错: {e}')
        y -= 18
        y = check_page_and_renew(p, y)

    # 结论段落（中文）
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph
    style = ParagraphStyle(
        'ConclusionStyle',
        fontName='SimHei',
        fontSize=12,
        leading=14,
        spaceBefore=6,
        spaceAfter=6,
        leftIndent=0,
        rightIndent=0,
        wordWrap='LTR',
        splitLongWords=True
    )
    # 结论判定
    try:
        details = json.loads(detection_record.result)
        is_fake = False
        if isinstance(details, dict):
            for issue in details.get('issues', []):
                if 'FakeFace' in issue.get('label', ''):
                    is_fake = True
                    break
    except Exception:
        is_fake = 'FakeFace' in detection_record.result
    conclusion_text = (
        '基于AI模型分析，系统判定该媒体文件为<b>{result}</b>，检测置信度为<b>{prob}%</b>。'
        .format(result='伪造' if is_fake else '真实', prob=f'{detection_record.probability*100:.2f}')
    )
    para = Paragraph(conclusion_text, style)
    para.wrapOn(p, 400, 100)
    para.drawOn(p, 100, y-para.height-10)

    p.showPage()
    p.save()
    
    # 确保reports目录存在且有正确的权限
    report_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
    os.makedirs(report_dir, exist_ok=True)
    
    # 在Windows上设置目录权限
    try:
        import stat
        os.chmod(report_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
    except Exception as e:
        print(f"Warning: Could not set directory permissions: {e}")
    
    report_filename = f'report_{detection_record.id}.pdf'
    report_path = os.path.join(report_dir, report_filename)
    
    try:
        with open(report_path, 'wb') as f:
            f.write(buffer.getvalue())
        print(f'Successfully generated report: {report_path}')
    except Exception as e:
        print(f'Error generating report: {str(e)}')
        report_filename = 'error_report.pdf'
    
    media_url = settings.MEDIA_URL.rstrip('/') + '/'
    relative_path = f'reports/{report_filename}'
    detection_record.report_path = relative_path  # 保存相对路径
    return relative_path  # 返回相对路径



def detect_objects_from_image(request):
    if request.method == 'POST':
        image_file = request.FILES['image']
        with NamedTemporaryFile(delete=False) as temp_image:
            for chunk in image_file.chunks():
                temp_image.write(chunk)
            temp_image_path = temp_image.name

        image = cv2.imread(temp_image_path)
        if image is None:
            return JsonResponse({'error': 'Failed to read image.'}, status=500)

        results = model.predict(image, conf=0.25, iou=0.85)
        labels = []
        conf_values = []
        
        for box in results[0].boxes:
            conf_values.append(box.conf.item())
            x_min, y_min, x_max, y_max = map(int, box.xyxy[0])
            label = model.names[int(box.cls)]
            labels.append(label)
            cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (0, 255, 255), 2)
            cv2.putText(image, label, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        processed_image_filename = str(uuid.uuid4()) + '.jpg'
        processed_image_path = os.path.join(settings.MEDIA_ROOT, processed_image_filename)
        cv2.imwrite(processed_image_path, image)

        return_value = 'No labels detected' if not labels else 'Fake faces' if 'FakeFace' in labels else 'Real faces'
        image_url = os.path.join(settings.MEDIA_URL, processed_image_filename).replace('\\', '/')

        detection_record = DetectionRecord.objects.create(
            user=request.user,
            result=return_value,
            probability=round(sum(conf_values)/len(conf_values), 2) if conf_values else 0.0,
            media_path=image_url,
            detection_type='image',
            report_path=''  # 先创建空路径
        )
        # 生成报告前确保记录已存在
        detection_record.report_path = generate_report(detection_record)
        detection_record.save()


        response = JsonResponse({'image_url': image_url, 'result': return_value, 'report_path': request.build_absolute_uri(settings.MEDIA_URL + detection_record.report_path)})
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response


@login_required
def front_end_view(request):
    return render(request, 'front_end_test.html')


@login_required
def history_view(request):
    records = DetectionRecord.objects.filter(user=request.user).order_by('-timestamp')
    for rec in records:
        if rec.detection_type == 'video':
            try:
                details = json.loads(rec.result)
                rec.summary = details.get('summary', '')
            except Exception:
                rec.summary = ''
        else:
            rec.summary = rec.result
    return render(request, 'history.html', {'records': records})


@login_required
def delete_record(request, record_id):
    try:
        rec = DetectionRecord.objects.get(id=record_id, user=request.user)
    except DetectionRecord.DoesNotExist:
        return HttpResponseForbidden('无权限或记录不存在')
    rec.delete()
    return HttpResponseRedirect(reverse('history'))


def logout_view(request):
    logout(request)
    return redirect('/custom_auth/login/')
