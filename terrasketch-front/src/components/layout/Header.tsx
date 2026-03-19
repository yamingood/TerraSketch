import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { 
  Menu, 
  User, 
  LogOut, 
  Settings, 
  TreePine,
  Plus,
  Search
} from 'lucide-react';

const Header: React.FC = () => {
  const { user, logout, isAuthenticated } = useAuthStore();
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  const handleLogout = () => {
    logout();
  };

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <TreePine className="h-8 w-8 text-primary-600" />
            <span className="text-xl font-bold text-gray-900">TerraSketch</span>
          </Link>

          {/* Navigation */}
          {isAuthenticated && (
            <nav className="hidden md:flex space-x-8">
              <Link
                to="/dashboard"
                className={isActive('/dashboard') ? 'nav-link-active' : 'nav-link'}
              >
                Tableau de bord
              </Link>
              <Link
                to="/projects"
                className={isActive('/projects') ? 'nav-link-active' : 'nav-link'}
              >
                Mes projets
              </Link>
              <Link
                to="/plants"
                className={isActive('/plants') ? 'nav-link-active' : 'nav-link'}
              >
                Bibliothèque
              </Link>
              {(user?.role === 'pro' || user?.role === 'agency') && (
                <Link
                  to="/pro"
                  className={isActive('/pro') ? 'nav-link-active' : 'nav-link'}
                >
                  Espace Pro
                </Link>
              )}
            </nav>
          )}

          {/* Right side */}
          <div className="flex items-center space-x-4">
            {isAuthenticated ? (
              <>
                {/* Search */}
                <button className="p-2 text-gray-400 hover:text-gray-600">
                  <Search className="h-5 w-5" />
                </button>

                {/* New Project */}
                <Link
                  to="/projects/new"
                  className="btn-primary flex items-center space-x-2"
                >
                  <Plus className="h-4 w-4" />
                  <span>Nouveau projet</span>
                </Link>

                {/* User Menu */}
                <div className="relative group">
                  <button className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100">
                    <div className="h-8 w-8 bg-primary-100 rounded-full flex items-center justify-center">
                      <User className="h-5 w-5 text-primary-600" />
                    </div>
                    <span className="text-sm font-medium text-gray-700">
                      {user?.firstName}
                    </span>
                  </button>

                  {/* Dropdown */}
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
                    <div className="py-2">
                      <div className="px-4 py-2 border-b">
                        <p className="text-sm font-medium text-gray-900">
                          {user?.firstName} {user?.lastName}
                        </p>
                        <p className="text-sm text-gray-500">{user?.email}</p>
                      </div>
                      
                      <Link
                        to="/settings"
                        className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                      >
                        <Settings className="h-4 w-4" />
                        <span>Paramètres</span>
                      </Link>
                      
                      <button
                        onClick={handleLogout}
                        className="flex items-center space-x-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 w-full text-left"
                      >
                        <LogOut className="h-4 w-4" />
                        <span>Se déconnecter</span>
                      </button>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="flex items-center space-x-3">
                <Link
                  to="/login"
                  className="text-gray-700 hover:text-primary-600 font-medium"
                >
                  Se connecter
                </Link>
                <Link
                  to="/register"
                  className="btn-primary"
                >
                  S'inscrire
                </Link>
              </div>
            )}

            {/* Mobile menu button */}
            <button className="md:hidden p-2 text-gray-400 hover:text-gray-600">
              <Menu className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;