import os

from flask import Flask, jsonify
from flask_cors import CORS
from models import init_db

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

init_db()

from routes.attendance import attendance_bp
from routes.faculty import faculty_bp
from routes.posttest import posttest_bp
from routes.pretest import pretest_bp
from routes.department import department_bp
from routes.trainee import trainee_bp
from routes.trainee_management import trainee_mgmt_bp
from routes.report import report_bp
from routes.dashboard import dashboard_bp
from routes.batch import batch_bp

app.register_blueprint(attendance_bp, url_prefix="/api/attendance")
app.register_blueprint(faculty_bp, url_prefix="/api/faculty")
app.register_blueprint(posttest_bp, url_prefix="/api/posttest")
app.register_blueprint(pretest_bp, url_prefix="/api/pretest")
app.register_blueprint(department_bp, url_prefix="/api/department")
app.register_blueprint(trainee_bp, url_prefix="/api/trainees")
app.register_blueprint(trainee_mgmt_bp, url_prefix="/api/trainee-mgmt")
app.register_blueprint(report_bp, url_prefix="/api/reports")
app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
app.register_blueprint(batch_bp, url_prefix="/api/batches")

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request"}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5001"))
    app.run(debug=True, host="0.0.0.0", port=port)
