const express = require("express");
const router = express.Router();
const axios = require("axios");
const multer = require("multer");
const { verifyToken } = require("../middleware/auth");

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 5 * 1024 * 1024 },
  fileFilter: (_req, file, cb) => {
    const allowed = ["image/jpeg", "image/png", "image/webp"];
    if (allowed.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error("Only JPEG, PNG, and WebP images are allowed"));
    }
  },
});

// POST /api/ocr/extract
router.post(
  "/extract",
  verifyToken,
  upload.single("prescription_image"),
  async (req, res) => {
    try {
      if (!req.file) {
        return res.status(400).json({ error: "No image uploaded" });
      }

      const base64String = req.file.buffer.toString("base64");
      const dataUri = `data:${req.file.mimetype};base64,${base64String}`;

      try {
        const mlResponse = await axios.post(`${process.env.ML_API_URL}/ocr`, {
          image_b64: dataUri,
          language: req.body.language || "english",
        });

        res.json(mlResponse.data);
      } catch (err) {
        res.status(503).json({
          error: "OCR service unavailable",
          rawError: err.message,
        });
      }
    } catch (err) {
      res.status(500).json({ error: err.message });
    }
  },
);

module.exports = router;
