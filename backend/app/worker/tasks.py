"""
Celery 任务定义
占位文件，后续步骤会完善
"""
from app.worker.celery_app import celery_app


@celery_app.task(name="placeholder_task")
def placeholder_task():
    """占位任务"""
    return "ok"
