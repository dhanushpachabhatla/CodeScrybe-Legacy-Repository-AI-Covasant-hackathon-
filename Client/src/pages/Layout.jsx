import React, { useState, useEffect, useRef } from 'react';
import RepositorySetupScreen from './NewRepositoryAdd';
import ChatScreen from './ChatScreen';
import CompactSidebar from './common/Sidebar';

const MainLayout = () => {
  const [theme, setTheme] = useState('dark');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [activeRepo, setActiveRepo] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentScreen, setCurrentScreen] = useState('welcome'); // 'welcome', 'setup', 'chat'
  const sidebarRef = useRef(null)

  // Mock repositories data
  const [repositories, setRepositories] = useState([
    {
      id: 1,
      name: "legacy-banking-system",
      description: "Core banking operations with COBOL mainframe integration",
      language: "COBOL",
      status: "analyzed",
      messageCount: 24,
      stars: 8,
      lastAnalyzed: "2h ago",
      url: "https://github.com/company/legacy-banking-system"
    },
    {
      id: 2,
      name: "financial-processor",
      description: "High-performance transaction processing engine",
      language: "C++",
      status: "analyzing",
      messageCount: 12,
      stars: 15,
      lastAnalyzed: "5m ago",
      url: "https://github.com/finance/financial-processor"
    },
    {
      id: 3,
      name: "analytics-dashboard",
      description: "Business intelligence and reporting system",
      language: "SAS",
      status: "analyzed",
      messageCount: 8,
      stars: 3,
      lastAnalyzed: "1d ago",
      url: "https://github.com/analytics/dashboard"
    }
  ]);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  const handleRepoSelect = (repo) => {
    setActiveRepo(repo);
    setCurrentScreen('chat');
  };

  const handleAddRepository = () => {
    setActiveRepo(null);
    setCurrentScreen('setup');
  };

  const handleRepositoryAdded = (newRepo) => {
    sidebarRef.current.fetchRepositories();
    setRepositories(prev => [...prev, newRepo]);
    setActiveRepo(newRepo);
    setCurrentScreen('chat');
  };

  const handleBackToWelcome = () => {
    setActiveRepo(null);
    setCurrentScreen('welcome');
  };

  const renderMainContent = () => {
    switch (currentScreen) {
      case 'setup':
        return (
          <RepositorySetupScreen
            onBack={handleBackToWelcome}
            onRepositoryAdded={handleRepositoryAdded}
          />
        );
      case 'chat':
        return (
          <ChatScreen
            activeRepo={activeRepo}
            onBack={handleBackToWelcome}
          />
        );
      default:
        return (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg">
                <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
                Welcome to CodeScrybe
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-8 max-w-md mx-auto">
                Select a repository from the sidebar to start analyzing or add a new repository to begin exploring your codebase
              </p>
              <button
                onClick={handleAddRepository}
                className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white px-6 py-3 rounded-xl font-medium transition-all duration-300 hover:scale-105 shadow-lg hover:shadow-xl flex items-center space-x-2 mx-auto"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                <span>Add Your First Repository</span>
              </button>
            </div>
          </div>
        );
    }
  };

  return (
    <div className={`h-screen flex ${theme === 'dark' ? 'dark' : ''} bg-gradient-to-br from-gray-50 via-white to-blue-50/30 dark:from-gray-950 dark:via-gray-900 dark:to-blue-950/30 transition-all duration-500`}>
      {/* Sidebar */}
      <CompactSidebar
        isCollapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        repositories={repositories}
        activeRepo={activeRepo}
        onRepoSelect={handleRepoSelect}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        theme={theme}
        onThemeToggle={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
        onAddRepository={handleAddRepository}
        currentScreen={currentScreen}
        ref={sidebarRef}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-h-0 relative">
        {renderMainContent()}
      </div>
    </div>
  );
};

export default MainLayout;