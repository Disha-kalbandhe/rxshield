require("dotenv").config();

const express = require("express");
const cors = require("cors");

// Initialize Firebase Admin early
require("./config/firebase");

const prescriptionRoutes = require("./routes/prescription");
const patientRoutes = require("./routes/patient");
const ocrRoutes = require("./routes/ocr");
const auditRoutes = require("./routes/audit");

const app = express();
const PORT = process.env.PORT || 5000;

// ── Middleware ────────────────────────────────────────────────────────────────
app.use(
  cors({
    origin: process.env.CLIENT_URL || "http://localhost:5173",
    credentials: true,
  }),
);
app.use(express.json({ limit: "10mb" }));
app.use(express.urlencoded({ extended: true, limit: "10mb" }));

// ── Routes ────────────────────────────────────────────────────────────────────
app.use("/api/prescription", prescriptionRoutes);
app.use("/api/patients", patientRoutes);
app.use("/api/ocr", ocrRoutes);
app.use("/api/audit", auditRoutes);

// Health check
app.get("/health", (_req, res) => {
  res.json({
    status: "ok",
    service: "RxShield API",
    timestamp: new Date().toISOString(),
  });
});

// ── 404 handler ───────────────────────────────────────────────────────────────
app.use((_req, res) => {
  res.status(404).json({ error: "Route not found" });
});

// ── Global error handler ──────────────────────────────────────────────────────
// eslint-disable-next-line no-unused-vars
app.use((err, _req, res, _next) => {
  console.error(err.stack);
  res.status(500).json({ error: err.message || "Internal server error" });
});

// ── Start ─────────────────────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`✅ RxShield server running on port ${PORT}`);
});
