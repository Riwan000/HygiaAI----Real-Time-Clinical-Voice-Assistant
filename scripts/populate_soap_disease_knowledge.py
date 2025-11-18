#!/usr/bin/env python3
"""
Populate Knowledge Base with SOAP Report Guidelines and Disease Information

This script populates the Qdrant knowledge base with:
1. Comprehensive SOAP note documentation guidelines
2. Common disease information (symptoms, diagnosis, treatment)
3. Clinical decision support information

Run this script to build a focused knowledge base for SOAP generation and clinical insights.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.storage.qdrant_storage import QdrantStorage
from src.storage.knowledge_ingestion import KnowledgeIngestionPipeline
from src.embeddings import BioBERTEmbeddingGenerator
from src.storage.schema import KnowledgeBaseMetadata, EmbeddingType, AccessType
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Comprehensive SOAP and Disease Knowledge Base
KNOWLEDGE_BASE_CONTENT = {
    # ========== SOAP NOTE GUIDELINES ==========
    "soap_comprehensive_guide": {
        "title": "Comprehensive SOAP Note Writing Guide",
        "content": """
SOAP Note Documentation: Complete Guide

SUBJECTIVE (S) - Patient's Story:
The subjective section captures what the patient tells you in their own words.

1. Chief Complaint (CC):
   - Primary reason for visit in patient's own words
   - Usually one sentence: "I have been having chest pain for 3 days"
   - Should be direct quote when possible

2. History of Present Illness (HPI):
   Use the OLDCARTS mnemonic:
   - O: Onset - When did it start? Sudden or gradual?
   - L: Location - Where exactly? Does it radiate?
   - D: Duration - How long? Constant or intermittent?
   - C: Character - What does it feel like? Sharp, dull, burning, pressure?
   - A: Aggravating/Alleviating factors - What makes it better or worse?
   - R: Radiation - Does it spread anywhere?
   - T: Timing - When does it occur? Time of day? Related to activities?
   - S: Severity - Rate on scale of 1-10. Compare to previous episodes.

3. Review of Systems (ROS):
   - Constitutional: Fever, chills, weight loss/gain, fatigue, night sweats
   - HEENT: Headaches, vision changes, hearing loss, sore throat, nasal congestion
   - Cardiovascular: Chest pain, palpitations, shortness of breath, edema
   - Respiratory: Cough, sputum, wheezing, hemoptysis
   - GI: Nausea, vomiting, diarrhea, constipation, abdominal pain, blood in stool
   - GU: Dysuria, frequency, urgency, hematuria, incontinence
   - Musculoskeletal: Joint pain, muscle weakness, stiffness
   - Neurological: Headaches, dizziness, seizures, weakness, numbness
   - Endocrine: Polyuria, polydipsia, heat/cold intolerance
   - Skin: Rashes, itching, changes in moles

4. Past Medical History (PMH):
   - Chronic conditions: Diabetes, hypertension, heart disease
   - Surgeries: Dates and types
   - Hospitalizations: Reasons and dates
   - Psychiatric history

5. Medications:
   - Current medications with dosages and frequencies
   - Over-the-counter medications
   - Herbal supplements

6. Allergies:
   - Medications, foods, environmental
   - Type of reaction (rash, anaphylaxis, etc.)

7. Social History:
   - Smoking: Pack-years (packs/day × years)
   - Alcohol: Amount and frequency
   - Illicit drugs
   - Occupation
   - Living situation
   - Travel history (if relevant)

8. Family History:
   - Relevant hereditary conditions
   - Age and cause of death of close relatives

OBJECTIVE (O) - What You Observe and Measure:

1. Vital Signs:
   - Blood Pressure: Systolic/Diastolic (mmHg)
   - Heart Rate: Beats per minute (bpm)
   - Respiratory Rate: Breaths per minute
   - Temperature: Fahrenheit or Celsius
   - Oxygen Saturation: Percentage (SpO2)
   - Weight: kg or lbs
   - Height: cm or inches
   - BMI: Calculated from weight and height

2. General Appearance:
   - Well-appearing, ill-appearing, in distress
   - Alertness, orientation
   - Comfort level

3. Physical Examination by System:
   - HEENT: Head, eyes, ears, nose, throat examination
   - Cardiovascular: Heart sounds, murmurs, rhythm, peripheral pulses
   - Respiratory: Breath sounds, symmetry, effort, accessory muscle use
   - Abdomen: Bowel sounds, tenderness, masses, organomegaly
   - Extremities: Edema, pulses, range of motion, deformities
   - Neurological: Mental status, cranial nerves, motor, sensory, reflexes
   - Skin: Color, temperature, moisture, lesions, rashes

4. Laboratory Results:
   - Complete Blood Count (CBC)
   - Comprehensive Metabolic Panel (CMP)
   - Lipid panel
   - Other relevant labs

5. Diagnostic Tests:
   - Imaging: X-rays, CT scans, MRIs, ultrasounds
   - EKG findings
   - Other diagnostic procedures

ASSESSMENT (A) - Clinical Reasoning:

1. Primary Diagnosis:
   - Main diagnosis with ICD-10 code if known
   - Severity: Mild, moderate, severe
   - Acuity: Acute, subacute, chronic

2. Differential Diagnoses:
   - Other possible diagnoses being considered
   - Rule-out diagnoses
   - Ranked by likelihood

