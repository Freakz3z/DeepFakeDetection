from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
from django.db import models

class User(AbstractUser):
    groups = models.ManyToManyField(
        Group,
        verbose_name='用户组',
        blank=True,
        help_text='用户所属的组',
        related_name='custom_user_groups',
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='用户权限',
        blank=True,
        help_text='用户拥有的特定权限',
        related_name='custom_user_permissions',
        related_query_name='user',
    )
    last_login = models.DateTimeField(verbose_name='最后登录时间', default=timezone.now)

    class Meta:
        verbose_name = '用户信息'
        verbose_name_plural = verbose_name

class DetectionRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='custom_auth_records')
    result = models.TextField(verbose_name='检测结果')
    probability = models.FloatField(verbose_name='结果概率', null=True, blank=True, default=0.0)
    media_path = models.CharField(max_length=255, verbose_name='媒体路径', default='')
    detection_type = models.CharField(max_length=20, choices=[('image', '图片检测'), ('video', '视频检测')], default='image', verbose_name='检测类型')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='检测时间')
    report_path = models.CharField(max_length=255, null=True, blank=True, verbose_name='检测报告路径')

    class Meta:
        verbose_name = '检测记录'
        verbose_name_plural = verbose_name
        ordering = ['-timestamp']
