import { Navigate, Route, Routes } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
import AuditLogs from './pages/AuditLogs';
import Policies from './pages/Policies';
import Sources from './pages/Sources';

function ProtectedRoute({ children, roles }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-shield-950">
        <div className="animate-spin w-8 h-8 border-2 border-shield-accent border-t-transparent rounded-full" />
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route
          path="chat"
          element={
            <ProtectedRoute roles={['admin', 'security_officer', 'employee']}>
              <Chat />
            </ProtectedRoute>
          }
        />
        <Route
          path="audit"
          element={
            <ProtectedRoute roles={['admin', 'security_officer', 'auditor']}>
              <AuditLogs />
            </ProtectedRoute>
          }
        />
        <Route
          path="policies"
          element={
            <ProtectedRoute roles={['admin', 'security_officer']}>
              <Policies />
            </ProtectedRoute>
          }
        />
        <Route
          path="sources"
          element={
            <ProtectedRoute roles={['admin', 'security_officer', 'auditor']}>
              <Sources />
            </ProtectedRoute>
          }
        />
      </Route>
    </Routes>
  );
}