3. Clinical Reasoning:
   - How subjective findings support the diagnosis
   - How objective findings support the diagnosis
   - Why other diagnoses are less likely

4. Problem List:
   - All active problems
   - Chronic conditions
   - New problems identified

5. Risk Assessment:
   - Risk factors identified
   - Complications to watch for

PLAN (P) - Treatment Strategy:

1. Medications:
   - New prescriptions: Drug name, dosage, frequency, duration
   - Medication changes: What changed and why
   - Medication discontinuation: What stopped and why
   - Refills: Which medications need refills

2. Diagnostic Tests:
   - Tests ordered: Name, rationale, urgency
   - Tests scheduled: When and where
   - Follow-up on pending tests

3. Treatment Plan:
   - Specific interventions
   - Therapies prescribed
   - Procedures scheduled

4. Patient Education:
   - Condition explanation
   - Medication instructions
   - Warning signs to watch for
   - When to seek immediate care

5. Follow-up:
   - Return visit timing
   - What to monitor
   - When to call with concerns

6. Referrals:
   - Specialist referrals
   - Reason for referral
   - Urgency

7. Lifestyle Modifications:
   - Diet changes
   - Exercise recommendations
   - Smoking cessation
   - Other behavioral changes

SOAP Note Quality Checklist:
- Subjective: Complete HPI, ROS, PMH, medications, allergies
- Objective: Vital signs, relevant physical exam, labs/tests
- Assessment: Clear diagnosis with reasoning
- Plan: Specific, actionable items with follow-up
        """,
        "domain": "guidelines",
        "source": "HygiaAI_Clinical_Guide"
    },

    "soap_extraction_techniques": {
        "title": "SOAP Note Extraction Techniques from Audio/Text",
        "content": """
Extracting SOAP Information from Clinical Conversations:

SUBJECTIVE Extraction Techniques:

1. Identifying Chief Complaint:
   - Look for opening statements: "I'm here because...", "The reason I came..."
   - First complaint mentioned
   - Patient's own words are best

2. HPI Extraction:
   - Temporal markers: "For 3 days", "Since last week", "Started yesterday"
   - Location phrases: "In my chest", "On the right side", "All over"
   - Quality descriptors: "Sharp", "Dull", "Burning", "Pressure", "Throbbing"
   - Severity indicators: "Rate it 7/10", "Very painful", "Mild discomfort"
   - Aggravating factors: "Worse when I move", "Hurts more when I breathe"
   - Alleviating factors: "Better with rest", "Helps when I take ibuprofen"

3. ROS Extraction:
   - System-specific questions: "Any fever?", "Any cough?", "Any nausea?"
   - Patient responses: "Yes, I've had a fever", "No, no cough"
   - Negative responses are also important: "Denies chest pain"

4. PMH Extraction:
   - "History of", "Previous diagnosis of", "I have diabetes"
   - "Had surgery for", "Was hospitalized for"
   - Dates are helpful but not always available

5. Medication Extraction:
   - "Taking", "On", "Prescribed", "I take metformin"
   - Dosage information: "500mg twice daily", "One tablet in the morning"
   - Medication names: Brand or generic names

6. Allergy Extraction:
   - "Allergic to", "Can't take", "Reaction to"
   - Type of reaction: "Get a rash", "Swelling", "Difficulty breathing"

OBJECTIVE Extraction Techniques:

1. Vital Signs:
   - Look for numbers with units: "BP is 140/90", "Heart rate 85", "Temp 98.6"
   - Normal ranges help identify if values are abnormal
   - Context: "Blood pressure elevated at 150/95"

2. Physical Exam Findings:
   - "On examination", "Physical exam shows", "I can see"
   - Observable findings: "Appears well", "In no acute distress"
   - System-specific findings: "Heart sounds regular", "Lungs clear"
   - Abnormal findings: "Tender to palpation", "Redness noted"

3. Laboratory Results:
   - "Lab results show", "Blood work reveals", "CBC is normal"
   - Specific values: "Glucose is 180", "Hemoglobin 12.5"
   - Abnormal markers: "Elevated", "Low", "Within normal limits"

4. Diagnostic Tests:
   - "X-ray shows", "CT scan demonstrates", "EKG reveals"
   - Findings: "No acute findings", "Pneumonia visible", "Normal sinus rhythm"

ASSESSMENT Extraction Techniques:

1. Diagnosis Statements:
   - "Diagnosis is", "Impression is", "This is consistent with"
   - "Likely", "Probable", "Possible"
   - ICD-10 codes if mentioned

2. Clinical Reasoning:
   - "Given the history and exam", "Based on the findings"
   - "Supports the diagnosis of", "Indicates"
   - "Rule out", "Consider"

3. Problem List:
   - All active problems mentioned
   - Chronic conditions: "Known diabetes", "Hypertension"
   - New problems: "New diagnosis of"

PLAN Extraction Techniques:

1. Medications:
   - "Will prescribe", "Start on", "Continue", "Change to"
   - Drug names with dosages: "Metformin 500mg twice daily"
   - Duration: "For 7 days", "Until symptoms improve"

2. Diagnostic Tests:
   - "Order", "Schedule", "Obtain", "Get"
   - Test names: "Chest X-ray", "Blood work", "EKG"
   - Timing: "Today", "This week", "As soon as possible"

