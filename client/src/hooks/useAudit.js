import { useState, useEffect, useCallback } from "react";
import { auditApi } from "../utils/api";
import toast from "react-hot-toast";

export const useAudit = (limit = 50) => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [count, setCount] = useState(0);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await auditApi.getAll(limit);
      setLogs(res.data.logs || []);
      setCount(res.data.count || 0);
    } catch (err) {
      toast.error("Failed to load audit logs");
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  return { logs, loading, count, refresh: fetchLogs };
};
