from flask import Flask, render_template, request, jsonify, send_file
import pickle
import numpy as np
import json
import os
from fpdf import FPDF
from datetime import datetime

app = Flask(__name__)

# Load the model
try:
    with open('logistic_model.pkl', 'rb') as f:
        model_data = pickle.load(f)
        if isinstance(model_data, tuple):
            model = next((m for m in model_data if hasattr(m, 'predict')), None)
            if model is None:
                raise ValueError("Model not found in tuple.")
        else:
            model = model_data
    print("[INFO] Model loaded:", type(model))
except Exception as e:
    print(f"[ERROR] Failed to load model: {e}")
    model = None

# Load LabelEncoder
try:
    with open('label_encoder.pkl', 'rb') as f:
        label_encoder = pickle.load(f)
    print("[INFO] LabelEncoder loaded.")
except Exception as e:
    print(f"[WARN] LabelEncoder not found: {e}")
    label_encoder = None

# Load disease information
try:
    with open('templates/disease_info.json', 'r') as f:
        disease_info = json.load(f)
except Exception as e:
    print(f"[ERROR] Failed to load disease_info.json: {e}")
    disease_info = {}

# List of symptoms
symptoms = [
    'itching', 'skin_rash', 'nodal_skin_eruptions', 'continuous_sneezing', 'shivering',
    'chills', 'joint_pain', 'stomach_pain', 'acidity', 'ulcers_on_tongue', 'muscle_wasting',
    'vomiting', 'burning_micturition', 'spotting_urination', 'fatigue', 'weight_gain',
    'anxiety', 'cold_hands_and_feets', 'mood_swings', 'weight_loss', 'restlessness',
    'lethargy', 'patches_in_throat', 'irregular_sugar_level', 'cough', 'high_fever',
    'sunken_eyes', 'breathlessness', 'sweating', 'dehydration', 'indigestion',
    'headache', 'yellowish_skin', 'dark_urine', 'nausea', 'loss_of_appetite',
    'pain_behind_the_eyes', 'back_pain', 'constipation', 'abdominal_pain', 'diarrhoea',
    'mild_fever', 'yellow_urine', 'yellowing_of_eyes', 'acute_liver_failure',
    'fluid_overload', 'swelling_of_stomach', 'swelled_lymph_nodes', 'malaise',
    'blurred_and_distorted_vision', 'phlegm', 'throat_irritation', 'redness_of_eyes',
    'sinus_pressure', 'runny_nose', 'congestion', 'chest_pain', 'weakness_in_limbs',
    'fast_heart_rate', 'pain_during_bowel_movements', 'pain_in_anal_region',
    'bloody_stool', 'irritation_in_anus', 'neck_pain', 'dizziness', 'cramps', 'bruising',
    'obesity', 'swollen_legs', 'swollen_blood_vessels', 'puffy_face_and_eyes',
    'enlarged_thyroid', 'brittle_nails', 'swollen_extremeties', 'excessive_hunger',
    'extra_marital_contacts', 'drying_and_tingling_lips', 'slurred_speech', 'knee_pain',
    'hip_joint_pain', 'muscle_weakness', 'stiff_neck', 'swelling_joints',
    'movement_stiffness', 'spinning_movements', 'loss_of_balance', 'unsteadiness',
    'weakness_of_one_body_side', 'loss_of_smell', 'bladder_discomfort',
    'foul_smell_of_urine', 'continuous_feel_of_urine', 'passage_of_gases',
    'internal_itching', 'toxic_look_(typhos)', 'depression', 'irritability',
    'muscle_pain', 'altered_sensorium', 'red_spots_over_body', 'belly_pain',
    'abnormal_menstruation', 'dischromic_patches', 'watering_from_eyes',
    'increased_appetite', 'polyuria', 'family_history', 'mucoid_sputum',
    'rusty_sputum', 'lack_of_concentration', 'visual_disturbances',
    'receiving_blood_transfusion', 'receiving_unsterile_injections', 'coma',
    'stomach_bleeding', 'distention_of_abdomen', 'history_of_alcohol_consumption',
    'fluid_overload.1', 'blood_in_sputum', 'prominent_veins_on_calf', 'palpitations',
    'painful_walking', 'pus_filled_pimples', 'blackheads', 'scurring', 'skin_peeling',
    'silver_like_dusting', 'small_dents_in_nails', 'inflammatory_nails', 'blister',
    'red_sore_around_nose', 'yellow_crust_ooze'
]

