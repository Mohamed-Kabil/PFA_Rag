import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Database,
  Share2,
  Brain,
  MessageSquare,
  Users,
  FileText,
  Settings,
} from 'lucide-react';
import { useAppStore } from '../../stores/app-store';

const modules = [
  { icon: Database,      label: 'Vectorial RAG',    path: '/vectorial', tag: 'M1' },
  { icon: Share2,        label: 'Graph RAG',         path: '/graph',     tag: 'M2' },
  { icon: Brain,         label: 'Agentic RAG',       path: '/agentic',   tag: 'M3' },
  { icon: MessageSquare, label: 'Query',             path: '/chat',      tag: 'M4' },
];

const extras = [
  { icon: LayoutDashboard, label: 'Dashboard',    path: '/' },
  { icon: Users,           label: 'Communities',  path: '/communities' },
  { icon: FileText,        label: 'Documents',    path: '/documents' },
];

export const Sidebar: React.FC = () => {
  const isSidebarOpen = useAppStore((state) => state.isSidebarOpen);

  return (
    <aside
      className={`bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 transition-all duration-300 flex flex-col ${
        isSidebarOpen ? 'w-64' : 'w-20'
      }`}
    >
      {/* Logo */}
      <div className="h-16 flex items-center px-5 border-b border-gray-100 dark:border-gray-800 shrink-0">
        <span className={`font-bold text-xl bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent truncate ${!isSidebarOpen && 'hidden'}`}>
          Graph RAG
        </span>
        {!isSidebarOpen && <span className="font-bold text-blue-600 text-lg">GR</span>}
      </div>

      <nav className="flex-1 overflow-y-auto p-3 space-y-1">
        {/* ── 4 Modules ── */}
        {isSidebarOpen && (
          <div className="px-2 pb-1 pt-2 text-[9px] font-black uppercase tracking-[0.15em] text-gray-400">
            Modules
          </div>
        )}
        {modules.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all font-medium text-sm ${
                isActive
                  ? 'bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400'
                  : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-800 dark:hover:text-gray-200'
              }`
            }
          >
            <item.icon size={19} className="shrink-0" />
            {isSidebarOpen && (
              <>
                <span className="flex-1 truncate">{item.label}</span>
                <span className="text-[9px] font-black px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900/40 text-blue-500 dark:text-blue-400 rounded">
                  {item.tag}
                </span>
              </>
            )}
          </NavLink>
        ))}

        {/* ── Extras ── */}
        <div className="pt-3">
          {isSidebarOpen && (
            <div className="px-2 pb-1 text-[9px] font-black uppercase tracking-[0.15em] text-gray-400">
              System
            </div>
          )}
          {extras.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-xl transition-all text-sm ${
                  isActive
                    ? 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-white font-semibold'
                    : 'text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-gray-600 dark:hover:text-gray-300'
                }`
              }
            >
              <item.icon size={17} className="shrink-0" />
              {isSidebarOpen && <span className="truncate">{item.label}</span>}
            </NavLink>
          ))}
        </div>
      </nav>

      {/* Settings pinned at bottom */}
      <div className="p-3 border-t border-gray-100 dark:border-gray-800 shrink-0">
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2 rounded-xl transition-all text-sm ${
              isActive
                ? 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-white font-semibold'
                : 'text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-gray-600 dark:hover:text-gray-300'
            }`
          }
        >
          <Settings size={17} className="shrink-0" />
          {isSidebarOpen && <span>Settings</span>}
        </NavLink>
      </div>
    </aside>
  );
};
