# 1. 生成新的迁移文件
python manage.py makemigrations

# 2. 将生成的py文件映射应用到数据库
python manage.py migrate

# 3. 启动服务
#python manage.py runserver
python manage.py runserver 127.0.0.1:8000