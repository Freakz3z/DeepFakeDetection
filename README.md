# DeepFakeDetection

基于 YOLOv11 和 Django 的深度伪造（DeepFake）检测平台

## 项目简介

本项目是一个基于 Django 框架开发的深度伪造检测平台，支持用户上传图片或视频，自动检测其真伪，并生成检测报告。

<img width="2529" height="1285" alt="图片2" src="https://github.com/user-attachments/assets/439c0c47-30b7-44a8-a8ba-c518ac67a73a" />

## 主要功能

- 用户注册与登录
- 支持图片、视频的深度伪造检测
- 检测结果展示与历史记录查询
- 检测报告自动生成（PDF）
- 管理员后台管理

## 模型性能

<img width="1224" height="612" alt="图片1" src="https://github.com/user-attachments/assets/761c1749-d123-4e50-af8f-5bc4f7942059" />


## 快速开始

### 1. 环境准备

- Python 3.8+
- pip

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 数据库设置

修改`DeepFakeDetection/mysite/setting.py`中`DATABASE`相关内容

```bash
python manage.py migrate
```

### 4. 创建超级用户（可选）

```bash
python manage.py createsuperuser
```

### 5. 启动服务

```bash
python manage.py runserver
```

### 6. 访问平台

浏览器访问：  
```
http://127.0.0.1:8000/
```
