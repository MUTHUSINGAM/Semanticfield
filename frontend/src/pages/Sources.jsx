import { useEffect, useState } from 'react';
import { Database, RefreshCw, CheckCircle, AlertCircle, Plug, Radio, Clock } from 'lucide-react';
import { sourcesAPI } from '../api/client';
import { useAuth } from '../context/AuthContext';

const SOURCE_ICONS = {
  Slack: '💬',
  ClickUp: '✅',
  Notion: '📝',
  Gmail: '📧',
  'Google Drive': '📁',
  Excel: '📊',
  PDF: '📄',
};

const CONNECTION_BADGES = {
  mcp_live: { label: 'MCP Live', className: 'bg-green-400/10 text-green-400 border-green-400/30' },
  mcp_local: { label: 'MCP Local', className: 'bg-blue-400/10 text-blue-400 border-blue-400/30' },
  mock: { label: 'Mock', className: 'bg-gray-400/10 text-gray-400 border-gray-400/30' },
};

export default function Sources() {
  const { user } = useAuth();
  const [sources, setSources] = useState([]);
  const [mcpInfo, setMcpInfo] = useState(null);
  const [syncInfo, setSyncInfo] = useState(null);
  const [slackInfo, setSlackInfo] = useState(null);
  const [ingesting, setIngesting] = useState(false);
  const [message, setMessage] = useState('');

  const loadSources = () => {
    sourcesAPI.list().then((res) => setSources(res.data));
    sourcesAPI.mcpStatus().then((res) => setMcpInfo(res.data)).catch(() => {});
    sourcesAPI.syncStatus().then((res) => setSyncInfo(res.data)).catch(() => {});
    if (user?.role === 'admin' || user?.role === 'security_officer') {
      sourcesAPI.slackVerify().then((res) => setSlackInfo(res.data)).catch(() => {});
    }
  };

  useEffect(() => {
    loadSources();
    const interval = setInterval(loadSources, 30000);
    return () => clearInterval(interval);
  }, [user?.role]);

  const handleIngest = async () => {
    setIngesting(true);
    setMessage('');
    try {
      const res = await sourcesAPI.ingest();
      setMessage(
        `[${res.data.mode}] Ingested ${res.data.documents_ingested} documents (${res.data.chunks_indexed} chunks) via MCP`
      );
      loadSources();
    } catch (err) {
      setMessage(err.response?.data?.detail || 'Ingestion failed');
    } finally {
      setIngesting(false);
    }
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">Enterprise Data Sources</h1>
          <p className="text-gray-500">
            Connected via MCP · Real-time sync every {syncInfo?.interval_seconds || 300}s
          </p>
        </div>
        {user?.role === 'admin' && (
          <button onClick={handleIngest} disabled={ingesting} className="btn-primary flex items-center gap-2">
            <RefreshCw className={`w-4 h-4 ${ingesting ? 'animate-spin' : ''}`} />
            {ingesting ? 'Syncing...' : 'Sync Now'}
          </button>
        )}
      </div>

      {syncInfo && (
        <div className="card mb-4 flex flex-wrap items-center gap-4 text-sm">
          <span className="flex items-center gap-2 text-gray-300">
            <Clock className="w-4 h-4" />
            Last sync: {syncInfo.last_sync_at ? new Date(syncInfo.last_sync_at).toLocaleString() : 'Never'}
            {syncInfo.last_trigger && <span className="text-gray-500">({syncInfo.last_trigger})</span>}
          </span>
          {syncInfo.realtime_enabled && (
            <span className="flex items-center gap-2 text-green-400">
              <Radio className="w-4 h-4" />
              Realtime sync {syncInfo.slack_socket_mode ? 'ON (Slack Socket Mode)' : 'ON (scheduled)'}
            </span>
          )}
          {syncInfo.last_result && (
            <span className="text-gray-500">
              {syncInfo.last_result.documents} docs · {syncInfo.last_result.chunks} chunks
            </span>
          )}
        </div>
      )}

      {slackInfo && slackInfo.status !== 'connected' && (user?.role === 'admin' || user?.role === 'security_officer') && (
        <div className="card mb-6 border-red-400/30">
          <h3 className="font-semibold text-red-400 mb-2">Slack Setup Required</h3>
          {slackInfo.missing_scopes?.length > 0 && (
            <p className="text-sm text-gray-400 mb-2">
              Missing scopes: <code className="text-yellow-400">{slackInfo.missing_scopes.join(', ')}</code>
            </p>
          )}
          {slackInfo.errors?.map((e) => (
            <p key={e} className="text-sm text-red-400/80">{e}</p>
          ))}
          <ol className="mt-3 space-y-1 text-xs text-gray-400 list-decimal list-inside">
            {slackInfo.setup_steps?.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </div>
      )}

      {mcpInfo && (
        <div className="card mb-6 border-shield-accent/30">
          <div className="flex items-center gap-2 mb-2">
            <Plug className="w-4 h-4 text-shield-accent" />
            <h3 className="font-semibold">MCP Mode: {mcpInfo.mode === 'mcp_live' ? 'Live' : 'Mock'}</h3>
          </div>
          <p className="text-sm text-gray-400">{mcpInfo.description}</p>
        </div>
      )}

      {message && (
        <div className="mb-4 text-sm text-green-400 bg-green-400/10 border border-green-400/20 rounded-lg px-4 py-2">
          {message}
        </div>
      )}

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sources.map((source) => {
          const badge = CONNECTION_BADGES[source.connection_type] || CONNECTION_BADGES.mock;
          const isError = source.status === 'error' || source.status === 'disconnected';
          return (
            <div key={source.name} className="card">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{SOURCE_ICONS[source.name] || '📦'}</span>
                  <div>
                    <h3 className="font-semibold">{source.name}</h3>
                    <p className="text-xs text-gray-500 capitalize">{source.type?.replace('_', ' ')}</p>
                  </div>
                </div>
                <span className={`flex items-center gap-1 text-xs ${isError ? 'text-red-400' : 'text-green-400'}`}>
                  {isError ? <AlertCircle className="w-3 h-3" /> : <CheckCircle className="w-3 h-3" />}
                  {source.status}
                </span>
              </div>

              <div className="flex flex-wrap gap-2 mb-3">
                <span className={`text-xs px-2 py-0.5 rounded-full border ${badge.className}`}>{badge.label}</span>
                {source.protocol === 'mcp' && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-purple-400/10 text-purple-400 border border-purple-400/30">MCP</span>
                )}
              </div>

              {source.last_error && <p className="text-xs text-red-400 mb-2">{source.last_error}</p>}

              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500">
                  <Database className="w-3 h-3 inline mr-1" />
                  {source.document_count} documents
                </span>
                {source.last_synced && (
                  <span className="text-xs text-gray-600">
                    {new Date(source.last_synced).toLocaleString()}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