3. Follow-up:
   - "Return in", "Come back", "Follow up"
   - Timeframe: "2 weeks", "1 month", "As needed"
   - Conditions: "If symptoms worsen", "If no improvement"

4. Patient Education:
   - "Counseled on", "Instructed to", "Advise"
   - Topics: "Diet", "Exercise", "Medication compliance", "Warning signs"

5. Referrals:
   - "Refer to", "Consult with", "See"
   - Specialist type: "Cardiologist", "Endocrinologist"
   - Urgency: "Urgent", "Routine", "As soon as possible"

Key Phrases for SOAP Extraction:

Subjective Indicators:
- "Patient reports", "States", "Complains of"
- "History of", "Previous", "Past"
- "Taking", "On medication", "Allergic to"
- "For X days/weeks", "Since", "Started"

Objective Indicators:
- "Vital signs", "Blood pressure", "Heart rate", "Temperature"
- "On exam", "Physical examination", "Examination reveals"
- "Lab shows", "Test results", "Imaging demonstrates"
- Numbers with medical units

Assessment Indicators:
- "Diagnosis", "Impression", "Assessment"
- "Consistent with", "Suggests", "Indicates"
- "Rule out", "Consider", "Possible"

Plan Indicators:
- "Plan", "Treatment", "Will"
- "Prescribe", "Order", "Schedule"
- "Follow up", "Return", "Refer"
- "Counsel", "Instruct", "Advise"
        """,
        "domain": "guidelines",
        "source": "HygiaAI_Clinical_Guide"
    },

    # ========== DISEASE INFORMATION ==========
    "hypertension": {
        "title": "Hypertension (High Blood Pressure) - Clinical Information",
        "content": """
Hypertension: Clinical Overview

Definition:
Hypertension is defined as sustained elevation of blood pressure ≥130/80 mmHg (Stage 1) or ≥140/90 mmHg (Stage 2).

Symptoms:
- Often asymptomatic (silent killer)
- Headaches (especially morning headaches)
- Dizziness
- Shortness of breath
- Chest pain
- Visual changes
- Nosebleeds (rare)

Risk Factors:
- Age (risk increases with age)
- Family history
- Obesity
- Sedentary lifestyle
- High salt intake
- Excessive alcohol consumption
- Smoking
- Stress
- Chronic kidney disease
- Diabetes

Diagnosis:
- Blood pressure measurement: ≥130/80 mmHg on two separate occasions
- Ambulatory blood pressure monitoring (ABPM) for confirmation
- Evaluation for secondary causes if:
  - Onset before age 30
  - Resistant hypertension
  - Hypertensive crisis

Physical Examination Findings:
- Elevated blood pressure
- Fundoscopic exam: Hypertensive retinopathy (narrowing, AV nicking)
- Cardiac exam: S4 gallop, left ventricular hypertrophy
- Peripheral pulses: May be diminished
- Edema: May be present in heart failure

Laboratory Tests:
- Complete blood count (CBC)
- Comprehensive metabolic panel (CMP): Check kidney function, electrolytes
- Lipid panel: Assess cardiovascular risk
- Urinalysis: Check for proteinuria, hematuria
- EKG: Look for left ventricular hypertrophy
- Echocardiogram: If indicated

Treatment:
1. Lifestyle Modifications:
   - DASH diet (Dietary Approaches to Stop Hypertension)
   - Reduce sodium intake to <2.3g/day
   - Regular exercise: 150 minutes/week moderate intensity
   - Weight loss if overweight/obese
   - Limit alcohol: ≤1 drink/day women, ≤2 drinks/day men
   - Smoking cessation
   - Stress management

2. Medications (First-line):
   - ACE inhibitors: Lisinopril, Enalapril
   - ARBs: Losartan, Valsartan
   - Calcium channel blockers: Amlodipine, Diltiazem
   - Thiazide diuretics: Hydrochlorothiazide, Chlorthalidone

3. Combination Therapy:
   - Often requires 2+ medications
   - ACE/ARB + Diuretic
   - ACE/ARB + CCB

Target Blood Pressure:
- General population: <130/80 mmHg
- Age ≥65: <130/80 mmHg (if tolerated)
- Diabetes: <130/80 mmHg
- Chronic kidney disease: <130/80 mmHg

Follow-up:
- Every 2-4 weeks until controlled
- Then every 3-6 months
- Annual comprehensive evaluation

Complications:
- Heart disease (MI, heart failure)
- Stroke
- Kidney disease
- Vision loss
- Peripheral artery disease
- Aortic aneurysm

SOAP Note Example:
S: 55-year-old male presents with "high blood pressure check". Denies headaches, chest pain, shortness of breath. History of hypertension x5 years. Taking lisinopril 10mg daily. Denies allergies.

O: BP 145/92, HR 78, RR 16, Temp 98.6°F, O2 Sat 98%. Well-appearing. Heart: Regular rhythm, no murmurs. Lungs: Clear bilaterally. No edema.

A: Hypertension, Stage 2, uncontrolled. Medication adherence needs assessment.

