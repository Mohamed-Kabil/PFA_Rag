import React from 'react';
import { Menu, Bell } from 'lucide-react';
import { useAppStore } from '../../stores/app-store';

export const Navbar: React.FC = () => {
  const { toggleSidebar } = useAppStore();

  return (
    <header className="h-16 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-6 flex items-center justify-between">
      <button
        onClick={toggleSidebar}
        className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-gray-500"
      >
        <Menu size={20} />
      </button>

      <div className="flex items-center gap-4">
        <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-gray-500">
          <Bell size={20} />
        </button>
        <div className="h-8 w-8 bg-gradient-to-tr from-blue-500 to-purple-500 rounded-full border-2 border-white dark:border-gray-800 shadow-sm"></div>
      </div>
    </header>
  );
};
