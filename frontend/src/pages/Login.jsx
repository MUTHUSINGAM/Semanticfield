import { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { Shield, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const DEMO_USERS = [
  { email: 'admin@singam.com', password: 'Admin@123', role: 'Admin' },
  { email: 'security@singam.com', password: 'Security@123', role: 'Security Officer' },
  { email: 'employee@singam.com', password: 'Employee@123', role: 'Employee' },
  { email: 'auditor@singam.com', password: 'Auditor@123', role: 'Auditor' },
];

export default function Login() {
  const { user, login, loading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (loading) return null;
  if (user) return <Navigate to="/" replace />;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Run backend seed first.');
    } finally {
      setSubmitting(false);
    }
  };

  const fillDemo = (demo) => {
    setEmail(demo.email);
    setPassword(demo.password);
  };

  return (
    <div className="min-h-screen flex">
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-shield-900 via-shield-950 to-indigo-950 p-12 flex-col justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-shield-accent rounded-lg flex items-center justify-center">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <span className="font-bold text-lg">SemanticShield AI</span>
        </div>

        <div>
          <h1 className="text-4xl font-bold leading-tight mb-4">
            Protect your enterprise
            <br />
            <span className="text-shield-accent">AI knowledge</span>
          </h1>
          <p className="text-gray-400 text-lg mb-8">
            Semantic-aware data loss prevention for every AI interaction. Stop confidential data from leaving — even when paraphrased.
          </p>
          <div className="space-y-4">
            {[
              { title: 'Semantic Similarity Detection', desc: '96%+ accuracy on paraphrased leaks' },
              { title: 'Real-time Pipeline Inspection', desc: 'Every AI response analyzed before delivery' },
              { title: 'Zero-trust AI Enforcement', desc: 'Block, mask, or warn based on policy' },
            ].map((f) => (
              <div key={f.title} className="flex items-start gap-3">
                <div className="w-2 h-2 mt-2 rounded-full bg-shield-accent" />
                <div>
                  <p className="font-medium">{f.title}</p>
                  <p className="text-sm text-gray-500">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <p className="text-sm text-gray-600">
          7 enterprise sources connected · Demo Mode · Singam Technologies Pvt Ltd
        </p>
      </div>

      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <div className="w-10 h-10 bg-shield-accent rounded-lg flex items-center justify-center">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <span className="font-bold">SemanticShield AI</span>
          </div>

          <h2 className="text-2xl font-bold mb-1">Sign in</h2>
          <p className="text-gray-500 mb-8">Access Singam Technologies AI Security Console</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1.5">Corporate Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-field"
                placeholder="you@singam.com"
                required
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1.5">Password</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-field pr-10"
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {error && (
              <div className="text-sm text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-4 py-2">
                {error}
              </div>
            )}

            <button type="submit" disabled={submitting} className="btn-primary w-full py-3">
              {submitting ? 'Signing in...' : 'Access Security Console'}
            </button>
          </form>

          <div className="mt-8">
            <p className="text-xs text-gray-500 mb-3">Demo Mode — Quick login:</p>
            <div className="grid grid-cols-2 gap-2">
              {DEMO_USERS.map((demo) => (
                <button
                  key={demo.email}
                  type="button"
                  onClick={() => fillDemo(demo)}
                  className="text-left text-xs px-3 py-2 rounded-lg bg-shield-800 border border-shield-700 hover:border-shield-accent/50 transition-colors"
                >
                  <span className="font-medium text-gray-300">{demo.role}</span>
                  <br />
                  <span className="text-gray-500">{demo.email}</span>
                </button>
              ))}
            </div>
          </div>

          <p className="mt-8 text-xs text-center text-gray-600">
            Demo Mode · No real data at risk · Singam Technologies Pvt Ltd
          </p>
        </div>
      </div>
    </div>
  );
}
