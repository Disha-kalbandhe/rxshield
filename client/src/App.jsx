import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";

import Landing from "./pages/Landing";
import Login from "./pages/Login";
import DoctorDashboard from "./pages/DoctorDashboard";
import PatientProfile from "./pages/PatientProfile";
import PharmacistPortal from "./pages/PharmacistPortal";
import AuditLog from "./pages/AuditLog";
import OCRUpload from "./pages/OCRUpload";

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DoctorDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/patients"
            element={
              <ProtectedRoute>
                <PatientProfile />
              </ProtectedRoute>
            }
          />
          <Route
            path="/patient/:id"
            element={
              <ProtectedRoute>
                <PatientProfile />
              </ProtectedRoute>
            }
          />
          <Route
            path="/pharmacist"
            element={
              <ProtectedRoute>
                <PharmacistPortal />
              </ProtectedRoute>
            }
          />
          <Route
            path="/audit-log"
            element={
              <ProtectedRoute>
                <AuditLog />
              </ProtectedRoute>
            }
          />
          <Route
            path="/ocr-upload"
            element={
              <ProtectedRoute>
                <OCRUpload />
              </ProtectedRoute>
            }
          />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
