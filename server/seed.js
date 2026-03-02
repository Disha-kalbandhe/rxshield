/**
 * RxShield Demo Data Seeder
 *
 * One-time script to populate Firestore with realistic demo data
 * for presentations and testing.
 *
 * Usage: node seed.js
 */

const admin = require("firebase-admin");
require("dotenv").config();

// Initialize Firebase Admin
admin.initializeApp({
  credential: admin.credential.cert({
    project_id: process.env.FIREBASE_PROJECT_ID,
    client_email: process.env.FIREBASE_CLIENT_EMAIL,
    private_key: process.env.FIREBASE_PRIVATE_KEY?.replace(/\\n/g, "\n"),
  }),
});

const db = admin.firestore();

// Demo patient data - 8 realistic Indian patients
const demoPatients = [
  {
    patient_id: "DEMO-001",
    name: "Rajesh Kumar Sharma",
    age: 58,
    gender: "Male",
    blood_group: "B+",
    weight_kg: 78,
    city: "Nashik",
    diagnosis: ["Type 2 Diabetes", "Hypertension"],
    allergies: ["Penicillin"],
    current_medications: ["Metformin", "Amlodipine"],
    comorbidities: ["Obesity"],
    phone: "9876543210",
    createdAt: new Date().toISOString(),
    isDemo: true,
  },
  {
    patient_id: "DEMO-002",
    name: "Priya Anand Deshmukh",
    age: 45,
    gender: "Female",
    blood_group: "O+",
    weight_kg: 62,
    city: "Pune",
    diagnosis: ["Hypothyroidism", "GERD"],
    allergies: ["Aspirin", "Sulfa"],
    current_medications: ["Levothyroxine", "Omeprazole"],
    comorbidities: [],
    phone: "9765432109",
    createdAt: new Date().toISOString(),
    isDemo: true,
  },
  {
    patient_id: "DEMO-003",
    name: "Mohammad Imran Khan",
    age: 67,
    gender: "Male",
    blood_group: "A+",
    weight_kg: 85,
    city: "Mumbai",
    diagnosis: ["Atrial Fibrillation", "Heart Failure"],
    allergies: [],
    current_medications: ["Warfarin", "Digoxin", "Furosemide"],
    comorbidities: ["CKD stage 2"],
    phone: "9654321098",
    createdAt: new Date().toISOString(),
    isDemo: true,
  },
  {
    patient_id: "DEMO-004",
    name: "Sunita Ramesh Patil",
    age: 34,
    gender: "Female",
    blood_group: "AB+",
    weight_kg: 55,
    city: "Nagpur",
    diagnosis: ["Asthma"],
    allergies: ["Aspirin", "Ibuprofen"],
    current_medications: ["Salbutamol"],
    comorbidities: [],
    phone: "9543210987",
    createdAt: new Date().toISOString(),
    isDemo: true,
  },
  {
    patient_id: "DEMO-005",
    name: "Anil Baburao Joshi",
    age: 72,
    gender: "Male",
    blood_group: "O-",
    weight_kg: 68,
    city: "Nashik",
    diagnosis: ["Hypertension", "Hypercholesterolemia"],
    allergies: [],
    current_medications: ["Atenolol", "Atorvastatin"],
    comorbidities: ["Smoking"],
    phone: "9432109876",
    createdAt: new Date().toISOString(),
    isDemo: true,
  },
  {
    patient_id: "DEMO-006",
    name: "Kavya Suresh Nair",
    age: 28,
    gender: "Female",
    blood_group: "B-",
    weight_kg: 52,
    city: "Bangalore",
    diagnosis: ["Bacterial Infection", "GERD"],
    allergies: ["Penicillin", "Amoxicillin"],
    current_medications: ["Omeprazole"],
    comorbidities: [],
    phone: "9321098765",
    createdAt: new Date().toISOString(),
    isDemo: true,
  },
  {
    patient_id: "DEMO-007",
    name: "Deepak Vinod Mehta",
    age: 51,
    gender: "Male",
    blood_group: "A-",
    weight_kg: 91,
    city: "Delhi",
    diagnosis: ["Type 2 Diabetes", "Hypercholesterolemia", "Hypertension"],
    allergies: [],
    current_medications: ["Metformin", "Atorvastatin", "Lisinopril"],
    comorbidities: ["Obesity", "Smoking"],
    phone: "9210987654",
    createdAt: new Date().toISOString(),
    isDemo: true,
  },
  {
    patient_id: "DEMO-008",
    name: "Meera Prakash Iyer",
    age: 63,
    gender: "Female",
    blood_group: "AB-",
    weight_kg: 59,
    city: "Chennai",
    diagnosis: ["Epilepsy"],
    allergies: ["Codeine"],
    current_medications: ["Carbamazepine"],
    comorbidities: ["Depression"],
    phone: "9109876543",
    createdAt: new Date().toISOString(),
    isDemo: true,
  },
];

/**
 * Main seeding function
 */
