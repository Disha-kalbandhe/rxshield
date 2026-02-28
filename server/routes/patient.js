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
      currentMedications,
      bloodGroup,
      weight,
      doctorId,
    } = req.body;

    const docRef = await db.collection("patients").add({
      name,
      age,
      gender,
      diagnosis,
      allergies,
      currentMedications,
      bloodGroup,
      weight,
      doctorId,
      createdAt: new Date().toISOString(),
      createdBy: req.user.uid,
    });

    res.json({ success: true, patientId: docRef.id });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/patients — get all patients for logged-in doctor
router.get("/", async (req, res) => {
  try {
    const snapshot = await db
      .collection("patients")
      .where("createdBy", "==", req.user.uid)
      .orderBy("createdAt", "desc")
      .get();

    const patients = snapshot.docs.map((doc) => ({
      id: doc.id,
      ...doc.data(),
    }));
    res.json(patients);
  } catch (err) {
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
    await db
      .collection("patients")
      .doc(req.params.id)
      .update({
        ...req.body,
        updatedAt: new Date().toISOString(),
      });

    res.json({ success: true });
  } catch (err) {
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
