import { Fragment, useEffect, useState } from 'react';
import { auditAPI } from '../api/client';

const RISK_COLORS = { LOW: '#22c55e', MEDIUM: '#eab308', HIGH: '#f97316', CRITICAL: '#ef4444' };

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    auditAPI.logs().then((res) => setLogs(res.data));
  }, []);

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold">Audit Logs</h1>
        <p className="text-gray-500">Complete record of AI interactions and DLP actions</p>
      </div>

      <div className="card overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-shield-700/50 text-gray-400 text-left">
                <th className="px-6 py-3 font-medium">Timestamp</th>
                <th className="px-6 py-3 font-medium">User</th>
                <th className="px-6 py-3 font-medium">Prompt</th>
                <th className="px-6 py-3 font-medium">Risk</th>
                <th className="px-6 py-3 font-medium">Action</th>
                <th className="px-6 py-3 font-medium">Source</th>
                <th className="px-6 py-3 font-medium">Leak</th>
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                    No audit logs yet. Use AI Chat to generate events.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <Fragment key={log.id}>
                    <tr
                      onClick={() => setExpanded(expanded === log.id ? null : log.id)}
                      className="border-b border-shield-700/30 hover:bg-shield-800/50 cursor-pointer transition-colors"
                    >
                      <td className="px-6 py-3 text-gray-400 whitespace-nowrap">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td className="px-6 py-3">
                        <div>{log.user_email}</div>
                        <div className="text-xs text-gray-500 capitalize">{log.user_role.replace('_', ' ')}</div>
                      </td>
                      <td className="px-6 py-3 max-w-xs truncate">{log.prompt}</td>
                      <td className="px-6 py-3">
                        <span
                          className="text-xs px-2 py-0.5 rounded-full font-medium"
                          style={{
                            background: `${RISK_COLORS[log.risk_level]}20`,
                            color: RISK_COLORS[log.risk_level],
                          }}
                        >
                          {log.risk_level}
                        </span>
                      </td>
                      <td className="px-6 py-3 capitalize">{log.action}</td>
                      <td className="px-6 py-3 text-gray-400">{log.matched_source}</td>
                      <td className="px-6 py-3">
                        {log.leak_detected ? (
                          <span className="text-red-400">Yes</span>
                        ) : (
                          <span className="text-green-400">No</span>
                        )}
                      </td>
                    </tr>
                    {expanded === log.id && (
                      <tr className="bg-shield-800/30">
                        <td colSpan={7} className="px-6 py-4 space-y-2">
                          <div>
                            <span className="text-xs text-gray-500">AI Response:</span>
                            <p className="text-sm mt-1">{log.ai_response}</p>
                          </div>
                          <div>
                            <span className="text-xs text-gray-500">Final Response:</span>
                            <p className="text-sm mt-1">{log.final_response}</p>
                          </div>
                          <div className="text-xs text-gray-500">
                            Similarity: {(log.similarity_score * 100).toFixed(1)}% · Score: {log.risk_score}
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
