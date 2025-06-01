from flask import Flask, jsonify, request
import os

app = Flask(__name__)

@app.route("/")
def home():
    return {"service": "resume-parser", "status": "simple version"}, 200

@app.route("/health")
def health():
    return {"status": "healthy", "service": "resume-parser"}, 200

@app.route("/metrics")
def metrics():
    return "# TYPE resume_parser_health gauge\nresume_parser_health 1\n", 200, {'Content-Type': 'text/plain'}

@app.route("/api/resume-parser/health")
def api_health():
    return {"status": "healthy", "service": "resume-parser", "endpoint": "/api/resume-parser/health"}, 200

@app.route("/api/resume-parser/metrics")
def api_metrics():
    return "# TYPE resume_parser_health gauge\nresume_parser_health 1\n", 200, {'Content-Type': 'text/plain'}

@app.route("/api/resume-parser/user-profile", methods=["POST"])
def user_profile():
    try:
        data = request.get_json()
        file_path = data.get("file_path") if data else None
        
        if not file_path:
            return {"error": "file_path parameter is required"}, 400
            
        # Return a mock response for now
        return {
            "message": "Resume parser endpoint is working", 
            "file_path": file_path,
            "status": "This is a simplified version. Full functionality will be available soon.",
            "mock_profile": {
                "name": "Sample User",
                "email": "sample@example.com", 
                "experience_years": 5,
                "skills": ["Python", "Flask", "AWS"]
            }
        }, 200
        
    except Exception as e:
        return {"error": f"Error processing request: {str(e)}"}, 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5004))
    app.run(host="0.0.0.0", port=port, debug=False)
