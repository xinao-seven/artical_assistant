"""
Celery 应用初始化
占位文件，后续步骤会完善
"""
from celery import Celery
from app.config import settings

# 创建 Celery 实例
celery_app = Celery(
    "paper_assistant",
    broker=settings.REDIS_URL,          # Redis 作为消息队列
    backend=settings.REDIS_URL,         # Redis 作为结果后端
)

# 默认配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_track_started=True,            # 跟踪任务状态
    task_ignore_result=False,
    worker_max_tasks_per_child=100,     # 每100个任务重启worker，防止内存泄漏
)

# 自动发现任务
celery_app.autodiscover_tasks(["app.worker.tasks"])
