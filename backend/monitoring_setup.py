"""
Production monitoring and observability utilities.
Tracks API performance, structured logs, health checks, and alert thresholds.
"""

import csv
import json
import logging
import os
import shutil
import threading
import time
import traceback
from datetime import datetime, timezone
from functools import wraps


class ProductionLogger:
    """Structured JSON logger for production telemetry."""

    _instance = None
    _instance_lock = threading.Lock()

    def __init__(self, log_file='backend/logs/production.log'):
        self.log_file = log_file
        self._ensure_log_dir()
        self.logger = logging.getLogger('quantum_ml_app')
        self._configure_handlers()

    @classmethod
    def get_instance(cls):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = ProductionLogger()
            return cls._instance

    def _ensure_log_dir(self):
        log_dir = os.path.dirname(self.log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

    def _configure_handlers(self):
        if self.logger.handlers:
            return

        self.logger.setLevel(logging.INFO)

        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)

        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    @staticmethod
    def _now_iso():
        return datetime.now(timezone.utc).isoformat()

    def _emit(self, level, payload):
        payload = dict(payload)
        payload.setdefault('timestamp', self._now_iso())
        payload.setdefault('log_level', level)
        line = json.dumps(payload, ensure_ascii=True)

        if level == 'DEBUG':
            self.logger.debug(line)
        elif level == 'WARNING':
            self.logger.warning(line)
        elif level == 'ERROR':
            self.logger.error(line)
        elif level == 'CRITICAL':
            self.logger.critical(line)
        else:
            self.logger.info(line)

    @classmethod
    def log_api_call(cls, endpoint, method, status_code, duration_ms):
        cls.get_instance()._emit(
            'INFO',
            {
                'type': 'api_call',
                'endpoint': endpoint,
                'method': method,
                'status_code': int(status_code),
                'duration_ms': round(float(duration_ms), 3),
            },
        )

    @classmethod
    def log_ml_event(cls, event_type, model_name, metrics):
        cls.get_instance()._emit(
            'INFO',
            {
                'type': 'ml_event',
                'event': event_type,
                'model': model_name,
                'metrics': metrics or {},
            },
        )

    @classmethod
    def log_error(cls, error_type, error_message, traceback_str, endpoint=None):
        cls.get_instance()._emit(
            'ERROR',
            {
                'type': 'error',
                'error_type': error_type,
                'error_message': str(error_message),
                'endpoint': endpoint,
                'traceback': traceback_str,
            },
        )


class PerformanceMonitor:
    """In-memory API performance metrics collector."""

    def __init__(self):
        self.lock = threading.Lock()
        self.metrics = {
            'total_requests': 0,
            'total_errors': 0,
            'avg_response_time_ms': 0.0,
            'min_response_time_ms': None,
            'max_response_time_ms': 0.0,
            'endpoints': {},
        }

    def record_request(self, endpoint, duration_ms, success=True):
        with self.lock:
            m = self.metrics
            m['total_requests'] += 1
            if not success:
                m['total_errors'] += 1

            n = m['total_requests']
            prev_avg = m['avg_response_time_ms']
            m['avg_response_time_ms'] = ((prev_avg * (n - 1)) + duration_ms) / n

            if m['min_response_time_ms'] is None:
                m['min_response_time_ms'] = duration_ms
            else:
                m['min_response_time_ms'] = min(m['min_response_time_ms'], duration_ms)
            m['max_response_time_ms'] = max(m['max_response_time_ms'], duration_ms)

            if endpoint not in m['endpoints']:
                m['endpoints'][endpoint] = {
                    'count': 0,
                    'errors': 0,
                    'avg_ms': 0.0,
                    'min_ms': None,
                    'max_ms': 0.0,
                }

            e = m['endpoints'][endpoint]
            e['count'] += 1
            if not success:
                e['errors'] += 1

            c = e['count']
            e['avg_ms'] = ((e['avg_ms'] * (c - 1)) + duration_ms) / c
            e['min_ms'] = duration_ms if e['min_ms'] is None else min(e['min_ms'], duration_ms)
            e['max_ms'] = max(e['max_ms'], duration_ms)

    def get_metrics(self):
        with self.lock:
            snapshot = json.loads(json.dumps(self.metrics))

        total = snapshot.get('total_requests', 0)
        errors = snapshot.get('total_errors', 0)
        snapshot['error_rate'] = (errors / total) if total else 0.0
        return snapshot

    def get_endpoint_stats(self, endpoint):
        with self.lock:
            return json.loads(json.dumps(self.metrics['endpoints'].get(endpoint, {})))

    def reset_metrics(self):
        with self.lock:
            self.metrics = {
                'total_requests': 0,
                'total_errors': 0,
                'avg_response_time_ms': 0.0,
                'min_response_time_ms': None,
                'max_response_time_ms': 0.0,
                'endpoints': {},
            }