P: Increase lisinopril to 20mg daily. Recheck BP in 2 weeks. Counsel on low-sodium diet, regular exercise. Return in 2 weeks for BP check.
        """,
        "domain": "cardiology",
        "source": "HygiaAI_Clinical_Guide"
    },

    "diabetes_type2": {
        "title": "Type 2 Diabetes Mellitus - Clinical Information",
        "content": """
Type 2 Diabetes Mellitus: Clinical Overview

Definition:
Type 2 diabetes is characterized by insulin resistance and relative insulin deficiency, leading to hyperglycemia.

Symptoms:
- Polyuria (increased urination)
- Polydipsia (increased thirst)
- Polyphagia (increased hunger)
- Fatigue
- Blurred vision
- Slow-healing wounds
- Frequent infections
- Tingling/numbness in hands/feet
- Weight loss (despite increased appetite)

Risk Factors:
- Age ≥45 years
- Overweight/obesity (BMI ≥25)
- Family history of diabetes
- Physical inactivity
- History of gestational diabetes
- Polycystic ovary syndrome (PCOS)
- Hypertension
- Dyslipidemia
- Prediabetes (A1C 5.7-6.4%)

Diagnosis:
- Fasting plasma glucose ≥126 mg/dL (on two occasions)
- Random plasma glucose ≥200 mg/dL with symptoms
- A1C ≥6.5%
- Oral glucose tolerance test: 2-hour glucose ≥200 mg/dL

Physical Examination Findings:
- May be overweight/obese
- Acanthosis nigricans (darkened skin folds)
- Diabetic foot: Ulcers, calluses, decreased sensation
- Retinopathy on fundoscopic exam
- Peripheral neuropathy: Decreased sensation, reflexes

Laboratory Tests:
- Fasting glucose
- A1C (glycated hemoglobin)
- Comprehensive metabolic panel
- Lipid panel
- Urinalysis: Check for proteinuria, ketones
- Microalbuminuria screening
- Thyroid function tests (if indicated)

Treatment Goals:
- A1C: <7% (individualized)
- Fasting glucose: 80-130 mg/dL
- Postprandial glucose: <180 mg/dL
- Blood pressure: <130/80 mmHg
- LDL cholesterol: <100 mg/dL (or <70 if high risk)

Treatment:
1. Lifestyle Modifications:
   - Medical nutrition therapy (carbohydrate counting)
   - Regular exercise: 150 minutes/week
   - Weight loss: 5-10% body weight
   - Smoking cessation

2. Medications (First-line):
   - Metformin: 500-2000mg daily (start low, titrate)
   - If A1C >9%: Consider dual therapy from start

3. Second-line Medications:
   - SGLT2 inhibitors: Empagliflozin, Canagliflozin
   - GLP-1 receptor agonists: Semaglutide, Liraglutide
   - DPP-4 inhibitors: Sitagliptin, Saxagliptin
   - Sulfonylureas: Glipizide, Glyburide
   - Thiazolidinediones: Pioglitazone
   - Insulin: If oral medications insufficient

Monitoring:
- A1C: Every 3-6 months
- Self-monitoring blood glucose: Frequency depends on treatment
- Annual comprehensive eye exam
- Annual foot exam
- Annual microalbuminuria screening
- Annual lipid panel

Complications:
- Microvascular: Retinopathy, nephropathy, neuropathy
- Macrovascular: Heart disease, stroke, peripheral artery disease
- Diabetic ketoacidosis (DKA) - less common in type 2
- Hyperosmolar hyperglycemic state (HHS)

SOAP Note Example:
S: 50-year-old female presents for diabetes follow-up. Reports increased thirst and urination over past month. A1C last checked 3 months ago was 7.2%. Taking metformin 1000mg twice daily. Denies hypoglycemia symptoms. Family history: Mother had diabetes.

O: BP 132/84, HR 82, RR 16, Temp 98.4°F. BMI 32. Weight 180 lbs. Acanthosis nigricans noted in neck folds. Feet: No ulcers, decreased sensation to monofilament testing. Fundoscopic exam: Mild diabetic retinopathy.

A: Type 2 diabetes mellitus, uncontrolled (A1C likely elevated). Diabetic neuropathy. Diabetic retinopathy.

P: Check A1C today. Increase metformin to 1500mg twice daily if tolerated. Counsel on diet, exercise, weight loss. Schedule ophthalmology referral. Annual foot exam completed. Return in 3 months for A1C check.
        """,
        "domain": "pathology",
        "source": "HygiaAI_Clinical_Guide"
    },

    "pneumonia": {
        "title": "Community-Acquired Pneumonia - Clinical Information",
        "content": """
Community-Acquired Pneumonia: Clinical Overview

Definition:
Pneumonia is an infection of the lung parenchyma, typically caused by bacteria, viruses, or fungi.

Symptoms:
- Cough (productive or non-productive)
- Fever and chills
- Shortness of breath
- Chest pain (pleuritic)
- Fatigue
- Malaise
- Sputum production (may be purulent)
- Hemoptysis (blood in sputum)

Risk Factors:
- Age (very young or elderly)
- Smoking
- Chronic lung disease (COPD, asthma)
- Immunocompromised state
- Alcohol abuse
- Malnutrition
- Recent viral infection
- Aspiration risk

