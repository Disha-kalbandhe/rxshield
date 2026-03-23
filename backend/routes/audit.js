const express = require("express");
const router = express.Router();
const { db } = require("../config/firebase");
const { verifyToken } = require("../middleware/auth");

// GET /api/audit
router.get("/", verifyToken, async (req, res) => {
  try {
    const limit = parseInt(req.query.limit) || 50;

    let query = db
      .collection("auditLog")
      .orderBy("timestamp", "desc")
      .limit(limit);

    if (req.query.startAfter) {
      const cursorDoc = await db
        .collection("auditLog")
        .doc(req.query.startAfter)
        .get();

      if (cursorDoc.exists) {
        query = query.startAfter(cursorDoc);
      }
    }

    const snapshot = await query.get();
    const logs = snapshot.docs.map((doc) => ({ id: doc.id, ...doc.data() }));

    res.json({ logs, count: logs.length });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/audit/prescription/:prescriptionId
router.get("/prescription/:prescriptionId", verifyToken, async (req, res) => {
  try {
    const snapshot = await db
      .collection("auditLog")
      .where("prescriptionId", "==", req.params.prescriptionId)
      .orderBy("timestamp", "desc")
      .get();

    const logs = snapshot.docs.map((doc) => ({ id: doc.id, ...doc.data() }));

    res.json(logs);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
