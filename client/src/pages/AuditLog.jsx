import { useState, useMemo } from "react";
import Layout from "../components/Layout";
import RiskBadge from "../components/ui/RiskBadge";
import LoadingSpinner from "../components/ui/LoadingSpinner";
import { useAudit } from "../hooks/useAudit";
import {
  FileText,
  Search,
  RefreshCw,
  Filter,
  Clock,
  User,
  AlertTriangle,
} from "lucide-react";

const AuditLog = () => {
  const { logs, loading, count, refresh } = useAudit(100);

  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [sortOrder, setSortOrder] = useState("desc");

  // Filtered and sorted logs
  const displayLogs = useMemo(() => {
    let filtered = logs;

    if (searchQuery) {
      filtered = filtered.filter(
        (log) =>
          log.prescriptionId
            ?.toLowerCase()
            .includes(searchQuery.toLowerCase()) ||
          log.patientId?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          log.doctorId?.toLowerCase().includes(searchQuery.toLowerCase()),
      );
    }

    if (filterType === "flagged") {
      filtered = filtered.filter((log) => log.errorCount > 0);
    } else if (filterType === "clear") {
      filtered = filtered.filter((log) => log.errorCount === 0);
    }

    filtered = [...filtered].sort((a, b) => {
      const diff = new Date(b.timestamp) - new Date(a.timestamp);
      return sortOrder === "desc" ? diff : -diff;
    });

    return filtered;
  }, [logs, searchQuery, filterType, sortOrder]);

  return (
    <Layout>
      <div className="max-w-6xl mx-auto">
        {/* HEADER ROW */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <FileText className="text-purple-400" size={32} />
            <div>
              <h1 className="text-3xl font-bold text-white flex items-center gap-2">
                Audit Log
                <span className="bg-purple-600 text-white text-sm font-semibold px-3 py-1 rounded-full">
                  Total: {count}
                </span>
              </h1>
            </div>
          </div>
          <button
            onClick={refresh}
            disabled={loading}
            className="border border-gray-700 text-gray-300 px-4 py-2 rounded-lg hover:bg-gray-800 flex items-center gap-2 text-sm font-medium transition-colors disabled:opacity-50"
          >
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>

        {/* CONTROLS ROW */}
        <div className="flex flex-wrap gap-3 mb-4">
          {/* Search Input */}
          <div className="flex-1 min-w-64 relative">
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500"
            />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by Rx ID, Patient ID, Doctor ID..."
              className="w-full bg-gray-900 border border-gray-800 rounded-xl pl-10 pr-4 py-3 text-white text-sm focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Filter Select */}
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-blue-500"
          >
            <option value="all">All Records</option>
            <option value="flagged">⚠️ Flagged Only</option>
            <option value="clear">✅ Clear Only</option>
          </select>

          {/* Sort Button */}
          <button
            onClick={() =>
              setSortOrder((prev) => (prev === "desc" ? "asc" : "desc"))
            }
            className="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3 text-white text-sm hover:bg-gray-800 transition-colors flex items-center gap-2"
          >
            <Filter size={16} />
            {sortOrder === "desc" ? "Newest First" : "Oldest First"}
          </button>
        </div>

        {/* SUMMARY STATS ROW */}
        <div className="grid grid-cols-3 gap-3 mb-6">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-3 text-center">
            <p className="text-gray-400 text-xs mb-1">Total</p>
            <p className="text-white font-bold text-xl">{displayLogs.length}</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-3 text-center">
            <p className="text-gray-400 text-xs mb-1">Flagged</p>
            <p className="text-red-400 font-bold text-xl">
              {displayLogs.filter((l) => l.errorCount > 0).length}
            </p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-3 text-center">
            <p className="text-gray-400 text-xs mb-1">Clear</p>
            <p className="text-green-400 font-bold text-xl">
              {displayLogs.filter((l) => l.errorCount === 0).length}
            </p>
          </div>
        </div>

        {/* TABLE */}
        {loading ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner text="Loading audit logs..." />
          </div>
        ) : displayLogs.length === 0 ? (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
            <FileText size={48} className="text-gray-700 mx-auto mb-3" />
            <p className="text-gray-400">No audit logs found</p>
            <p className="text-gray-600 text-sm mt-1">
              {searchQuery || filterType !== "all"
                ? "Try adjusting your filters"
                : "Logs will appear as prescriptions are analyzed"}
            </p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto bg-gray-900 border border-gray-800 rounded-xl">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-800 text-gray-400 text-sm">
                    <th className="text-left py-3 px-4 font-medium">
                      Timestamp
                    </th>
                    <th className="text-left py-3 px-4 font-medium">
                      Prescription ID
                    </th>
                    <th className="text-left py-3 px-4 font-medium">
                      Patient ID
                    </th>
                    <th className="text-left py-3 px-4 font-medium">
                      Doctor ID
                    </th>
                    <th className="text-left py-3 px-4 font-medium">Errors</th>
                    <th className="text-left py-3 px-4 font-medium">
                      Risk Score
                    </th>
                    <th className="text-left py-3 px-4 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {displayLogs.map((log, index) => (
                    <tr
                      key={log.id || index}
                      className="border-b border-gray-900 hover:bg-gray-900/50 transition-colors text-sm"
                    >
                      {/* Timestamp */}
                      <td className="py-3 px-4 text-gray-400">
                        <div className="flex items-center gap-1.5">
                          <Clock size={12} className="text-gray-600" />
                          {new Date(log.timestamp).toLocaleString("en-IN", {
                            day: "2-digit",
                            month: "short",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </div>
                      </td>

                      {/* Prescription ID */}
                      <td className="py-3 px-4">
                        <span className="font-mono text-blue-400 text-xs bg-blue-900/20 px-2 py-1 rounded">
                          {log.prescriptionId || "—"}
                        </span>
                      </td>

                      {/* Patient ID */}
                      <td className="py-3 px-4 text-gray-300">
                        {log.patientId || "—"}
                      </td>

                      {/* Doctor ID */}
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-1.5 text-gray-400">
                          <User size={12} />
                          {log.doctorId || "—"}
                        </div>
                      </td>

                      {/* Errors */}
                      <td className="py-3 px-4">
                        {log.errorCount > 0 ? (
                          <span className="flex items-center gap-1 text-orange-400">
                            <AlertTriangle size={12} />
                            {log.errorCount} issue
                            {log.errorCount > 1 ? "s" : ""}
                          </span>
                        ) : (
                          <span className="text-green-400 text-xs">
                            ✅ None
                          </span>
                        )}
                      </td>

                      {/* Risk Score */}
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${
                                log.riskScore > 0.6
                                  ? "bg-red-500"
                                  : log.riskScore > 0.3
                                    ? "bg-yellow-500"
                                    : "bg-green-500"
                              }`}
                              style={{
                                width: `${(log.riskScore || 0) * 100}%`,
                              }}
                            />
                          </div>
                          <span className="text-gray-400 text-xs">
                            {((log.riskScore || 0) * 100).toFixed(0)}%
                          </span>
                        </div>
                      </td>

                      {/* Status */}
                      <td className="py-3 px-4">
                        <RiskBadge
                          level={
                            log.errorCount === 0
                              ? "SAFE"
                              : log.riskScore > 0.6
                                ? "HIGH"
                                : "MEDIUM"
                          }
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Footer */}
            <div className="mt-4 text-center text-gray-500 text-sm">
              Showing {displayLogs.length} of {count} records
            </div>
          </>
        )}
      </div>
    </Layout>
  );
};

export default AuditLog;