Physical Examination Findings:
- Fever (may be absent in elderly)
- Tachypnea (increased respiratory rate)
- Tachycardia
- Decreased oxygen saturation
- Dullness to percussion (consolidation)
- Increased tactile fremitus
- Egophony ("E" to "A" change)
- Whispered pectoriloquy
- Crackles/rales
- Bronchial breath sounds
- Pleural friction rub

Laboratory Tests:
- Complete blood count: Elevated WBC, left shift
- Comprehensive metabolic panel: Check kidney function
- Blood cultures (if severe)
- Sputum culture and Gram stain
- Procalcitonin (to distinguish bacterial from viral)
- C-reactive protein (CRP)
- Arterial blood gas (if hypoxemic)

Imaging:
- Chest X-ray: Infiltrate, consolidation, pleural effusion
- CT chest: If X-ray unclear or complications suspected

Severity Assessment (CURB-65):
- C: Confusion
- U: Urea >7 mmol/L
- R: Respiratory rate ≥30
- B: Blood pressure <90/60
- 65: Age ≥65
Score 0-1: Outpatient treatment
Score 2: Consider hospitalization
Score ≥3: Hospitalization

Treatment:
1. Outpatient (Low Risk):
   - Healthy, <65 years, no comorbidities:
     * Amoxicillin 1g TID or Doxycycline 100mg BID
   - With comorbidities:
     * Amoxicillin-clavulanate 875/125mg BID + Azithromycin 500mg daily
     * OR Levofloxacin 750mg daily

2. Inpatient (Non-ICU):
   - Ceftriaxone 1-2g IV daily + Azithromycin 500mg IV daily
   - OR Levofloxacin 750mg IV daily

3. Inpatient (ICU):
   - Beta-lactam (Ceftriaxone, Cefotaxime) + Azithromycin
   - OR Beta-lactam + Respiratory fluoroquinolone

Duration:
- Typically 5-7 days
- May extend to 10-14 days for severe cases
- Follow clinical response

Supportive Care:
- Oxygen therapy if hypoxemic
- Hydration
- Antipyretics (acetaminophen, ibuprofen)
- Rest

Follow-up:
- Clinical improvement expected in 48-72 hours
- Repeat chest X-ray if no improvement or worsening
- Consider alternative diagnosis if not responding

Complications:
- Pleural effusion/empyema
- Lung abscess
- Respiratory failure
- Sepsis
- ARDS (Acute Respiratory Distress Syndrome)

SOAP Note Example:
S: 45-year-old male presents with "cough and fever for 3 days". Reports productive cough with yellow sputum, fever up to 101°F, chills, shortness of breath, and right-sided chest pain worse with deep breathing. Denies recent travel. Smokes 1 pack/day x20 years. No known drug allergies.

O: BP 128/78, HR 98, RR 24, Temp 101.2°F, O2 Sat 94% on room air. Appears ill, in mild respiratory distress. Lungs: Decreased breath sounds and dullness to percussion right lower lobe, crackles and egophony present. Heart: Regular rhythm, no murmurs.

A: Community-acquired pneumonia, right lower lobe. CURB-65 score 0 (outpatient appropriate).

P: Chest X-ray ordered. Start amoxicillin-clavulanate 875/125mg BID + azithromycin 500mg daily x7 days. Acetaminophen 650mg Q6H for fever. Counsel on smoking cessation. Return if symptoms worsen or no improvement in 48 hours. Follow-up in 1 week.
        """,
        "domain": "pathology",
        "source": "HygiaAI_Clinical_Guide"
    },

    "asthma": {
        "title": "Asthma - Clinical Information",
        "content": """
Asthma: Clinical Overview

Definition:
Asthma is a chronic inflammatory airway disease characterized by reversible airway obstruction, bronchial hyperresponsiveness, and inflammation.

Symptoms:
- Wheezing
- Shortness of breath
- Chest tightness
- Cough (often worse at night or early morning)
- Exercise-induced symptoms
- Symptoms triggered by:
  * Allergens (pollen, dust mites, pet dander)
  * Respiratory infections
  * Exercise
  * Cold air
  * Stress/emotions
  * Medications (aspirin, NSAIDs, beta-blockers)

Risk Factors:
- Family history of asthma or allergies
- Atopy (allergic rhinitis, eczema)
- Exposure to tobacco smoke (especially in childhood)
- Obesity
- Occupational exposures
- Viral respiratory infections in childhood

Physical Examination Findings:
- May be normal between attacks
- During exacerbation:
  * Wheezing (expiratory > inspiratory)
  * Prolonged expiratory phase
  * Tachypnea
  * Use of accessory muscles
  * Hyperinflation
  * Tachycardia
  * Pulsus paradoxus (in severe cases)

Diagnostic Tests:
- Spirometry: FEV1/FVC <0.70, improvement with bronchodilator
- Peak expiratory flow (PEF): Variability >20%
- Methacholine challenge: If spirometry normal
- Allergy testing: Identify triggers
- Chest X-ray: Usually normal, rule out other causes

Asthma Severity Classification:
1. Intermittent:
   - Symptoms ≤2 days/week
   - Nighttime awakenings ≤2/month
   - SABA use ≤2 days/week
   - Normal FEV1 between attacks

2. Mild Persistent:
   - Symptoms >2 days/week but not daily
   - Nighttime awakenings 3-4/month
   - SABA use >2 days/week
   - FEV1 ≥80% predicted

