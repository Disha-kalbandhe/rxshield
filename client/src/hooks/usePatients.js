import { useState, useEffect, useCallback } from "react";
import { patientApi } from "../utils/api";
import toast from "react-hot-toast";

export const usePatients = () => {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const fetchPatients = useCallback(async () => {
    setLoading(true);
    try {
      const res = await patientApi.getAll();
      setPatients(res.data);
    } catch (err) {
      setError(err.message);
      toast.error("Failed to fetch patients");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPatients();
  }, [fetchPatients]);

  const createPatient = async (patientData) => {
    setSaving(true);
    try {
      const res = await patientApi.create(patientData);
      toast.success("✅ Patient created successfully!");
      await fetchPatients();
      return res.data;
    } catch (err) {
      toast.error(err.message || "Failed to create patient");
      return null;
    } finally {
      setSaving(false);
    }
  };

  const updatePatient = async (id, data) => {
    setSaving(true);
    try {
      await patientApi.update(id, data);
      toast.success("Patient updated!");
      await fetchPatients();
      return true;
    } catch (err) {
      toast.error(err.message || "Update failed");
      return false;
    } finally {
      setSaving(false);
    }
  };

  const deletePatient = async (id) => {
    try {
      await patientApi.delete(id);
      toast.success("Patient removed");
      await fetchPatients();
      return true;
    } catch (err) {
      toast.error(err.message || "Delete failed");
      return false;
    }
  };

  return {
    patients,
    loading,
    saving,
    error,
    fetchPatients,
    createPatient,
    updatePatient,
    deletePatient,
  };
};
