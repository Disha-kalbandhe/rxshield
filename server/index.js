const express = require("express");
const cors = require("cors");
require("dotenv").config();

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

// Test route
app.get("/", (req, res) => {
  res.json({
    message: "RxShield API is running 🚀",
    version: "1.0.0",
  });
});

app.listen(PORT, () => {
  console.log(`✅ RxShield server running on port ${PORT}`);
});
