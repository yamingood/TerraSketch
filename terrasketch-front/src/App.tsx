import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import OnboardingPage from './pages/OnboardingPage';
import PlanVisualizationPage from './pages/PlanVisualizationPage';
// import DashboardPage from './pages/dashboard/DashboardPage'; // Temporairement désactivé à cause d'un problème d'import

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: false,
    },
  },
});

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Routes>
            {/* Page d'onboarding comme point d'entrée principal */}
            <Route path="/onboarding" element={<OnboardingPage />} />
            
            {/* Page dashboard (accueil) - temporairement désactivée */}
            {/* <Route path="/dashboard" element={<DashboardPage />} /> */}
            
            {/* Page de visualisation des plans */}
            <Route path="/plan/:planId" element={<PlanVisualizationPage />} />
            
            {/* Redirection de toutes les routes vers onboarding */}
            <Route path="/" element={<Navigate to="/onboarding" replace />} />
            <Route path="*" element={<Navigate to="/onboarding" replace />} />
          </Routes>
        </div>
      </Router>
    </QueryClientProvider>
  );
};

export default App;