@app.route('/')
def home():
    return render_template('index.html', symptoms=symptoms)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        selected_symptoms = request.form.getlist('symptoms')
        patient_name = request.form.get('patient_name', '').strip()
        print("[INFO] Selected symptoms:", selected_symptoms)

        if not selected_symptoms:
            raise ValueError("No symptoms selected.")

        input_vector = [1 if symptom in selected_symptoms else 0 for symptom in symptoms]

        raw_prediction = model.predict([input_vector])[0]
        probability = round(np.max(model.predict_proba([input_vector])) * 100, 2)

        # Decode if LabelEncoder is available
        prediction = label_encoder.inverse_transform([raw_prediction])[0] if label_encoder else str(raw_prediction)

        disease_data = disease_info.get(prediction, {
            "description": "No information available.",
            "prevention": ["No prevention tips available."],
            "medication": ["Consult a doctor for proper medication."]
        })

        pdf_path = generate_pdf_report(prediction, probability, selected_symptoms, disease_data, patient_name)

        return render_template('result.html',
                               prediction=prediction,
                               probability=probability,
                               symptoms=selected_symptoms,
                               disease_data=disease_data,
                               pdf_path=pdf_path)

    except Exception as e:
        print(f"[ERROR] Prediction failed: {e}")
        return render_template('error.html', error=f"An error occurred during prediction: {e}")

@app.route('/search_disease')
def search_disease():
    query = request.args.get('query', '').lower()
    results = []
    for disease, info in disease_info.items():
        if query in disease.lower():
            results.append({
                'name': disease,
                'description': info.get('description', ''),
                'prevention': info.get('prevention', [])
            })
    return jsonify(results)

@app.route('/download_report/<path:filename>')
def download_report(filename):
    return send_file(filename, as_attachment=True)

def generate_pdf_report(disease, probability, symptoms, disease_data, patient_name=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add logo if exists
    logo_path = 'static/images/logo.png'
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=10, y=8, w=30)
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Disease Prediction Report", ln=1, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Patient: {patient_name or 'Your Name'}", ln=1)
    pdf.cell(200, 10, f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=1)
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, "Prediction Results:", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Predicted Disease: {disease}", ln=1)
    pdf.cell(200, 10, f"Confidence: {probability}%", ln=1)
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, "Reported Symptoms:", ln=1)
    pdf.set_font("Arial", size=12)
    for symptom in symptoms:
        pdf.cell(200, 10, f"- {symptom.replace('_', ' ').title()}", ln=1)
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, "Disease Information:", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, disease_data.get('description', 'No description'))
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, "Prevention Tips:", ln=1)
    pdf.set_font("Arial", size=12)
    for tip in disease_data.get('prevention', []):
        pdf.multi_cell(0, 10, f"- {tip}")
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, "Medication:", ln=1)
    pdf.set_font("Arial", size=12)
    for med in disease_data.get('medication', []):
        pdf.multi_cell(0, 10, f"- {med}")

    os.makedirs('static/reports', exist_ok=True)
    filename = f"static/reports/{str(disease).replace(' ', '_')}_report_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    pdf.output(filename)

    return filename

if __name__ == '__main__':
    os.makedirs('static/reports', exist_ok=True)
    os.makedirs('static/images', exist_ok=True)
    os.makedirs('static/videos', exist_ok=True)
    app.run(debug=True)