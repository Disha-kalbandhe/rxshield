import { useState } from "react";
import Layout from "../components/Layout";
import LoadingSpinner from "../components/ui/LoadingSpinner";
import { usePatients } from "../hooks/usePatients";
import {
  User,
  Plus,
  Edit2,
  Trash2,
  ChevronDown,
  ChevronUp,
  Search,
  X,
  Save,
} from "lucide-react";
import toast from "react-hot-toast";

const PatientProfile = () => {
  const {
    patients,
    loading,
    saving,
    createPatient,
    updatePatient,
    deletePatient,
  } = usePatients();

  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedId, setExpandedId] = useState(null);

  const emptyForm = {
    name: "",
    age: "",
    gender: "Male",
    blood_group: "",
    weight_kg: "",
    city: "",
    diagnosis: "",
    allergies: "",
    current_medications: "",
    comorbidities: "",
  };

  const [formData, setFormData] = useState(emptyForm);

  // Filter patients by search query
  const filteredPatients = patients.filter(
    (p) =>
      p.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.patient_id?.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  // Update form field
  const updateField = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();

    const payload = {
      ...formData,
      age: parseInt(formData.age),
      weight_kg: parseFloat(formData.weight_kg) || 70,
      diagnosis: formData.diagnosis
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      allergies: formData.allergies
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      current_medications: formData.current_medications
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      comorbidities: formData.comorbidities
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
    };

    let success;
    if (editingId) {
      success = await updatePatient(editingId, payload);
    } else {
      success = await createPatient(payload);
    }

    if (success || success !== null) {
      setShowForm(false);
      setEditingId(null);
      setFormData(emptyForm);
    }
  };

  // Handle edit patient
  const handleEdit = (patient) => {
    setFormData({
      name: patient.name || "",
      age: patient.age || "",
      gender: patient.gender || "Male",
      blood_group: patient.blood_group || "",
      weight_kg: patient.weight_kg || "",
      city: patient.city || "",
      diagnosis: (patient.diagnosis || []).join(", "),
      allergies: (patient.allergies || []).join(", "),
      current_medications: (patient.current_medications || []).join(", "),
      comorbidities: (patient.comorbidities || []).join(", "),
    });
    setEditingId(patient.id);
    setShowForm(true);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  // Handle delete patient
  const handleDelete = async (id, name) => {
    if (window.confirm(`Delete patient ${name}?`)) {
      await deletePatient(id);
    }
  };

  // Close form
  const closeForm = () => {
    setShowForm(false);
    setEditingId(null);
    setFormData(emptyForm);
  };

  return (
    <Layout>
      <div className="max-w-5xl mx-auto">
        {/* HEADER ROW */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <User className="text-blue-400" size={32} />
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                Patient Profiles
                <span className="bg-blue-600 text-white text-sm font-semibold px-3 py-1 rounded-full">
                  {patients.length}
                </span>
              </h1>
            </div>
          </div>
          <button
            onClick={() => setShowForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 text-sm font-medium transition-colors"
          >
            <Plus size={16} />
            Add Patient
          </button>
        </div>

        {/* ADD/EDIT FORM */}
        {showForm && (
          <div className="bg-gray-50 dark:bg-gray-900 border border-blue-700/50 rounded-2xl p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                {editingId ? "Edit" : "Add New"} Patient
              </h2>
              <button
                onClick={closeForm}
                className="text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* Name */}
                <div className="md:col-span-2 lg:col-span-1">
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                    Name *
                  </label>
                  <input
                    id="patient-name"
                    name="name"
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => updateField("name", e.target.value)}
                    placeholder="Patient name"
                    className="w-full bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 text-gray-900 dark:text-white text-sm focus:outline-none focus:border-blue-500"
                  />
                </div>

                {/* Age */}
                <div>
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                    Age *
                  </label>
                  <input
                    id="patient-age"
                    name="age"
                    type="number"
                    required
                    min="1"
                    max="120"
                    value={formData.age}
                    onChange={(e) => updateField("age", e.target.value)}
                    placeholder="Age"
                    className="w-full bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 text-gray-900 dark:text-white text-sm focus:outline-none focus:border-blue-500"
                  />
                </div>

                {/* Gender */}
                <div>
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                    Gender
                  </label>
                  <select
                    id="patient-gender"
                    name="gender"
                    value={formData.gender}
                    onChange={(e) => updateField("gender", e.target.value)}
                    className="w-full bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 text-gray-900 dark:text-white text-sm focus:outline-none focus:border-blue-500"
                  >
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                {/* Blood Group */}
                <div>
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                    Blood Group
                  </label>
                  <select
                    id="patient-blood-group"
                    name="blood_group"
                    value={formData.blood_group}
                    onChange={(e) => updateField("blood_group", e.target.value)}
                    className="w-full bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 text-gray-900 dark:text-white text-sm focus:outline-none focus:border-blue-500"
                  >
                    <option value="">Select</option>
                    <option value="A+">A+</option>
                    <option value="A-">A-</option>
                    <option value="B+">B+</option>
                    <option value="B-">B-</option>
                    <option value="O+">O+</option>
                    <option value="O-">O-</option>
                    <option value="AB+">AB+</option>
                    <option value="AB-">AB-</option>
                  </select>
                </div>

                {/* Weight */}
                <div>
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                    Weight (kg)
                  </label>
                  <input
                    id="patient-weight"
                    name="weight_kg"
                    type="number"
                    step="0.1"
                    value={formData.weight_kg}
                    onChange={(e) => updateField("weight_kg", e.target.value)}
                    placeholder="Weight in kg"
                    className="w-full bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 text-gray-900 dark:text-white text-sm focus:outline-none focus:border-blue-500"
                  />
                </div>

                {/* City */}
                <div>
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                    City
                  </label>
                  <input
                    id="patient-city"
                    name="city"
                    type="text"
                    value={formData.city}
                    onChange={(e) => updateField("city", e.target.value)}
                    placeholder="City"
                    className="w-full bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 text-gray-900 dark:text-white text-sm focus:outline-none focus:border-blue-500"
                  />
                </div>

                {/* Diagnosis */}
                <div className="col-span-full">
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                    Diagnosis
                  </label>
                  <input
                    id="patient-diagnosis"
                    name="diagnosis"
                    type="text"
                    value={formData.diagnosis}
                    onChange={(e) => updateField("diagnosis", e.target.value)}
                    placeholder="Type 2 Diabetes, Hypertension"
                    className="w-full bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 text-gray-900 dark:text-white text-sm focus:outline-none focus:border-blue-500"
                  />
                </div>

                {/* Allergies */}
                <div className="col-span-full">
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                    Allergies
                  </label>
                  <input
                    id="patient-allergies"
                    name="allergies"
                    type="text"
                    value={formData.allergies}
                    onChange={(e) => updateField("allergies", e.target.value)}
                    placeholder="Penicillin, Sulfa (comma separated)"
                    className="w-full bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 text-gray-900 dark:text-white text-sm focus:outline-none focus:border-blue-500"
                  />
                </div>

                {/* Current Medications */}
                <div className="col-span-full">
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                    Current Medications
                  </label>
                  <input
                    id="patient-medications"
                    name="current_medications"
                    type="text"
                    value={formData.current_medications}
                    onChange={(e) =>
                      updateField("current_medications", e.target.value)
                    }
                    placeholder="Metformin, Amlodipine"
                    className="w-full bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 text-gray-900 dark:text-white text-sm focus:outline-none focus:border-blue-500"
                  />
                </div>

                {/* Comorbidities */}
                <div className="col-span-full">
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                    Comorbidities
                  </label>
                  <input
                    id="patient-comorbidities"
                    name="comorbidities"
                    type="text"
                    value={formData.comorbidities}
                    onChange={(e) =>
                      updateField("comorbidities", e.target.value)
                    }
                    placeholder="Obesity, CKD (optional)"
                    className="w-full bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 text-gray-900 dark:text-white text-sm focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={saving}
                className="mt-6 bg-green-600 hover:bg-green-700 disabled:bg-gray-700 text-white font-medium px-6 py-2.5 rounded-lg flex items-center gap-2 transition-colors"
              >
                {saving ? <LoadingSpinner size="sm" /> : <Save size={16} />}
                {saving
                  ? "Saving..."
                  : editingId
                    ? "Update Patient"
                    : "Save Patient"}
              </button>
            </form>
          </div>
        )}

        {/* SEARCH BAR */}
        <div className="relative mb-4">
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500"
          />
          <input
            id="patient-search"
            name="search"
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by name or patient ID..."
            className="w-full bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl pl-10 pr-4 py-3 text-gray-900 dark:text-white text-sm focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* PATIENT LIST */}
        {loading ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner text="Loading patients..." />
          </div>
        ) : patients.length === 0 ? (
          <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-12 text-center">
            <User
              size={48}
              className="text-gray-400 dark:text-gray-700 mx-auto mb-3"
            />
            <p className="text-gray-500 dark:text-gray-400">No patients yet</p>
            <p className="text-gray-400 dark:text-gray-600 text-sm mt-1">
              Click "Add Patient" to create the first profile
            </p>
          </div>
        ) : filteredPatients.length === 0 ? (
          <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-12 text-center">
            <Search
              size={48}
              className="text-gray-400 dark:text-gray-700 mx-auto mb-3"
            />
            <p className="text-gray-500 dark:text-gray-400">
              No patients match your search
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredPatients.map((patient) => (
              <div
                key={patient.id}
                className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl overflow-hidden"
              >
                {/* COLLAPSED ROW */}
                <div className="px-5 py-4 flex items-center justify-between">
                  <div className="flex items-center gap-3 flex-1">
                    {/* Avatar */}
                    <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-semibold">
                      {patient.name?.charAt(0).toUpperCase()}
                    </div>

                    {/* Name & ID */}
                    <div>
                      <h3 className="text-gray-900 dark:text-white font-semibold">
                        {patient.name}
                      </h3>
                      <p className="text-gray-500 text-xs">
                        {patient.patient_id}
                      </p>
                    </div>
                  </div>

                  {/* Middle Info (hidden on mobile) */}
                  <div className="hidden md:flex items-center gap-3 flex-1">
                    <span className="bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 text-xs px-2 py-1 rounded">
                      {patient.age} yrs • {patient.gender}
                    </span>
                    {patient.diagnosis && patient.diagnosis.length > 0 && (
                      <div className="flex items-center gap-1">
                        {patient.diagnosis.slice(0, 2).map((d, i) => (
                          <span
                            key={i}
                            className="bg-purple-900/30 text-purple-300 text-xs px-2 py-1 rounded"
                          >
                            {d}
                          </span>
                        ))}
                        {patient.diagnosis.length > 2 && (
                          <span className="text-gray-500 text-xs">
                            +{patient.diagnosis.length - 2} more
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() =>
                        setExpandedId(
                          expandedId === patient.id ? null : patient.id,
                        )
                      }
                      className="text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors p-2"
                    >
                      {expandedId === patient.id ? (
                        <ChevronUp size={18} />
                      ) : (
                        <ChevronDown size={18} />
                      )}
                    </button>
                    <button
                      onClick={() => handleEdit(patient)}
                      className="text-yellow-400 hover:text-yellow-300 transition-colors p-2"
                    >
                      <Edit2 size={16} />
                    </button>
                    <button
                      onClick={() => handleDelete(patient.id, patient.name)}
                      className="text-red-400 hover:text-red-300 transition-colors p-2"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>

                {/* EXPANDED SECTION */}
                {expandedId === patient.id && (
                  <div className="border-t border-gray-200 dark:border-gray-800 px-5 py-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Allergies */}
                      <div>
                        <h4 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-2">
                          Allergies
                        </h4>
                        {patient.allergies && patient.allergies.length > 0 ? (
                          <div className="flex flex-wrap gap-2">
                            {patient.allergies.map((allergy, i) => (
                              <span
                                key={i}
                                className="bg-red-900/30 border border-red-700/50 text-red-300 text-xs px-2 py-1 rounded"
                              >
                                {allergy}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <p className="text-gray-500 dark:text-gray-600 text-sm">
                            None known
                          </p>
                        )}
                      </div>

                      {/* Current Medications */}
                      <div>
                        <h4 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-2">
                          Current Medications
                        </h4>
                        {patient.current_medications &&
                        patient.current_medications.length > 0 ? (
                          <div className="flex flex-wrap gap-2">
                            {patient.current_medications.map((med, i) => (
                              <span
                                key={i}
                                className="bg-blue-900/30 border border-blue-700/50 text-blue-300 text-xs px-2 py-1 rounded"
                              >
                                {med}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <p className="text-gray-500 dark:text-gray-600 text-sm">
                            None
                          </p>
                        )}
                      </div>

                      {/* Blood Group / Weight */}
                      <div>
                        <h4 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-2">
                          Blood Group / Weight
                        </h4>
                        <p className="text-gray-300 text-sm">
                          {patient.blood_group || "Not specified"} •{" "}
                          {patient.weight_kg || "N/A"} kg
                        </p>
                      </div>

                      {/* City / Comorbidities */}
                      <div>
                        <h4 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-2">
                          City / Comorbidities
                        </h4>
                        <p className="text-gray-600 dark:text-gray-300 text-sm">
                          {patient.city || "N/A"}
                        </p>
                        {patient.comorbidities &&
                          patient.comorbidities.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {patient.comorbidities.map((comorb, i) => (
                                <span
                                  key={i}
                                  className="bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 text-xs px-2 py-1 rounded"
                                >
                                  {comorb}
                                </span>
                              ))}
                            </div>
                          )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
};

export default PatientProfile;
