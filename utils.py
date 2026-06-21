from flask import request
from flask_login import current_user
from models import db, OperationLog

def log_operation(operation_type, operation_module, operation_detail, target_type=None, target_id=None):
    """
    记录操作日志
    
    参数:
        operation_type: 操作类型（登录、创建、编辑、删除、审批等）
        operation_module: 操作模块（项目、工时、报销、任务等）
        operation_detail: 操作详情描述
        target_type: 目标对象类型（可选）
        target_id: 目标对象ID（可选）
    """
    try:
        log = OperationLog(
            user_id=current_user.id,
            operation_type=operation_type,
            operation_module=operation_module,
            operation_detail=operation_detail,
            target_type=target_type,
            target_id=target_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:500]
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"记录操作日志失败: {e}")
        db.session.rollback()