async function seedDemoData() {
  console.log("🌱 Starting RxShield demo data seeding...\n");

  // Seed patients
  console.log("👥 Seeding patients...");
  const batch = db.batch();

  for (const patient of demoPatients) {
    const ref = db.collection("patients").doc(patient.patient_id);
    const existing = await ref.get();
    if (!existing.exists) {
      batch.set(ref, {
        ...patient,
        createdBy: "DEMO_SEED",
        id: patient.patient_id,
      });
      console.log(`  ✅ Patient: ${patient.name}`);
    } else {
      console.log(`  ⏭️  Already exists: ${patient.name}`);
    }
  }
  await batch.commit();

  // Seed demo prescriptions (5 scenarios covering all error types)
  console.log("\n💊 Seeding demo prescriptions...");

  const demoPrescriptions = [
    {
      id: "DEMO-RX-001",
      patientId: "DEMO-001",
      prescriptionText:
        "Rx:\n1. Metformin 500mg twice daily x 30 days\n2. Amlodipine 5mg once daily\n3. Atorvastatin 20mg at night",
      extractedDrugs: [
        {
          drug_name: "Metformin",
          dose: "500 mg",
          frequency: "twice daily",
          duration: "30 days",
        },
        {
          drug_name: "Amlodipine",
          dose: "5 mg",
          frequency: "once daily",
          duration: null,
        },
        {
          drug_name: "Atorvastatin",
          dose: "20 mg",
          frequency: "once daily",
          duration: null,
        },
      ],
      errors: [],
      riskScore: 0.0,
      riskLevel: "SAFE",
      status: "clear",
      analyzedBy: "DEMO_SEED",
      createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: "DEMO-RX-002",
      patientId: "DEMO-003",
      prescriptionText:
        "Rx:\n1. Aspirin 500mg three times daily\n2. Warfarin 5mg once daily\nFor DVT",
      extractedDrugs: [
        {
          drug_name: "Aspirin",
          dose: "500 mg",
          frequency: "three times daily",
          duration: null,
        },
        {
          drug_name: "Warfarin",
          dose: "5 mg",
          frequency: "once daily",
          duration: null,
        },
      ],
      errors: [
        {
          error_type: "DDI",
          drug_a: "Aspirin",
          drug_b: "Warfarin",
          severity: "CRITICAL",
          message:
            "Aspirin + Warfarin: Major bleeding risk. Additive antiplatelet + anticoagulant effect.",
          confidence: 0.97,
        },
      ],
      riskScore: 0.95,
      riskLevel: "CRITICAL",
      status: "flagged",
      analyzedBy: "DEMO_SEED",
      createdAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: "DEMO-RX-003",
      patientId: "DEMO-001",
      prescriptionText:
        "Rx:\n1. Metformin 5000mg twice daily x 30 days\nDiagnosis: Type 2 Diabetes",
      extractedDrugs: [
        {
          drug_name: "Metformin",
          dose: "5000 mg",
          frequency: "twice daily",
          duration: "30 days",
        },
      ],
      errors: [
        {
          error_type: "DOSAGE_ERROR",
          drug: "Metformin",
          severity: "CRITICAL",
          message:
            "Dose is 10x the normal dose. Normal: 500mg, Prescribed: 5000mg",
          details: { prescribed_dose: 5000, normal_dose: 500, dose_ratio: 10 },
        },
      ],
      riskScore: 0.88,
      riskLevel: "CRITICAL",
      status: "flagged",
      analyzedBy: "DEMO_SEED",
      createdAt: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: "DEMO-RX-004",
      patientId: "DEMO-006",
      prescriptionText:
        "Rx:\n1. Amoxicillin 500mg three times daily x 7 days\nFor throat infection",
      extractedDrugs: [
        {
          drug_name: "Amoxicillin",
          dose: "500 mg",
          frequency: "three times daily",
          duration: "7 days",
        },
      ],
      errors: [
        {
          error_type: "ALLERGY",
          drug: "Amoxicillin",
          severity: "CRITICAL",
          message:
            "ALERT: Patient is allergic to Amoxicillin! (Penicillin cross-reactivity)",
          confidence: 1.0,
        },
      ],
      riskScore: 0.92,
      riskLevel: "CRITICAL",
      status: "flagged",
      analyzedBy: "DEMO_SEED",
      createdAt: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    },
    {
      id: "DEMO-RX-005",
      patientId: "DEMO-004",
      prescriptionText: "Rx:\n1. Aspirin 75mg once daily\nDiagnosis: Asthma",
      extractedDrugs: [
        {
          drug_name: "Aspirin",
          dose: "75 mg",
          frequency: "once daily",
          duration: null,
        },
      ],
      errors: [
        {
          error_type: "INDICATION_MISMATCH",
          drug: "Aspirin",
          severity: "HIGH",
          message:
            "Aspirin may worsen Asthma (Aspirin-exacerbated respiratory disease)",
          confidence: 0.84,
        },
      ],
      riskScore: 0.65,
      riskLevel: "HIGH",
      status: "flagged",
      analyzedBy: "DEMO_SEED",
      createdAt: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
    },
  ];

  for (const rx of demoPrescriptions) {
    const ref = db.collection("prescriptions").doc(rx.id);
    const existing = await ref.get();
    if (!existing.exists) {
      await ref.set(rx);
      console.log(`  ✅ Prescription: ${rx.id} (${rx.riskLevel})`);
    } else {
      console.log(`  ⏭️  Already exists: ${rx.id}`);
    }
  }

  // Seed audit log entries
  console.log("\n📋 Seeding audit log...");
  for (const rx of demoPrescriptions) {
    await db.collection("auditLog").add({
      action: "prescription_analyzed",
      prescriptionId: rx.id,
      patientId: rx.patientId,
      doctorId: "DEMO_SEED",
      errorCount: rx.errors.length,
      riskScore: rx.riskScore,
      timestamp: rx.createdAt,
    });
    console.log(`  ✅ Audit log: ${rx.id}`);
  }

  console.log("\n✅ Demo data seeding complete!");
  console.log("📊 Summary:");
  console.log(`   Patients: ${demoPatients.length}`);
  console.log(`   Prescriptions: ${demoPrescriptions.length}`);
  console.log(`   Audit logs: ${demoPrescriptions.length}`);
  console.log("\n🚀 Open your app to see demo data!");

  process.exit(0);
}

// Run the seeder
seedDemoData().catch((err) => {
  console.error("❌ Seeding failed:", err);
  process.exit(1);
});
