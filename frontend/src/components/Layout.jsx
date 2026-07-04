import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  Shield,
  LayoutDashboard,
  MessageSquare,
  FileText,
  Settings,
  Database,
  LogOut,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', roles: ['admin', 'security_officer', 'auditor'] },
  { to: '/chat', icon: MessageSquare, label: 'AI Chat', roles: ['admin', 'security_officer', 'employee'] },
  { to: '/audit', icon: FileText, label: 'Audit Logs', roles: ['admin', 'security_officer', 'auditor'] },
  { to: '/policies', icon: Settings, label: 'Policies', roles: ['admin', 'security_officer'] },
  { to: '/sources', icon: Database, label: 'Data Sources', roles: ['admin', 'security_officer', 'auditor'] },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const visibleNav = navItems.filter((item) => item.roles.includes(user?.role));

  return (
    <div className="min-h-screen flex bg-shield-950">
      <aside className="w-64 bg-shield-900 border-r border-shield-700/50 flex flex-col">
        <div className="p-6 border-b border-shield-700/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-shield-accent rounded-lg flex items-center justify-center">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-sm">SemanticShield AI</h1>
              <p className="text-xs text-gray-500">Enterprise AI-DLP</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {visibleNav.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-shield-accent/20 text-shield-400 font-medium'
                    : 'text-gray-400 hover:bg-shield-800 hover:text-gray-200'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-shield-700/50">
          <div className="px-4 py-2 mb-2">
            <p className="text-sm font-medium truncate">{user?.full_name}</p>
            <p className="text-xs text-gray-500 truncate">{user?.email}</p>
            <span className="inline-block mt-1 text-xs px-2 py-0.5 rounded-full bg-shield-accent/20 text-shield-400 capitalize">
              {user?.role?.replace('_', ' ')}
            </span>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 w-full px-4 py-2 text-sm text-gray-400 hover:text-red-400 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Sign out
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
