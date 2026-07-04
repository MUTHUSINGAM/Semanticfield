import { useEffect, useState } from 'react';
import { Save } from 'lucide-react';
import { auditAPI } from '../api/client';

export default function Policies() {
  const [policies, setPolicies] = useState(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    auditAPI.policies().then((res) => setPolicies(res.data));
  }, []);

  const handleSave = async () => {
    await auditAPI.updatePolicies(policies);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  if (!policies) {
    return (
      <div className="p-8 flex items-center justify-center h-full">
        <div className="animate-spin w-8 h-8 border-2 border-shield-accent border-t-transparent rounded-full" />
      </div>
    );
  }

  const fields = [
    { key: 'risk_low_action', label: 'LOW Risk Action', options: ['allow', 'mask', 'block', 'human_review'] },
    { key: 'risk_medium_action', label: 'MEDIUM Risk Action', options: ['allow', 'mask', 'block', 'human_review'] },
    { key: 'risk_high_action', label: 'HIGH Risk Action', options: ['allow', 'mask', 'block', 'human_review'] },
    { key: 'risk_critical_action', label: 'CRITICAL Risk Action', options: ['allow', 'mask', 'block', 'human_review'] },
  ];

  return (
    <div className="p-8 max-w-2xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold">Governance Policies</h1>
        <p className="text-gray-500">Configure DLP actions based on risk levels</p>
      </div>

      <div className="card space-y-6">
        {fields.map(({ key, label, options }) => (
          <div key={key}>
            <label className="block text-sm text-gray-400 mb-1.5">{label}</label>
            <select
              value={policies[key]}
              onChange={(e) => setPolicies({ ...policies, [key]: e.target.value })}
              className="input-field"
            >
              {options.map((o) => (
                <option key={o} value={o}>
                  {o.replace('_', ' ')}
                </option>
              ))}
            </select>
          </div>
        ))}

        <div>
          <label className="block text-sm text-gray-400 mb-1.5">
            Similarity Threshold ({policies.similarity_threshold})
          </label>
          <input
            type="range"
            min="0.5"
            max="0.95"
            step="0.05"
            value={policies.similarity_threshold}
            onChange={(e) =>
              setPolicies({ ...policies, similarity_threshold: parseFloat(e.target.value) })
            }
            className="w-full accent-shield-accent"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>0.50 (permissive)</span>
            <span>0.95 (strict)</span>
          </div>
        </div>

        <button onClick={handleSave} className="btn-primary flex items-center gap-2">
          <Save className="w-4 h-4" />
          {saved ? 'Saved!' : 'Save Policies'}
        </button>
      </div>
    </div>
  );
}
