import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';

const Sidebar = ({ role }) => {
  const logout = useAuthStore((state) => state.logout);

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', roles: ['admin', 'supervisor', 'investigator'] },
    { name: 'Cases', path: '/cases', roles: ['admin', 'supervisor', 'investigator'] },
    { name: 'Transactions', path: '/transactions', roles: ['admin', 'supervisor', 'investigator'] },
    { name: 'Escalations', path: '/escalations', roles: ['admin', 'supervisor'] },
  ];

  return (
    <div className="flex flex-col w-64 bg-gray-900 text-white h-screen">
      <div className="flex items-center justify-center h-20 shadow-md">
        <h1 className="text-xl font-bold uppercase tracking-wider text-blue-400">Fintelligence</h1>
      </div>
      <nav className="flex-1 px-4 py-4 space-y-2">
        {navItems
          .filter((item) => item.roles.includes(role))
          .map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `block px-4 py-2 rounded-md transition-colors ${
                  isActive ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }`
              }
            >
              {item.name}
            </NavLink>
          ))}
      </nav>
      <div className="px-4 py-4 border-t border-gray-800">
        <button
          onClick={logout}
          className="w-full text-left px-4 py-2 text-gray-300 hover:bg-gray-800 hover:text-white rounded-md transition-colors"
        >
          Sign Out
        </button>
      </div>
    </div>
  );
};

export default Sidebar;