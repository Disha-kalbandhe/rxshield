import { useState, useEffect } from "react";
import Layout from "../components/Layout";
import RiskBadge from "../components/ui/RiskBadge";
import LoadingSpinner from "../components/ui/LoadingSpinner";
import { prescriptionApi, nodeApi } from "../utils/api";
import {
  ShieldCheck,
  CheckCircle,
  XCircle,
  Clock,
  Eye,
  MessageSquare,
  X,
} from "lucide-react";
import toast from "react-hot-toast";

const PharmacistPortal = () => {
  const [prescriptions, setPrescriptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState("flagged");
  const [reviewingId, setReviewingId] = useState(null);
  const [note, setNote] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  // Fetch prescriptions based on filter
  useEffect(() => {
    const fetchPrescriptions = async () => {
      setLoading(true);
      try {
        const res = await nodeApi.get(
          `/api/prescription/flagged?status=${filter}`,
        );
        setPrescriptions(res.data || []);
      } catch (err) {
        setPrescriptions([]);
      } finally {
        setLoading(false);
      }
    };
    fetchPrescriptions();
  }, [filter]);

  // Handle approve/reject action
  const handleAction = async (id, status) => {
    if (status === "rejected" && !note.trim()) {
      toast.error("Please add a note for rejection");
      return;
    }

    setActionLoading(true);
    try {
      await prescriptionApi.updateStatus(id, {
        status,
        pharmacistNote: note || "Reviewed by pharmacist",
      });
      toast.success(
        status === "approved"
          ? "✅ Prescription approved!"
          : "❌ Prescription rejected",
      );
      setReviewingId(null);
      setNote("");
      setPrescriptions((prev) => prev.filter((p) => p.id !== id));
    } catch (err) {
      toast.error(err.message || "Action failed");
    } finally {
      setActionLoading(false);
    }
  };

  // Get error type color
  const getErrorColor = (type) => {
    const colors = {
      DDI: "bg-orange-900/30 text-orange-300 border-orange-700/50",
      ALLERGY: "bg-red-900/30 text-red-300 border-red-700/50",
      DOSAGE_ERROR: "bg-yellow-900/30 text-yellow-300 border-yellow-700/50",
      INDICATION_MISMATCH: "bg-red-900/30 text-red-300 border-red-700/50",
      LASA: "bg-purple-900/30 text-purple-300 border-purple-700/50",
    };
    return colors[type] || "bg-gray-800 text-gray-400";
  };

  // Truncate text
  const truncate = (text, length = 150) => {
    if (!text) return "";
    return text.length > length ? text.substring(0, length) + "..." : text;
  };

  return (
    <Layout>
      <div className="max-w-5xl mx-auto">
        {/* HEADER */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <ShieldCheck className="text-green-400" size={32} />
            <h1 className="text-3xl font-bold text-white">Pharmacist Portal</h1>
          </div>
          <p className="text-gray-400">
            Review and approve flagged prescriptions
          </p>
        </div>

        {/* STATS ROW */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <Clock className="text-blue-400 mb-2" size={24} />
            <p className="text-gray-400 text-xs mb-1">Pending Review</p>
            <p className="text-white font-bold text-2xl">
              {filter === "flagged" ? prescriptions.length : "—"}
            </p>
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <CheckCircle className="text-green-400 mb-2" size={24} />
            <p className="text-gray-400 text-xs mb-1">Approved Today</p>
            <p className="text-white font-bold text-2xl">—</p>
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <XCircle className="text-red-400 mb-2" size={24} />
            <p className="text-gray-400 text-xs mb-1">Rejected Today</p>
            <p className="text-white font-bold text-2xl">—</p>
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <ShieldCheck className="text-purple-400 mb-2" size={24} />
            <p className="text-gray-400 text-xs mb-1">Total Reviewed</p>
            <p className="text-white font-bold text-2xl">—</p>
          </div>
        </div>

        {/* FILTER TABS */}
        <div className="flex gap-2 mb-6 overflow-x-auto">
          {["all", "flagged", "approved", "rejected"].map((tab) => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className={`px-4 py-2 rounded-lg font-medium text-sm whitespace-nowrap transition-colors ${
                filter === tab
                  ? "bg-blue-600 text-white"
                  : "bg-gray-900 border border-gray-800 text-gray-400 hover:text-white"
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* PRESCRIPTIONS LIST */}
        {loading ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner text="Loading prescriptions..." />
          </div>
        ) : prescriptions.length === 0 ? (
          <div className="text-center py-16 text-gray-500">
            <ShieldCheck size={48} className="mx-auto mb-4 text-gray-700" />
            <p className="text-lg font-medium text-gray-400">
              {filter === "flagged"
                ? "No flagged prescriptions"
                : `No ${filter} prescriptions`}
            </p>
            <p className="text-sm mt-2">
              {filter === "flagged"
                ? "All prescriptions are currently safe ✅"
                : ""}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {prescriptions.map((prescription) => (
              <div
                key={prescription.id}
                className="bg-gray-900 border border-gray-800 rounded-xl p-5"
              >
                {/* TOP ROW */}
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <p className="font-mono text-blue-400 font-semibold">
                      {prescription.prescriptionId || `RX-${prescription.id}`}
                    </p>
                    <p className="text-gray-500 text-sm mt-1">
                      Patient: {prescription.patientId || "Unknown"}
                    </p>
                  </div>
                  <div className="text-right">
                    <RiskBadge level={prescription.riskLevel || "MEDIUM"} />
                    <p className="text-gray-500 text-xs mt-1">
                      {prescription.timestamp
                        ? new Date(prescription.timestamp).toLocaleString()
                        : "Just now"}
                    </p>
                  </div>
                </div>

                {/* ERRORS ROW */}
                <div className="mt-3">
                  <p className="text-gray-400 text-xs font-medium mb-2">
                    Detected Issues:
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {prescription.errors && prescription.errors.length > 0 ? (
                      prescription.errors.map((error, idx) => (
                        <span
                          key={idx}
                          className={`text-xs px-2 py-1 rounded border ${getErrorColor(
                            error.error_type,
                          )}`}
                        >
                          {error.error_type}:{" "}
                          {error.drug || error.drug_a || "Issue detected"}
                        </span>
                      ))
                    ) : (
                      <span className="bg-green-900/30 text-green-300 border border-green-700/50 text-xs px-2 py-1 rounded">
                        No issues detected
                      </span>
                    )}
                  </div>
                </div>

                {/* PRESCRIPTION TEXT */}
                <div className="mt-3">
                  <div className="bg-gray-800 rounded-lg px-4 py-3">
                    <p className="text-gray-400 font-mono text-sm">
                      {truncate(
                        prescription.prescriptionText ||
                          prescription.text ||
                          "No text available",
                      )}
                    </p>
                  </div>
                </div>

                {/* ACTION ROW */}
                <div className="mt-4">
                  {reviewingId !== prescription.id ? (
                    <div className="flex flex-wrap gap-2">
                      <button
                        onClick={() => {
                          setReviewingId(prescription.id);
                          setNote("");
                        }}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
                      >
                        <Eye size={14} />
                        Review
                      </button>

                      <button
                        onClick={() =>
                          handleAction(prescription.id, "approved")
                        }
                        disabled={actionLoading}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors disabled:bg-gray-700"
                      >
                        <CheckCircle size={14} />
                        Quick Approve
                      </button>

                      <button
                        onClick={() => setReviewingId(prescription.id)}
                        className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors"
                      >
                        <XCircle size={14} />
                        Quick Reject
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {/* Note Textarea */}
                      <div>
                        <label className="block text-xs font-medium text-gray-400 mb-2 flex items-center gap-1">
                          <MessageSquare size={12} />
                          Pharmacist Note (required for rejection)
                        </label>
                        <textarea
                          value={note}
                          onChange={(e) => setNote(e.target.value)}
                          placeholder="Add pharmacist note (required for rejection)..."
                          rows={2}
                          className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:border-blue-500"
                        />
                      </div>

                      {/* Action Buttons */}
                      <div className="flex flex-wrap gap-2">
                        <button
                          onClick={() =>
                            handleAction(prescription.id, "approved")
                          }
                          disabled={actionLoading}
                          className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-700 text-white rounded-lg text-sm font-medium transition-colors"
                        >
                          {actionLoading ? (
                            <LoadingSpinner size="sm" />
                          ) : (
                            <CheckCircle size={14} />
                          )}
                          Approve
                        </button>

                        <button
                          onClick={() =>
                            handleAction(prescription.id, "rejected")
                          }
                          disabled={actionLoading}
                          className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-700 text-white rounded-lg text-sm font-medium transition-colors"
                        >
                          {actionLoading ? (
                            <LoadingSpinner size="sm" />
                          ) : (
                            <XCircle size={14} />
                          )}
                          Reject
                        </button>

                        <button
                          onClick={() => setReviewingId(null)}
                          disabled={actionLoading}
                          className="flex items-center gap-2 px-4 py-2 border border-gray-700 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg text-sm font-medium transition-colors"
                        >
                          <X size={14} />
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
};

export default PharmacistPortal;