3. Moderate Persistent:
   - Daily symptoms
   - Nighttime awakenings >1/week but not nightly
   - Daily SABA use
   - FEV1 60-80% predicted

4. Severe Persistent:
   - Symptoms throughout day
   - Frequent nighttime awakenings
   - SABA use several times/day
   - FEV1 <60% predicted

Treatment:
1. Quick-Relief (Rescue) Medications:
   - Short-acting beta-agonists (SABA): Albuterol, Levalbuterol
   - Anticholinergics: Ipratropium (often combined with SABA)

2. Long-Term Control Medications:
   - Inhaled corticosteroids (ICS): Fluticasone, Budesonide
   - Long-acting beta-agonists (LABA): Salmeterol, Formoterol (always with ICS)
   - Leukotriene modifiers: Montelukast
   - Theophylline
   - Biologics: For severe asthma (omalizumab, mepolizumab)

Stepwise Treatment Approach:
- Step 1 (Intermittent): SABA PRN
- Step 2 (Mild Persistent): Low-dose ICS
- Step 3 (Moderate Persistent): Medium-dose ICS or Low-dose ICS+LABA
- Step 4 (Moderate-Severe): Medium-dose ICS+LABA
- Step 5 (Severe): High-dose ICS+LABA + consider biologics
- Step 6 (Severe): High-dose ICS+LABA + oral corticosteroids + biologics

Asthma Action Plan:
- Green Zone (Well-controlled): No symptoms, use controller meds
- Yellow Zone (Caution): Symptoms increasing, increase controller or add SABA
- Red Zone (Danger): Severe symptoms, use SABA immediately, seek care

Patient Education:
- Proper inhaler technique
- Avoid triggers
- Recognize early warning signs
- When to seek emergency care
- Importance of controller medications

SOAP Note Example:
S: 30-year-old female presents with "asthma acting up". Reports increased wheezing and shortness of breath for past 2 days, worse at night. Using albuterol inhaler 3-4 times daily (usually 1-2 times/week). Denies fever, chest pain. History of asthma since childhood. Allergic to pollen, dust mites. Taking fluticasone inhaler daily.

O: BP 118/72, HR 88, RR 20, Temp 98.6°F, O2 Sat 96% on room air. Mild expiratory wheezing bilaterally, no accessory muscle use. Lungs: Prolonged expiratory phase, otherwise clear. Heart: Regular rhythm.

A: Asthma exacerbation, moderate persistent. Poorly controlled.

P: Increase fluticasone to twice daily. Continue albuterol PRN. Add montelukast 10mg daily. Review inhaler technique. Counsel on trigger avoidance. Return in 2 weeks for reassessment. Consider step-up therapy if not improved.
        """,
        "domain": "pathology",
        "source": "HygiaAI_Clinical_Guide"
    },

    "copd": {
        "title": "Chronic Obstructive Pulmonary Disease (COPD) - Clinical Information",
        "content": """
Chronic Obstructive Pulmonary Disease (COPD): Clinical Overview

Definition:
COPD is a progressive lung disease characterized by persistent airflow limitation, typically caused by chronic bronchitis and/or emphysema.

Symptoms:
- Chronic cough (often productive)
- Sputum production (mucoid or purulent)
- Dyspnea (shortness of breath) - progressive, worse with exertion
- Wheezing
- Chest tightness
- Fatigue
- Weight loss (in advanced disease)
- Frequent respiratory infections

Risk Factors:
- Smoking (primary risk factor)
- Age (usually >40 years)
- Occupational exposures (dust, chemicals)
- Air pollution
- Alpha-1 antitrypsin deficiency (genetic)
- History of childhood respiratory infections

Physical Examination Findings:
- Barrel chest (hyperinflation)
- Pursed-lip breathing
- Use of accessory muscles
- Decreased breath sounds
- Wheezing
- Prolonged expiratory phase
- Cyanosis (in advanced disease)
- Peripheral edema (if cor pulmonale)
- Clubbing (rare, consider other diagnoses)

Diagnostic Tests:
- Spirometry: FEV1/FVC <0.70 (post-bronchodilator)
- Chest X-ray: Hyperinflation, flattened diaphragms, bullae
- CT chest: More detailed assessment
- Alpha-1 antitrypsin level: If early onset or family history
- Arterial blood gas: If hypoxemic or advanced disease

COPD Severity (GOLD Criteria):
- GOLD 1 (Mild): FEV1 ≥80% predicted
- GOLD 2 (Moderate): FEV1 50-79% predicted
- GOLD 3 (Severe): FEV1 30-49% predicted
- GOLD 4 (Very Severe): FEV1 <30% predicted

Treatment:
1. Smoking Cessation:
   - Most important intervention
   - Counseling, medications (varenicline, bupropion, nicotine replacement)

2. Bronchodilators:
   - Short-acting (SABA/SAMA): Albuterol, Ipratropium
   - Long-acting (LABA/LAMA): Salmeterol, Tiotropium, Umeclidinium

3. Inhaled Corticosteroids:
   - Combined with LABA for frequent exacerbations
   - Not for all patients

4. Oxygen Therapy:
   - If SpO2 ≤88% or PaO2 ≤55 mmHg
   - Continuous if severe, ambulatory if needed

5. Pulmonary Rehabilitation:
   - Exercise training
   - Education
   - Nutritional counseling

