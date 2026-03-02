import { useState, useRef } from "react";
import Layout from "../components/Layout";
import LoadingSpinner from "../components/ui/LoadingSpinner";
import RiskReport from "../components/ui/RiskReport";
import { usePrescription } from "../hooks/usePrescription";
import { ocrApi } from "../utils/api";
import {
  Upload,
  Image,
  FileText,
  X,
  CheckCircle,
  AlertCircle,
  Scan,
} from "lucide-react";
import toast from "react-hot-toast";

const OCRUpload = () => {
  const {
    loading: analyzing,
    result,
    analyzePrescription,
    reset,
  } = usePrescription();

  const [dragOver, setDragOver] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [ocrResult, setOcrResult] = useState(null);
  const [ocrLoading, setOcrLoading] = useState(false);
  const [editableText, setEditableText] = useState("");
  const [language, setLanguage] = useState("auto");
  const fileInputRef = useRef(null);

  // Handle file selection/upload
  const handleFile = (file) => {
    if (!file) return;

    const allowed = ["image/jpeg", "image/png", "image/webp", "image/jpg"];
    if (!allowed.includes(file.type)) {
      toast.error("Only JPG, PNG, WEBP images allowed");
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      toast.error("File size must be under 5MB");
      return;
    }

    setUploadedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setOcrResult(null);
    setEditableText("");
    reset();
  };

  // Drag and drop handlers
  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    handleFile(e.dataTransfer.files[0]);
  };

  // Clear uploaded file
  const clearFile = () => {
    setUploadedFile(null);
    setPreviewUrl(null);
    setOcrResult(null);
    setEditableText("");
    reset();
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  // Run OCR extraction
  const runOCR = async () => {
    if (!uploadedFile) return;

    setOcrLoading(true);
    try {
      const formData = new FormData();
      formData.append("prescription_image", uploadedFile);
      formData.append("language", language);

      const res = await ocrApi.extract(formData);
      setOcrResult(res.data);
      setEditableText(res.data.cleanedText || res.data.extractedText || "");
      toast.success(
        `✅ OCR complete! ${res.data.charCount} characters extracted`,
      );
    } catch (err) {
      toast.error(err.message || "OCR extraction failed");
    } finally {
      setOcrLoading(false);
    }
  };

  // Analyze extracted text
  const handleAnalyzeOCR = async () => {
    if (!editableText.trim()) {
      toast.error("No text to analyze");
      return;
    }

    await analyzePrescription(editableText, {
      age: 40,
      gender: "Male",
      weight_kg: 70,
      diagnosis: [],
      allergies: [],
      current_medications: [],
      comorbidities: [],
    });
  };

  // Get confidence color
  const getConfidenceColor = (confidence) => {
    if (confidence > 70) return "text-green-400";
    if (confidence > 40) return "text-yellow-400";
    return "text-red-400";
  };

  // If we have results, show the report
  if (result) {
    return (
      <Layout>
        <RiskReport result={result} onReset={reset} />
      </Layout>
    );
  }

  // Otherwise, show OCR upload page
  return (
    <Layout>
      <div className="max-w-5xl mx-auto">
        {/* HEADER */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <Scan className="text-purple-400" size={32} />
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              OCR Prescription Scanner
            </h1>
          </div>
          <p className="text-gray-500 dark:text-gray-400">
            Upload a handwritten prescription — AI extracts text automatically
          </p>
        </div>

        {/* TWO COLUMN LAYOUT */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
          {/* LEFT COLUMN — Upload Area */}
          <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <Image className="text-blue-400" size={20} />
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Upload Image
              </h2>
            </div>

            {/* Language Selector */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                Script / Language
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 text-gray-900 dark:text-white rounded-lg px-3 py-2 w-full text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="auto">Auto Detect</option>
                <option value="english">English (Handwritten)</option>
                <option value="hindi">Hindi (हिंदी)</option>
                <option value="marathi">Marathi (मराठी)</option>
                <option value="devanagari">Hindi + Marathi</option>
              </select>
            </div>

            {/* Drop Zone or Preview */}
            {!uploadedFile ? (
              <>
                <div
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all mt-4 ${
                    dragOver
                      ? "border-blue-500 bg-blue-900/20"
                      : "border-gray-300 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800/50"
                  }`}
                >
                  <Upload
                    size={48}
                    className="mx-auto text-gray-400 dark:text-gray-600 mb-3"
                  />
                  <p className="text-gray-900 dark:text-white font-medium">
                    Drop image here
                  </p>
                  <p className="text-gray-500 text-sm mt-1">
                    or click to browse
                  </p>
                  <p className="text-gray-500 dark:text-gray-600 text-xs mt-3">
                    JPG, PNG, WEBP • Max 5MB
                  </p>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={(e) => handleFile(e.target.files[0])}
                  className="hidden"
                />
              </>
            ) : (
              <>
                {/* Image Preview */}
                <div className="relative mt-4 rounded-xl overflow-hidden border border-gray-300 dark:border-gray-700">
                  <img
                    src={previewUrl}
                    alt="prescription"
                    className="w-full max-h-80 object-contain bg-white dark:bg-gray-800"
                  />
                  <button
                    onClick={clearFile}
                    className="absolute top-2 right-2 bg-red-600 hover:bg-red-700 text-white rounded-full p-1"
                  >
                    <X size={14} />
                  </button>
                </div>

                {/* File Info */}
                <div className="mt-4 flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                  <FileText size={16} />
                  <span className="font-medium text-gray-600 dark:text-gray-300">
                    {uploadedFile.name}
                  </span>
                  <span className="text-gray-500 dark:text-gray-600">
                    ({(uploadedFile.size / 1024).toFixed(1)} KB)
                  </span>
                </div>

                {/* OCR Button */}
                <button
                  onClick={runOCR}
                  disabled={ocrLoading}
                  className="w-full mt-4 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 text-white font-medium py-3 rounded-xl flex items-center justify-center gap-2 transition-colors"
                >
                  {ocrLoading ? (
                    <LoadingSpinner size="sm" />
                  ) : (
                    <Scan size={16} />
                  )}
                  {ocrLoading ? "Extracting Text..." : "Extract Text (OCR)"}
                </button>
              </>
            )}
          </div>

          {/* RIGHT COLUMN — Extracted Text */}
          <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <FileText className="text-green-400" size={20} />
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Extracted Text
              </h2>
            </div>

            {!ocrResult ? (
              /* Empty State */
              <div className="flex flex-col items-center justify-center h-64 text-center">
                <Scan
                  size={48}
                  className="text-gray-400 dark:text-gray-700 mb-3"
                />
                <p className="text-gray-500">Upload an image and click</p>
                <p className="text-gray-500">"Extract Text" to begin</p>
              </div>
            ) : (
              <>
                {/* OCR Metadata */}
                <div className="flex flex-wrap gap-2 mb-3">
                  <span className="bg-gray-100 dark:bg-gray-800 rounded px-2 py-1 text-xs text-gray-500 dark:text-gray-400">
                    Engine: {ocrResult.engine}
                  </span>
                  <span className="bg-gray-100 dark:bg-gray-800 rounded px-2 py-1 text-xs text-gray-500 dark:text-gray-400">
                    Language: {ocrResult.language}
                  </span>
                  {ocrResult.confidence && (
                    <span
                      className={`bg-gray-100 dark:bg-gray-800 rounded px-2 py-1 text-xs ${getConfidenceColor(
                        ocrResult.confidence,
                      )}`}
                    >
                      Confidence: {ocrResult.confidence.toFixed(1)}%
                    </span>
                  )}
                </div>

                {/* Editable Textarea */}
                <textarea
                  value={editableText}
                  onChange={(e) => setEditableText(e.target.value)}
                  rows={10}
                  className="w-full bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 text-gray-900 dark:text-white rounded-xl p-4 text-sm font-mono resize-none focus:outline-none focus:border-blue-500"
                  placeholder="OCR extracted text will appear here..."
                />
                <p className="text-gray-500 dark:text-gray-600 text-xs mt-1">
                  ✏️ You can edit the text before analysis
                </p>

                {/* Analyze Button */}
                <button
                  onClick={handleAnalyzeOCR}
                  disabled={analyzing || !editableText.trim()}
                  className="w-full mt-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white font-semibold py-3 rounded-xl flex items-center justify-center gap-2 transition-colors"
                >
                  {analyzing ? (
                    <LoadingSpinner size="sm" />
                  ) : (
                    <CheckCircle size={16} />
                  )}
                  {analyzing ? "Analyzing..." : "Analyze This Prescription"}
                </button>
              </>
            )}
          </div>
        </div>

        {/* HOW IT WORKS */}
        <div className="mt-8">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 text-center">
            How It Works
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Step 1 */}
            <div className="bg-gray-50/50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-800 rounded-xl p-4 text-center">
              <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold mx-auto mb-3">
                1
              </div>
              <Upload className="text-blue-400 mx-auto mb-2" size={32} />
              <h4 className="text-gray-900 dark:text-white font-semibold mb-1">
                Upload Image
              </h4>
              <p className="text-gray-500 dark:text-gray-400 text-sm">
                JPG/PNG of handwritten prescription
              </p>
            </div>

            {/* Step 2 */}
            <div className="bg-gray-50/50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-800 rounded-xl p-4 text-center">
              <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold mx-auto mb-3">
                2
              </div>
              <Scan className="text-purple-400 mx-auto mb-2" size={32} />
              <h4 className="text-gray-900 dark:text-white font-semibold mb-1">
                Extract Text
              </h4>
              <p className="text-gray-500 dark:text-gray-400 text-sm">
                AI reads text via TrOCR/Tesseract
              </p>
            </div>

            {/* Step 3 */}
            <div className="bg-gray-50/50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-800 rounded-xl p-4 text-center">
              <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold mx-auto mb-3">
                3
              </div>
              <CheckCircle className="text-green-400 mx-auto mb-2" size={32} />
              <h4 className="text-gray-900 dark:text-white font-semibold mb-1">
                Get Analysis
              </h4>
              <p className="text-gray-500 dark:text-gray-400 text-sm">
                Error detection on extracted text
              </p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default OCRUpload;