def track_performance(func):
    """Decorator for timing function execution and logging failures."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            performance_monitor.record_request(func.__name__, duration_ms, success=True)
            ProductionLogger.log_api_call(func.__name__, 'N/A', 200, duration_ms)
            return result
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            performance_monitor.record_request(func.__name__, duration_ms, success=False)
            ProductionLogger.log_error(type(exc).__name__, str(exc), traceback.format_exc(), endpoint=func.__name__)
            raise

    return wrapper


class HealthCheck:
    """System health probes for ML and storage dependencies."""

    @staticmethod
    def check_ml_model():
        from ml_model_trainer import QuantumKeyQualityClassifier

        try:
            classifier = QuantumKeyQualityClassifier()
            loaded = classifier.load_model()
            metadata = classifier.get_metadata() if loaded else {}
            return {
                'model_loaded': bool(loaded),
                'model_size_mb': float(metadata.get('model_size_mb', 0.0) or 0.0),
                'prediction_latency_ms': metadata.get('prediction_latency_ms'),
                'status': 'healthy' if loaded else 'unhealthy',
            }
        except Exception as exc:
            return {
                'model_loaded': False,
                'model_size_mb': 0.0,
                'prediction_latency_ms': None,
                'status': 'unhealthy',
                'error': str(exc),
            }

    @staticmethod
    def check_data_logging():
        from ml_data_logger import QuantumDataLogger

        logger = QuantumDataLogger()
        stats = logger.get_dataset_stats()
        csv_path = logger.csv_path
        latest_ts = None
        logs_being_written = False

        try:
            if os.path.exists(csv_path):
                with open(csv_path, 'r', encoding='utf-8-sig') as handle:
                    reader = csv.DictReader(handle)
                    last_row = None
                    for row in reader:
                        last_row = row
                    if last_row:
                        latest_ts = last_row.get('timestamp')
                        logs_being_written = True
        except Exception:
            logs_being_written = False

        return {
            'logs_being_written': logs_being_written,
            'latest_log_timestamp': latest_ts,
            'total_samples': int(stats.get('total_samples', 0) or 0),
            'status': 'healthy' if logs_being_written else 'degraded',
        }

    @staticmethod
    def check_storage():
        root_path = os.path.abspath('.')
        total, used, free = shutil.disk_usage(root_path)
        usage = (used / total) if total else 0.0

        if usage >= 0.95:
            status = 'critical'
        elif usage >= 0.85:
            status = 'warning'
        else:
            status = 'healthy'

        return {
            'total_gb': round(total / (1024 ** 3), 3),
            'used_gb': round(used / (1024 ** 3), 3),
            'available_gb': round(free / (1024 ** 3), 3),
            'usage_percent': round(usage * 100.0, 3),
            'status': status,
        }

    @staticmethod
    def check_api_endpoints():
        app_path = os.path.join('backend', 'app.py')
        targets = ['/api/health', '/api/generate-key', '/api/ml/status', '/api/ml/improvement-summary']
        found = {ep: False for ep in targets}

        try:
            with open(app_path, 'r', encoding='utf-8') as handle:
                text = handle.read()
                for endpoint in targets:
                    found[endpoint] = endpoint in text
        except Exception:
            pass

        healthy_count = sum(1 for ok in found.values() if ok)
        status = 'healthy' if healthy_count == len(targets) else 'degraded'

        return {
            'endpoints_checked': len(targets),
            'endpoints_healthy': healthy_count,
            'response_times': {},
            'route_presence': found,
            'status': status,
        }

    @staticmethod
    def full_system_health():
        checks = {
            'ml_model': HealthCheck.check_ml_model(),
            'data_logging': HealthCheck.check_data_logging(),
            'storage': HealthCheck.check_storage(),
            'api_endpoints': HealthCheck.check_api_endpoints(),
        }

        statuses = [checks[k].get('status') for k in checks]
        if any(s in ('critical', 'unhealthy') for s in statuses):
            overall = 'unhealthy'
        elif any(s in ('warning', 'degraded') for s in statuses):
            overall = 'degraded'
        else:
            overall = 'healthy'

        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'overall_status': overall,
            'checks': checks,
        }


class AlertManager:
    """Threshold-based local alert manager."""

    def __init__(self):
        self.alert_thresholds = {
            'error_rate': 0.05,
            'response_time': 5000,
            'storage_usage': 90.0,
            'model_accuracy': 0.75,
            'uptime': 0.95,
        }

    def check_error_rate(self, error_count, total_count):
        rate = (error_count / total_count) if total_count else 0.0
        if rate > self.alert_thresholds['error_rate']:
            self.send_alert('WARNING', f'High error rate detected: {rate:.2%}')
            return True
        return False

    def check_response_time(self, avg_response_time_ms):
        if avg_response_time_ms > self.alert_thresholds['response_time']:
            self.send_alert('WARNING', f'High average response time: {avg_response_time_ms:.2f}ms')
            return True
        return False

    def check_storage_usage(self, usage_percent):
        if usage_percent > self.alert_thresholds['storage_usage']:
            self.send_alert('CRITICAL', f'Storage usage critical: {usage_percent:.2f}%')
            return True
        return False

    def check_ml_performance(self, model_accuracy):
        if model_accuracy < self.alert_thresholds['model_accuracy']:
            self.send_alert('WARNING', f'ML model performance degraded: {model_accuracy:.4f}')
            return True
        return False

    def send_alert(self, alert_level, alert_message):
        payload = {
            'type': 'alert',
            'level': alert_level,
            'message': alert_message,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

        ProductionLogger.get_instance()._emit(alert_level if alert_level in ('WARNING', 'ERROR', 'CRITICAL') else 'INFO', payload)

        alert_log = os.path.join('backend', 'logs', 'alerts.log')
        os.makedirs(os.path.dirname(alert_log), exist_ok=True)
        with open(alert_log, 'a', encoding='utf-8') as handle:
            handle.write(json.dumps(payload) + '\n')


production_logger = ProductionLogger.get_instance()
performance_monitor = PerformanceMonitor()
alert_manager = AlertManager()
