import os
from datetime import datetime
from typing import Dict, List, Callable, Any
from flask import jsonify, current_app
import logging

logger = logging.getLogger(__name__)

class HealthCheckMixin:
    """
    Mixin to add health check capabilities to Flask apps
    """
    
    def __init__(self):
        self.health_checks = []
    
    def add_health_check(self, name: str, check_func: Callable[[], Dict[str, Any]]):
        """
        Add a health check function
        
        Args:
            name: Name of the health check
            check_func: Function that returns dict with 'healthy' bool and optional 'message'
        """
        self.health_checks.append({
            'name': name,
            'check': check_func
        })
    
    def create_health_endpoint(self, app):
        """
        Create health check endpoint for Flask app
        """
        
        @app.route('/health')
        def health_check():
            """Comprehensive health check endpoint"""
            
            start_time = datetime.utcnow()
            checks_passed = []
            checks_failed = []
            
            # Run all health checks
            for health_check in self.health_checks:
                try:
                    result = health_check['check']()
                    if result.get('healthy', False):
                        checks_passed.append({
                            'name': health_check['name'],
                            'status': 'healthy',
                            'message': result.get('message', 'OK')
                        })
                    else:
                        checks_failed.append({
                            'name': health_check['name'],
                            'status': 'unhealthy',
                            'message': result.get('message', 'Failed')
                        })
                except Exception as e:
                    checks_failed.append({
                        'name': health_check['name'],
                        'status': 'error',
                        'message': str(e)
                    })
            
            # Calculate overall health
            total_checks = len(checks_passed) + len(checks_failed)
            health_score = len(checks_passed) / total_checks if total_checks > 0 else 0
            
            # Determine status
            if health_score == 1.0:
                status = 'healthy'
                status_code = 200
            elif health_score >= 0.5:
                status = 'degraded'
                status_code = 200
            else:
                status = 'unhealthy'
                status_code = 503
            
            # Build response
            response = {
                'status': status,
                'timestamp': datetime.utcnow().isoformat(),
                'service': os.getenv('SERVICE_NAME', 'unknown'),
                'version': os.getenv('SERVICE_VERSION', '1.0.0'),
                'uptime': self._get_uptime(),
                'health_score': health_score,
                'checks': {
                    'passed': checks_passed,
                    'failed': checks_failed
                },
                'response_time_ms': (datetime.utcnow() - start_time).total_seconds() * 1000
            }
            
            return jsonify(response), status_code
        
        @app.route('/health/live')
        def liveness_check():
            """Simple liveness check for k8s"""
            return jsonify({'status': 'alive'}), 200
        
        @app.route('/health/ready')
        def readiness_check():
            """Readiness check for k8s"""
            # Only check critical dependencies
            critical_checks = [hc for hc in self.health_checks 
                             if hc['name'] in ['database', 'redis']]
            
            for check in critical_checks:
                try:
                    result = check['check']()
                    if not result.get('healthy', False):
                        return jsonify({
                            'status': 'not_ready',
                            'reason': f"{check['name']} is unhealthy"
                        }), 503
                except Exception as e:
                    return jsonify({
                        'status': 'not_ready',
                        'reason': str(e)
                    }), 503
            
            return jsonify({'status': 'ready'}), 200
    
    def _get_uptime(self) -> str:
        """Get service uptime"""
        if hasattr(self, '_start_time'):
            uptime = datetime.utcnow() - self._start_time
            return str(uptime)
        return 'unknown'


# Common health check functions
def check_redis_health(redis_client) -> Dict[str, Any]:
    """Check Redis connectivity"""
    try:
        redis_client.ping()
        return {'healthy': True, 'message': 'Redis is responsive'}
    except Exception as e:
        return {'healthy': False, 'message': f'Redis error: {str(e)}'}


def check_database_health(db_client) -> Dict[str, Any]:
    """Check database connectivity"""
    try:
        # Example for Supabase
        db_client.table('job').select('id').limit(1).execute()
        return {'healthy': True, 'message': 'Database is responsive'}
    except Exception as e:
        return {'healthy': False, 'message': f'Database error: {str(e)}'}


def check_openai_health(openai_client) -> Dict[str, Any]:
    """Check OpenAI API availability"""
    try:
        # Simple models endpoint check
        models = openai_client.models.list()
        return {'healthy': True, 'message': 'OpenAI API is accessible'}
    except Exception as e:
        return {'healthy': False, 'message': f'OpenAI API error: {str(e)}'}


def check_disk_space(threshold_percent: int = 90) -> Dict[str, Any]:
    """Check available disk space"""
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        percent_used = (used / total) * 100
        
        if percent_used < threshold_percent:
            return {
                'healthy': True, 
                'message': f'Disk usage: {percent_used:.1f}%'
            }
        else:
            return {
                'healthy': False,
                'message': f'Disk usage critical: {percent_used:.1f}%'
            }
    except Exception as e:
        return {'healthy': False, 'message': f'Disk check error: {str(e)}'}


def check_memory_usage(threshold_percent: int = 90) -> Dict[str, Any]:
    """Check memory usage"""
    try:
        import psutil
        memory = psutil.virtual_memory()
        
        if memory.percent < threshold_percent:
            return {
                'healthy': True,
                'message': f'Memory usage: {memory.percent:.1f}%'
            }
        else:
            return {
                'healthy': False,
                'message': f'Memory usage critical: {memory.percent:.1f}%'
            }
    except Exception as e:
        return {'healthy': False, 'message': f'Memory check error: {str(e)}'}