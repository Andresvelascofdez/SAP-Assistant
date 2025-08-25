"""
Sistema de logging estructurado
Wiki Inteligente SAP IS-U
"""
import logging
import sys
from typing import Any, Dict
import structlog
from api.config import settings


def configure_logging():
    """Configurar logging estructurado"""
    # Configurar structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.JSONRenderer() if settings.log_format == "json" 
            else structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper())
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configurar logging estándar
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(message)s",
        stream=sys.stdout,
    )


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Obtener logger estructurado"""
    return structlog.get_logger(name)


def add_request_context(request_id: str, user_id: str = None, tenant: str = None):
    """Añadir contexto de request a logs"""
    context = {"request_id": request_id}
    if user_id:
        context["user_id"] = user_id
    if tenant:
        context["tenant"] = tenant
    
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(**context)
