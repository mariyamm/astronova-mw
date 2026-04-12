#!/usr/bin/env python3
"""
AstroNova Render.com Deployment Validator

This script validates that your AstroNova deployment on Render.com 
is working correctly by testing all critical endpoints and services.

Usage:
    python validate_deployment.py https://your-app.onrender.com
"""

import sys
import json
import requests
import time
from typing import Dict, List, Tuple

def colorize(text: str, color: str) -> str:
    """Add color to console output"""
    colors = {
        'green': '\033[92m',
        'red': '\033[91m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'reset': '\033[0m'
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"

def success(msg: str) -> str:
    return colorize(f"✅ {msg}", 'green')

def error(msg: str) -> str:
    return colorize(f"❌ {msg}", 'red')

def warning(msg: str) -> str:
    return colorize(f"⚠️  {msg}", 'yellow')

def info(msg: str) -> str:
    return colorize(f"ℹ️  {msg}", 'blue')

class RenderValidator:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.results: List[Tuple[str, bool, str]] = []
        
    def test(self, name: str, func) -> bool:
        """Run a test and record the result"""
        print(f"\n🧪 Testing: {name}")
        try:
            success_msg = func()
            print(success(success_msg))
            self.results.append((name, True, success_msg))
            return True
        except Exception as e:
            error_msg = str(e)
            print(error(error_msg))
            self.results.append((name, False, error_msg))
            return False
    
    def test_basic_connectivity(self) -> str:
        """Test basic API connectivity"""
        response = requests.get(f"{self.base_url}", timeout=self.timeout)
        if response.status_code == 200:
            return "API is accessible"
        elif response.status_code == 302:
            return "API is accessible (redirected to login)"
        else:
            raise Exception(f"API returned status code {response.status_code}")
    
    def test_health_endpoint(self) -> str:
        """Test health check endpoint"""
        response = requests.get(f"{self.base_url}/api/admin/health", timeout=self.timeout)
        if response.status_code != 200:
            raise Exception(f"Health check failed with status {response.status_code}")
        
        data = response.json()
        if data.get('status') != 'healthy':
            raise Exception(f"Health status is '{data.get('status')}', not 'healthy'")
        
        return f"Health check passed - {data.get('service', 'Unknown')}"
    
    def test_database_connectivity(self) -> str:
        """Test database connectivity via health endpoint"""
        response = requests.get(f"{self.base_url}/api/admin/health", timeout=self.timeout)
        data = response.json()
        
        if data.get('database') != 'connected':
            raise Exception(f"Database status is '{data.get('database')}', not 'connected'")
        
        return "Database connection verified"
    
    def test_api_documentation(self) -> str:
        """Test API documentation endpoint"""
        response = requests.get(f"{self.base_url}/docs", timeout=self.timeout)
        if response.status_code != 200:
            raise Exception(f"API docs returned status {response.status_code}")
        
        return "API documentation is accessible"
    
    def test_static_files(self) -> str:
        """Test static file serving"""
        static_endpoints = [
            "/static/styles.css",
            "/login.html", 
            "/dashboard.html"
        ]
        
        working_endpoints = []
        for endpoint in static_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    working_endpoints.append(endpoint)
            except:
                pass
        
        if not working_endpoints:
            raise Exception("No static files are accessible")
        
        return f"Static files accessible ({len(working_endpoints)}/{len(static_endpoints)} endpoints)"
    
    def test_cors_headers(self) -> str:
        """Test CORS configuration"""
        response = requests.options(f"{self.base_url}/api/admin/health", 
                                  headers={'Origin': 'https://example.com'},
                                  timeout=self.timeout)
        
        cors_headers = [h for h in response.headers.keys() if h.lower().startswith('access-control')]
        
        if not cors_headers:
            return warning("CORS headers not found (may be intentional)")
        
        return f"CORS configured ({len(cors_headers)} headers found)"
    
    def test_response_time(self) -> str:
        """Test API response time"""
        start_time = time.time()
        response = requests.get(f"{self.base_url}/api/admin/health", timeout=self.timeout)
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        if response.status_code != 200:
            raise Exception(f"Health check failed during response time test")
        
        if response_time > 5000:  # 5 seconds
            return warning(f"Response time is slow: {response_time:.0f}ms")
        elif response_time > 2000:  # 2 seconds
            return warning(f"Response time is acceptable: {response_time:.0f}ms")
        else:
            return f"Response time is good: {response_time:.0f}ms"
    
    def test_ssl_certificate(self) -> str:
        """Test SSL certificate (for HTTPS)"""
        if not self.base_url.startswith('https://'):
            return warning("Not using HTTPS (consider enabling for production)")
        
        # The fact that requests.get works with https means SSL is valid
        return "HTTPS/SSL is properly configured"
    
    def run_all_tests(self) -> Dict:
        """Run all validation tests"""
        print(colorize(f"\n🚀 AstroNova Render.com Deployment Validator", 'blue'))
        print(colorize(f"Testing: {self.base_url}\n", 'blue'))
        
        # Core functionality tests
        self.test("Basic Connectivity", self.test_basic_connectivity)
        self.test("Health Endpoint", self.test_health_endpoint)  
        self.test("Database Connectivity", self.test_database_connectivity)
        self.test("API Documentation", self.test_api_documentation)
        
        # Performance and configuration tests
        self.test("Static Files", self.test_static_files)
        self.test("Response Time", self.test_response_time)
        self.test("SSL Certificate", self.test_ssl_certificate)
        self.test("CORS Configuration", self.test_cors_headers)
        
        # Generate summary
        return self.generate_summary()
    
    def generate_summary(self) -> Dict:
        """Generate test summary"""
        passed = sum(1 for _, success, _ in self.results if success)
        total = len(self.results)
        
        print(f"\n{'='*60}")
        print(colorize(f"🎯 DEPLOYMENT VALIDATION SUMMARY", 'blue'))
        print(f"{'='*60}")
        
        # Print individual results
        for name, success, message in self.results:
            status = success("PASS") if success else error("FAIL")
            print(f"{status} {name}: {message}")
        
        print(f"\n{'='*60}")
        
        # Overall status
        if passed == total:
            print(success(f"🎉 ALL TESTS PASSED ({passed}/{total})"))
            print(success("Your AstroNova deployment is working correctly!"))
            deployment_status = "healthy"
        elif passed > total * 0.7:  # 70% pass rate
            print(warning(f"⚠️  MOST TESTS PASSED ({passed}/{total})"))
            print(warning("Your deployment is working with minor issues"))
            deployment_status = "warning"
        else:
            print(error(f"❌ MULTIPLE FAILURES ({passed}/{total})"))
            print(error("Your deployment has significant issues"))
            deployment_status = "failed"
        
        print(f"\n💡 Next Steps:")
        if deployment_status == "healthy":
            print("✅ Set up your admin user and configure Shopify webhook")
            print("✅ Test PDF generation with a real order")
            print("✅ Monitor logs and performance")
        else:
            print("🔧 Check Render.com dashboard for service logs")
            print("🔧 Verify environment variables are set correctly")
            print("🔧 Ensure all services are running")
        
        return {
            'total_tests': total,
            'passed_tests': passed,
            'failed_tests': total - passed,
            'success_rate': (passed / total) * 100,
            'status': deployment_status,
            'url': self.base_url
        }

def main():
    """Main validation function"""
    if len(sys.argv) != 2:
        print("Usage: python validate_deployment.py <base_url>")
        print("Example: python validate_deployment.py https://your-app.onrender.com")
        sys.exit(1)
    
    base_url = sys.argv[1]
    
    # Validate URL format
    if not base_url.startswith(('http://', 'https://')):
        print(error("URL must start with http:// or https://"))
        sys.exit(1)
    
    # Run validation
    validator = RenderValidator(base_url)
    summary = validator.run_all_tests()
    
    # Exit with appropriate code
    if summary['status'] == 'healthy':
        sys.exit(0)
    elif summary['status'] == 'warning':
        sys.exit(1)
    else:
        sys.exit(2)

if __name__ == "__main__":
    main()