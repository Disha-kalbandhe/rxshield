const express = require("express");
const router = express.Router();
const { db } = require("../config/firebase");
const { verifyToken } = require("../middleware/auth");

router.use(verifyToken);

// POST /api/patients — create new patient
router.post("/", async (req, res) => {
  try {
    const {
      name,
      age,
      gender,
      diagnosis,
      allergies,
      current_medications,
      blood_group,
      weight_kg,
      city,
      comorbidities,
    } = req.body;

    const patientData = {
      name,
      age: age ? parseInt(age) : null,
      gender: gender || "Male",
      diagnosis: diagnosis || [],
      allergies: allergies || [],
      current_medications: current_medications || [],
      blood_group: blood_group || "",
      weight_kg: weight_kg ? parseFloat(weight_kg) : null,
      city: city || "",
      comorbidities: comorbidities || [],
      createdAt: new Date().toISOString(),
      createdBy: req.user.uid,
    };

    const docRef = await db.collection("patients").add(patientData);

    res.json({ success: true, patientId: docRef.id });
  } catch (err) {
    console.error("[POST /api/patients] Error:", err.message);
    res.status(500).json({ error: err.message });
  }
});

// GET /api/patients — get all patients for logged-in doctor
router.get("/", async (req, res) => {
  try {
    console.log("[GET /api/patients] Request from user:", req.user?.uid);

    const snapshot = await db
      .collection("patients")
      .where("createdBy", "==", req.user.uid)
      .get();

    console.log("[GET /api/patients] Found", snapshot.docs.length, "patients");

    const patients = snapshot.docs.map((doc) => ({
      id: doc.id,
      ...doc.data(),
    }));

    // Sort by createdAt on server to avoid Firestore composite index requirement
    patients.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));

    res.json(patients);
  } catch (err) {
    console.error("[GET /api/patients] Error:", err.message);
    console.error("[GET /api/patients] Stack:", err.stack);
    res.status(500).json({ error: err.message });
  }
});

// GET /api/patients/:id — get single patient
router.get("/:id", async (req, res) => {
  try {
    const doc = await db.collection("patients").doc(req.params.id).get();

    if (!doc.exists) {
      return res.status(404).json({ error: "Patient not found" });
    }

    res.json({ id: doc.id, ...doc.data() });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// PUT /api/patients/:id — update patient
router.put("/:id", async (req, res) => {
  try {
    // Remove undefined values and prepare update data
    const updateData = Object.entries(req.body).reduce((acc, [key, value]) => {
      if (value !== undefined) {
        acc[key] = value;
      }
      return acc;
    }, {});

    await db
      .collection("patients")
      .doc(req.params.id)
      .update({
        ...updateData,
        updatedAt: new Date().toISOString(),
      });

    res.json({ success: true });
  } catch (err) {
    console.error("[PUT /api/patients/:id] Error:", err.message);
    res.status(500).json({ error: err.message });
  }
});

// DELETE /api/patients/:id — delete patient
router.delete("/:id", async (req, res) => {
  try {
    await db.collection("patients").doc(req.params.id).delete();
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
