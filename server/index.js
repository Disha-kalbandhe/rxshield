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
    origin: function (origin, callback) {
      // Allow requests with no origin (like mobile apps or curl)
      if (!origin) return callback(null, true);

      // In development, allow any localhost origin
      if (origin.match(/^http:\/\/localhost:\d+$/)) {
        return callback(null, true);
      }

      // In production, check against environment variable
      if (process.env.CLIENT_URL && origin === process.env.CLIENT_URL) {
        return callback(null, true);
      }

      callback(new Error("Not allowed by CORS"));
    },
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
    mlApiUrl: process.env.ML_API_URL,
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
