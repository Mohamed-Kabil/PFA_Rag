import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEffect } from 'react';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { Dashboard } from './features/dashboard/Dashboard';
import { VectorialRAG } from './features/vectorial/VectorialRAG';
import { GraphExplorer } from './features/graph-explorer/GraphExplorer';
import { ChatInterface } from './features/semantic-search/ChatInterface';
import { Communities } from './features/communities/Communities';
import { Analytics } from './features/analytics/Analytics';
import { Documents } from './features/documents/Documents';
import { Settings } from './features/settings/Settings';
import { useAppStore } from './stores/app-store';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  const darkMode = useAppStore((state) => state.darkMode);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route element={<DashboardLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/vectorial" element={<VectorialRAG />} />
            <Route path="/graph" element={<GraphExplorer />} />
            <Route path="/agentic" element={<Analytics />} />
            <Route path="/chat" element={<ChatInterface />} />
            <Route path="/communities" element={<Communities />} />
<Route path="/documents" element={<Documents />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </Router>
    </QueryClientProvider>
  )
}

export default App
