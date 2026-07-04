import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import {
  Activity,
  AlertTriangle,
  Ban,
  Eye,
  Shield,
  TrendingUp,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { useAuth } from '../context/AuthContext';
import { dashboardAPI } from '../api/client';

const RISK_COLORS = { LOW: '#22c55e', MEDIUM: '#eab308', HIGH: '#f97316', CRITICAL: '#ef4444' };

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [activities, setActivities] = useState([]);
  const [topSources, setTopSources] = useState([]);

  if (user?.role === 'employee') return <Navigate to="/chat" replace />;

  useEffect(() => {
    Promise.all([
      dashboardAPI.stats(),
      dashboardAPI.activities(),
      dashboardAPI.topSources(),
    ]).then(([s, a, t]) => {
      setStats(s.data);
      setActivities(a.data);
      setTopSources(t.data);
    });
  }, []);

  if (!stats) {
    return (
      <div className="p-8 flex items-center justify-center h-full">
        <div className="animate-spin w-8 h-8 border-2 border-shield-accent border-t-transparent rounded-full" />
      </div>
    );
  }

  const riskData = Object.entries(stats.risk_distribution).map(([name, value]) => ({
    name,
    value,
    color: RISK_COLORS[name],
  }));

  const statCards = [
    { label: 'Total Requests', value: stats.total_requests, icon: Activity, color: 'text-blue-400' },
    { label: 'Leaks Detected', value: stats.leaks_detected, icon: AlertTriangle, color: 'text-orange-400' },
    { label: 'Blocked Responses', value: stats.blocked_responses, icon: Ban, color: 'text-red-400' },
    { label: 'Masked Responses', value: stats.masked_responses, icon: Eye, color: 'text-yellow-400' },
    { label: 'Human Review', value: stats.human_review_pending, icon: Shield, color: 'text-purple-400' },
    { label: 'Connected Sources', value: stats.connected_sources, icon: TrendingUp, color: 'text-green-400' },
  ];

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold">Security Dashboard</h1>
        <p className="text-gray-500">Singam Technologies · AI Security Operations Center</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        {statCards.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="card">
            <div className="flex items-center justify-between mb-2">
              <Icon className={`w-5 h-5 ${color}`} />
            </div>
            <p className="text-2xl font-bold">{value}</p>
            <p className="text-xs text-gray-500 mt-1">{label}</p>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-6 mb-8">
        <div className="card">
          <h3 className="font-semibold mb-4">Risk Distribution</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={riskData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                paddingAngle={3}
              >
                {riskData.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: '#1a2236', border: '1px solid #243049', borderRadius: 8 }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-3 justify-center mt-2">
            {riskData.map((r) => (
              <span key={r.name} className="flex items-center gap-1.5 text-xs text-gray-400">
                <span className="w-2 h-2 rounded-full" style={{ background: r.color }} />
                {r.name}: {r.value}
              </span>
            ))}
          </div>
        </div>

        <div className="card">
          <h3 className="font-semibold mb-4">Top Sensitive Sources</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={topSources}>
              <XAxis dataKey="source" tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: '#1a2236', border: '1px solid #243049', borderRadius: 8 }}
              />
              <Bar dataKey="alerts" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <h3 className="font-semibold mb-4">Recent Activities</h3>
        {activities.length === 0 ? (
          <p className="text-gray-500 text-sm">No activity yet. Try the AI Chat to generate audit events.</p>
        ) : (
          <div className="space-y-3">
            {activities.map((a) => (
              <div
                key={a.id}
                className="flex items-center justify-between py-3 border-b border-shield-700/30 last:border-0"
              >
                <div>
                  <p className="text-sm font-medium">{a.user_email}</p>
                  <p className="text-xs text-gray-500">{a.summary}</p>
                </div>
                <div className="text-right">
                  <span
                    className="text-xs px-2 py-0.5 rounded-full font-medium"
                    style={{
                      background: `${RISK_COLORS[a.risk_level]}20`,
                      color: RISK_COLORS[a.risk_level],
                    }}
                  >
                    {a.risk_level}
                  </span>
                  <p className="text-xs text-gray-600 mt-1">
                    {new Date(a.timestamp).toLocaleString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