6. Vaccinations:
   - Annual influenza vaccine
   - Pneumococcal vaccines

7. Medications for Exacerbations:
   - Systemic corticosteroids
   - Antibiotics (if purulent sputum)
   - Increased bronchodilators

Complications:
- Respiratory failure
- Cor pulmonale (right heart failure)
- Pneumonia
- Pneumothorax
- Depression/anxiety

SOAP Note Example:
S: 65-year-old male with COPD presents for follow-up. Reports increased shortness of breath over past month, now with minimal exertion. Chronic productive cough, yellow sputum. Using albuterol inhaler more frequently. Smokes 1 pack/day x40 years. History of 2 COPD exacerbations in past year.

O: BP 142/88, HR 92, RR 22, Temp 98.4°F, O2 Sat 90% on room air. Barrel chest, pursed-lip breathing, using accessory muscles. Lungs: Decreased breath sounds bilaterally, expiratory wheezing, prolonged expiratory phase. No peripheral edema.

A: COPD, GOLD 3 (Severe), with exacerbation. Continued smoking.

P: Start tiotropium 18mcg daily (long-acting bronchodilator). Prednisone 40mg daily x5 days for exacerbation. Consider azithromycin if sputum remains purulent. Strongly counsel on smoking cessation - offer varenicline. Check SpO2 - consider oxygen if <88%. Pulmonary rehabilitation referral. Return in 1 week for reassessment.
        """,
        "domain": "pathology",
        "source": "HygiaAI_Clinical_Guide"
    },

    "heart_failure": {
        "title": "Heart Failure - Clinical Information",
        "content": """
Heart Failure: Clinical Overview

Definition:
Heart failure is a complex clinical syndrome resulting from structural or functional impairment of ventricular filling or ejection of blood.

Symptoms:
- Dyspnea (shortness of breath):
  * At rest (advanced)
  * With exertion
  * Orthopnea (worse when lying flat)
  * Paroxysmal nocturnal dyspnea (PND)
- Fatigue and weakness
- Exercise intolerance
- Edema (peripheral, especially legs/ankles)
- Weight gain (fluid retention)
- Nocturia (frequent urination at night)
- Abdominal distension (ascites)
- Anorexia

Risk Factors:
- Coronary artery disease (most common)
- Hypertension
- Diabetes
- Obesity
- Valvular heart disease
- Cardiomyopathy
- Arrhythmias (especially atrial fibrillation)
- Alcohol abuse
- Chemotherapy (cardiotoxic)
- Family history

Physical Examination Findings:
- Tachycardia or irregular rhythm
- Elevated jugular venous pressure (JVP)
- S3 gallop (ventricular gallop)
- Rales/crackles (pulmonary edema)
- Peripheral edema (pitting)
- Hepatomegaly
- Ascites
- Cool extremities (if low cardiac output)
- Cyanosis (if severe)

Diagnostic Tests:
- BNP or NT-proBNP: Elevated (helps diagnose and assess severity)
- EKG: May show arrhythmias, previous MI, left ventricular hypertrophy
- Chest X-ray: Cardiomegaly, pulmonary edema, pleural effusions
- Echocardiogram: Assess ejection fraction, wall motion, valvular function
- Complete blood count, comprehensive metabolic panel
- Lipid panel

Heart Failure Classification:
1. NYHA Class I: No limitation, ordinary activity doesn't cause symptoms
2. NYHA Class II: Slight limitation, comfortable at rest, ordinary activity causes symptoms
3. NYHA Class III: Marked limitation, comfortable at rest, less than ordinary activity causes symptoms
4. NYHA Class IV: Unable to carry out any activity without symptoms, symptoms at rest

Types:
- Heart Failure with Reduced Ejection Fraction (HFrEF): EF <40%
- Heart Failure with Preserved Ejection Fraction (HFpEF): EF ≥50%

Treatment (HFrEF):
1. ACE Inhibitors or ARBs:
   - First-line unless contraindicated
   - Examples: Lisinopril, Enalapril, Losartan

2. Beta-Blockers:
   - Carvedilol, Metoprolol, Bisoprolol
   - Start low, titrate up

3. Diuretics:
   - Loop diuretics: Furosemide, Bumetanide
   - For fluid overload

4. Aldosterone Antagonists:
   - Spironolactone, Eplerenone
   - For moderate-severe HFrEF

5. ARNI (Angiotensin Receptor-Neprilysin Inhibitor):
   - Sacubitril/Valsartan
   - Alternative to ACE/ARB

6. SGLT2 Inhibitors:
   - Empagliflozin, Dapagliflozin
   - Newer addition, shown to reduce hospitalizations

Lifestyle Modifications:
- Low-sodium diet (<2g/day)
- Fluid restriction if severe (1.5-2L/day)
- Daily weight monitoring
- Regular exercise (cardiac rehabilitation)
- Smoking cessation
- Limit alcohol
- Vaccinations (influenza, pneumococcal)

Monitoring:
- Daily weights
- Symptoms (dyspnea, edema)
- Blood pressure
- Kidney function
- Electrolytes (especially potassium)

SOAP Note Example:
S: 70-year-old male with heart failure presents with "shortness of breath getting worse". Reports dyspnea with minimal exertion, orthopnea requiring 3 pillows, and leg swelling. Gained 5 pounds in past week. History of MI 5 years ago, hypertension, diabetes. Taking lisinopril 10mg daily, metoprolol 25mg BID, furosemide 40mg daily.

