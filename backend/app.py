from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import numpy as np
import smtplib
import os
import tempfile
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# SMTP Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")


def validate_email_format(email):
    """Validate email format using regex"""
    pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return re.match(pattern, email) is not None


def validate_weights(weights_str):
    """Validate weights are numeric and comma-separated"""
    try:
        weights = [float(w.strip()) for w in weights_str.split(',')]
        return weights, None
    except ValueError:
        return None, "Weights must be comma-separated numeric values"


def validate_impacts(impacts_str):
    """Validate impacts are +/- and comma-separated"""
    impacts = [i.strip() for i in impacts_str.split(',')]
    for impact in impacts:
        if impact not in ['+', '-']:
            return None, "Impacts must be comma-separated + or - values"
    return impacts, None


def perform_topsis(df, weights, impacts):
    """
    Perform TOPSIS analysis on the dataframe
    
    Args:
        df: DataFrame with first column as names, rest as criteria
        weights: List of numeric weights
        impacts: List of '+' or '-' values
    
    Returns:
        DataFrame with Topsis Score and Rank columns added
    """
    # Extract the decision matrix (all columns except the first one)
    decision_matrix = df.iloc[:, 1:].values.astype(float)
    weight_array = np.array(weights)
    
    # Step 1: Normalize the decision matrix using vector normalization
    norms = np.sqrt((decision_matrix ** 2).sum(axis=0))
    # Avoid division by zero
    norms[norms == 0] = 1
    normalized_matrix = decision_matrix / norms
    
    # Step 2: Calculate weighted normalized decision matrix
    weighted_matrix = normalized_matrix * weight_array
    
    # Step 3: Determine ideal best and ideal worst
    ideal_best = np.zeros(len(weights))
    ideal_worst = np.zeros(len(weights))
    
    for i, impact in enumerate(impacts):
        if impact == '+':
            ideal_best[i] = weighted_matrix[:, i].max()
            ideal_worst[i] = weighted_matrix[:, i].min()
        else:  # impact == '-'
            ideal_best[i] = weighted_matrix[:, i].min()
            ideal_worst[i] = weighted_matrix[:, i].max()
    
    # Step 4: Calculate Euclidean distance from ideal best and ideal worst
    distance_best = np.sqrt(((weighted_matrix - ideal_best) ** 2).sum(axis=1))
    distance_worst = np.sqrt(((weighted_matrix - ideal_worst) ** 2).sum(axis=1))
    
    # Step 5: Calculate TOPSIS score (relative closeness to ideal solution)
    # Handle case where both distances are 0
    denominator = distance_best + distance_worst
    denominator[denominator == 0] = 1
    topsis_score = distance_worst / denominator
    
    # Step 6: Rank the alternatives (higher score = better rank)
    ranks = (-topsis_score).argsort().argsort() + 1
    
    # Add results to dataframe
    result_df = df.copy()
    result_df['Topsis Score'] = np.round(topsis_score, 6)
    result_df['Rank'] = ranks.astype(int)
    
    return result_df


def send_email_with_attachment(recipient_email, result_csv_path, original_filename):
    """Send email with the result CSV attached"""
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        return False, "Email not configured. Please set SMTP credentials in environment variables."
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = 'TOPSIS Analysis Results'
        
        # Email body
        body = f"""
Hello,

Your TOPSIS analysis has been completed successfully.

Please find the result file attached. The file includes the original data with two additional columns:
- Topsis Score: The calculated TOPSIS score for each alternative
- Rank: The ranking based on the TOPSIS score (1 = best)

Original file: {original_filename}

Thank you for using the TOPSIS Web Service!

Best regards,
TOPSIS Analysis Tool
        """
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach CSV file
        with open(result_csv_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename=topsis_result.csv'
            )
            msg.attach(part)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        
        return True, "Email sent successfully"
    
    except smtplib.SMTPAuthenticationError:
        return False, "Email authentication failed. Please check SMTP credentials."
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"


@app.route("/")
def home():
    return jsonify({
        "status": "running",
        "message": "TOPSIS Backend Running",
        "endpoints": {
            "/topsis": "POST - Submit TOPSIS analysis"
        }
    })


@app.route("/topsis", methods=["POST"])
def topsis_api():
    """
    TOPSIS API endpoint
    
    Expected form data:
    - file: CSV file with data
    - weights: Comma-separated numeric weights
    - impacts: Comma-separated + or - values
    - email: Email address to send results
    """
    # Check required fields
    file = request.files.get("file")
    weights_str = request.form.get("weights", "").strip()
    impacts_str = request.form.get("impacts", "").strip()
    email = request.form.get("email", "").strip()
    
    # Validate all inputs are present
    if not file:
        return jsonify({"message": "Please upload a CSV file"}), 400
    if not weights_str:
        return jsonify({"message": "Weights are required"}), 400
    if not impacts_str:
        return jsonify({"message": "Impacts are required"}), 400
    if not email:
        return jsonify({"message": "Email is required"}), 400
    
    # Validate email format
    if not validate_email_format(email):
        return jsonify({"message": "Invalid email format"}), 400
    
    # Validate and parse weights
    weights, weights_error = validate_weights(weights_str)
    if weights_error:
        return jsonify({"message": weights_error}), 400
    
    # Validate and parse impacts
    impacts, impacts_error = validate_impacts(impacts_str)
    if impacts_error:
        return jsonify({"message": impacts_error}), 400
    
    # Check weights and impacts count match
    if len(weights) != len(impacts):
        return jsonify({
            "message": f"Number of weights ({len(weights)}) must equal number of impacts ({len(impacts)})"
        }), 400
    
    # Read and validate CSV file
    try:
        df = pd.read_csv(file)
    except Exception as e:
        return jsonify({"message": f"Error reading CSV file: {str(e)}"}), 400
    
    # Check minimum columns
    if len(df.columns) < 3:
        return jsonify({"message": "CSV file must have at least 3 columns (name + 2 criteria)"}), 400
    
    # Check weights/impacts match number of criteria columns
    num_criteria = len(df.columns) - 1
    if len(weights) != num_criteria:
        return jsonify({
            "message": f"Number of weights ({len(weights)}) must equal number of criteria columns ({num_criteria})"
        }), 400
    
    # Check numeric columns
    for col in df.columns[1:]:
        if not pd.api.types.is_numeric_dtype(df[col]):
            try:
                df[col] = pd.to_numeric(df[col])
            except:
                return jsonify({"message": f"Column '{col}' contains non-numeric values"}), 400
    
    # Perform TOPSIS analysis
    try:
        result_df = perform_topsis(df, weights, impacts)
    except Exception as e:
        return jsonify({"message": f"Error performing TOPSIS analysis: {str(e)}"}), 500
    
    # Save result to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
        result_df.to_csv(tmp.name, index=False)
        tmp_path = tmp.name
    
    try:
        # Send email with results
        original_filename = file.filename or "data.csv"
        email_sent, email_message = send_email_with_attachment(email, tmp_path, original_filename)
        
        if email_sent:
            return jsonify({
                "message": f"TOPSIS analysis completed! Results have been sent to {email}",
                "success": True
            })
        else:
            # If email fails, still inform user analysis was successful
            return jsonify({
                "message": f"TOPSIS analysis completed, but email could not be sent: {email_message}",
                "success": True,
                "email_sent": False
            })
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


if __name__ == "__main__":
    print("Starting TOPSIS Backend Server...")
    print(f"SMTP configured: {'Yes' if SENDER_EMAIL else 'No'}")
    # Use PORT from environment (Render provides this), fallback to 5000 for local dev
    port = int(os.getenv("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