O: BP 138/88, HR 88 (irregular), RR 24, Temp 98.2°F, O2 Sat 92% on room air. JVP elevated at 8cm. S3 gallop present. Lungs: Bibasilar rales. Heart: Irregularly irregular rhythm, no murmurs. Extremities: 2+ pitting edema bilaterally to knees. Weight: 185 lbs (up from 180 lbs last week).

A: Heart failure exacerbation, NYHA Class III. Atrial fibrillation. Fluid overload.

P: Increase furosemide to 80mg daily. Check BNP, EKG, CMP today. Continue lisinopril and metoprolol. Strict low-sodium diet (<2g/day). Fluid restriction 1.5L/day. Daily weights. Return in 1 week or sooner if symptoms worsen. Consider cardiology referral if not improved.
        """,
        "domain": "cardiology",
        "source": "HygiaAI_Clinical_Guide"
    }
}


def populate_knowledge_base():
    """Populate Qdrant knowledge base with SOAP and disease information"""
    
    print("=" * 80)
    print("  Populate Knowledge Base: SOAP Reports & Disease Information")
    print("=" * 80)
    print()
    
    # Initialize Qdrant storage - use clinical_kb_collection
    qdrant_url = os.getenv("QDRANT_URL")
    if qdrant_url:
        knowledge_storage = QdrantStorage(
            url=qdrant_url,
            api_key=os.getenv("QDRANT_API_KEY"),
            collection_name="clinical_kb_collection",  # Use new collection name
            vector_size=768,
            enable_encryption=False,
            enable_deidentification=False
        )
        print(f"✓ Connected to Qdrant Cloud: {qdrant_url}")
    else:
        knowledge_storage = QdrantStorage(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6334")),
            api_key=os.getenv("QDRANT_API_KEY"),
            collection_name="clinical_kb_collection",  # Use new collection name
            vector_size=768,
            enable_encryption=False,
            enable_deidentification=False
        )
        print(f"✓ Connected to Qdrant Local: {os.getenv('QDRANT_HOST', 'localhost')}:{os.getenv('QDRANT_PORT', '6334')}")
    
    # Initialize embedding generator
    print("Initializing embedding generator...")
    embedder = BioBERTEmbeddingGenerator()
    
    # Initialize ingestion pipeline
    ingestion_pipeline = KnowledgeIngestionPipeline(
        qdrant_storage=knowledge_storage,
        text_embedding_generator=lambda text: embedder.generate_embedding(text),
        chunk_size=512,
        chunk_overlap=50,
        enforce_open_access=False  # Allow user-uploaded content
    )
    
    print()
    print(f"📚 Processing {len(KNOWLEDGE_BASE_CONTENT)} documents...")
    print()
    
    ingested_count = 0
    total_chunks = 0
    
    for doc_id, doc_data in KNOWLEDGE_BASE_CONTENT.items():
        print(f"📄 Processing: {doc_data['title']}")
        print(f"   Domain: {doc_data['domain']}")
        
        try:
            document = {
                "title": doc_data["title"],
                "text": doc_data["content"],
                "content": doc_data["content"],
                "source": doc_data.get("source", "HygiaAI_Clinical_Guide"),
                "domain": doc_data["domain"],
                "year": datetime.now(timezone.utc).year,
                "provenance_url": f"https://hygiaai.internal/knowledge/{doc_id}",
                "author": "HygiaAI Clinical Team",
                "version": "1.0"
            }
            
            metadata = KnowledgeBaseMetadata(
                title=doc_data["title"],
                source=doc_data.get("source", "HygiaAI_Clinical_Guide"),
                domain=doc_data["domain"],
                year=datetime.now(timezone.utc).year,
                embedding_type=EmbeddingType.TEXT,
                access_type=AccessType.OPEN,
                provenance_url=f"https://hygiaai.internal/knowledge/{doc_id}",
                author="HygiaAI Clinical Team",
                version="1.0"
            )
            
            point_ids = ingestion_pipeline.ingest_document(
                document,
                metadata=metadata,
                force_update=False
            )
            
            if point_ids:
                ingested_count += 1
                total_chunks += len(point_ids)
                print(f"   ✅ Ingested successfully ({len(point_ids)} chunks)")
            else:
                print(f"   ⚠️  Already exists, skipped")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    # Summary
    print("=" * 80)
    print("  Summary")
    print("=" * 80)
    print(f"✅ Documents processed: {len(KNOWLEDGE_BASE_CONTENT)}")
    print(f"✅ Documents ingested: {ingested_count}")
    print(f"✅ Total chunks created: {total_chunks}")
    print()
    print("Knowledge base now contains:")
    print("  • Comprehensive SOAP note writing guidelines")
    print("  • SOAP extraction techniques from audio/text")
    print("  • Disease information (Hypertension, Diabetes, Pneumonia, Asthma, COPD, Heart Failure)")
    print()
    print("Ready for use in:")
    print("  • Enhanced SOAP note generation")
    print("  • Clinical decision support")
    print("  • RAG-based clinical insights")
    print("=" * 80)


if __name__ == "__main__":
    try:
        populate_knowledge_base()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

