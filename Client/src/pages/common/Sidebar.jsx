import React, { useState, useEffect, useRef, forwardRef, useImperativeHandle, } from 'react';
import {
  MessageCircle,
  Plus,
  Search,
  Settings,
  Moon,
  Sun,
  ChevronLeft,
  ChevronRight,
  BarChart3,
  Code,
  Star,
  Download,
  Share,
  Sparkles,
  Upload,
  Network,
  MoreVertical,
  Send,
  Paperclip,
  Zap,
  ArrowLeft,
  FolderGit2,
  Shield,
  Layers,
  Database,
  Terminal,
  CheckCircle,
  Clock,
  AlertCircle,
  Github,
  GitBranch,
  FileText,
  Loader2,
  Trash2,
  Eye,
  Play,
  Square,
  RefreshCw,
  TrendingUp,
  X
} from 'lucide-react';
import { apiUrl } from '../../constants.ts';

// Enhanced Sidebar Component with API Integration
const EnhancedSidebar = forwardRef(({
  isCollapsed,
  onToggleCollapse,
  activeRepo,
  onRepoSelect,
  searchQuery,
  onSearchChange,
  theme,
  onThemeToggle,
  onAddRepository,
  currentScreen
}, ref) => {
  const [repositories, setRepositories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [graphStates, setGraphStates] = useState({});
  const [loadingStates, setLoadingStates] = useState({});
  const [showInsights, setShowInsights] = useState(null);
  const [insights, setInsights] = useState(null);
  const [insightsLoading, setInsightsLoading] = useState(false);

  useImperativeHandle(ref, () => ({
    fetchRepositories
  }))

  // Fetch repositories from API
  const fetchRepositories = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${apiUrl}/repositories`);
      if (!response.ok) throw new Error('Failed to fetch repositories');
      const data = await response.json();

      // Transform API data to match component expectations
      const transformedData = data.map(repo => ({
        id: repo.id,
        name: repo.name,
        description: repo.description,
        language: repo.language,
        status: repo.status,
        status_data: repo.status_data,
        messageCount: repo.message_count,
        stars: repo.stars,
        lastAnalyzed: formatDate(repo.last_analyzed),
        url: repo.url,
        filesAnalyzed: repo.files_analyzed,
        totalChunks: repo.total_chunks,
        errorMessage: repo.error_message
      }));

      setRepositories(transformedData);

      // Fetch graph states for all repositories
      await fetchAllGraphStates(transformedData);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Fetch graph states for all repositories
  const fetchAllGraphStates = async (repos) => {
    const states = {};
    for (const repo of repos) {
      try {
        const response = await fetch(`${apiUrl}/repositories/${repo.id}/graph-status`);
        if (response.ok) {
          const data = await response.json();
          states[repo.id] = data;
        }
      } catch (err) {
        console.warn(`Failed to fetch graph state for ${repo.id}:`, err);
      }
    }
    setGraphStates(states);
  };

  // Delete repository
  const deleteRepository = async (repoId, e) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this repository? This action cannot be undone.')) {
      return;
    }

    try {
      setLoadingStates(prev => ({ ...prev, [repoId]: 'deleting' }));
      const response = await fetch(`${apiUrl}/repositories/${repoId}`, {
        method: 'DELETE'
      });

      if (!response.ok) throw new Error('Failed to delete repository');

      setRepositories(prev => prev.filter(repo => repo.id !== repoId));
      setGraphStates(prev => {
        const newStates = { ...prev };
        delete newStates[repoId];
        return newStates;
      });

    } catch (err) {
      alert(`Error deleting repository: ${err.message}`);
    } finally {
      setLoadingStates(prev => {
        const newStates = { ...prev };
        delete newStates[repoId];
        return newStates;
      });
    }
  };

  // Load graph
  const loadGraph = async (repoId, e) => {
    e.stopPropagation();
    try {
      setLoadingStates(prev => ({ ...prev, [repoId]: 'loading' }));
      const response = await fetch(`${apiUrl}/repositories/${repoId}/load-graph`, {
        method: 'POST'
      });

      if (!response.ok) throw new Error('Failed to load graph');

      // Update graph state
      setGraphStates(prev => ({
        ...prev,
        [repoId]: { ...prev[repoId], graph_loaded: true, current_repo_loaded: true }
      }));

    } catch (err) {
      alert(`Error loading graph: ${err.message}`);
    } finally {
      setLoadingStates(prev => {
        const newStates = { ...prev };
        delete newStates[repoId];
        return newStates;
      });
    }
  };

  // Clear graph
  const clearGraph = async (repoId, e) => {
    e.stopPropagation();
    try {
      setLoadingStates(prev => ({ ...prev, [repoId]: 'clearing' }));
      const response = await fetch(`${apiUrl}/repositories/${repoId}/clear-graph`, {
        method: 'POST'
      });

      if (!response.ok) throw new Error('Failed to clear graph');

      // Update graph state
      setGraphStates(prev => ({
        ...prev,
        [repoId]: { ...prev[repoId], graph_loaded: false, current_repo_loaded: false }
      }));

    } catch (err) {
      alert(`Error clearing graph: ${err.message}`);
    } finally {
      setLoadingStates(prev => {
        const newStates = { ...prev };
        delete newStates[repoId];
        return newStates;
      });
    }
  };

  // Show insights
  const showGraphInsights = async (repoId, e) => {
    e.stopPropagation();
    try {
      setInsightsLoading(true);
      setShowInsights(repoId);

      const response = await fetch(`${apiUrl}/repositories/${repoId}/graph-insights`);
      if (!response.ok) throw new Error('Failed to fetch insights');

      const data = await response.json();
      setInsights(data);

    } catch (err) {
      alert(`Error fetching insights: ${err.message}`);
      setShowInsights(null);
    } finally {
      setInsightsLoading(false);
    }
  };

  // Format date
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMinutes = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  // Load repositories on component mount
  useEffect(() => {
    fetchRepositories();
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case 'analyzed': return 'bg-emerald-500';
      case 'analyzing': return 'bg-amber-500 animate-pulse';
      case 'error': return 'bg-rose-500';
      default: return 'bg-slate-500';
    }
  };

  const getLanguageIcon = (language) => {
    const iconProps = { className: "w-3.5 h-3.5" };
    switch (language?.toLowerCase()) {
      case 'cobol': return <Database {...iconProps} />;
      case 'c++': return <Code {...iconProps} />;
      case 'sas': return <BarChart3 {...iconProps} />;
      case 'assembly': return <Terminal {...iconProps} />;
      case 'javascript': return <Code {...iconProps} />;
      case 'python': return <Code {...iconProps} />;
      case 'java': return <Code {...iconProps} />;
      default: return <Code {...iconProps} />;
    }
  };

  const filteredRepos = repositories.filter(repo =>
    repo.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    repo.language?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Loading state
  if (loading) {
    return (
      <div className={`${isCollapsed ? 'w-16' : 'w-72'} h-full bg-white/95 dark:bg-gray-900/95 backdrop-blur-xl border-r border-gray-200/50 dark:border-gray-700/50 flex items-center justify-center`}>
        <div className="flex flex-col items-center space-y-3">
          <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
          {!isCollapsed && <span className="text-sm text-gray-500 dark:text-gray-400">Loading repositories...</span>}
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={`${isCollapsed ? 'w-16' : 'w-72'} h-full bg-white/95 dark:bg-gray-900/95 backdrop-blur-xl border-r border-gray-200/50 dark:border-gray-700/50 flex items-center justify-center`}>
        <div className="flex flex-col items-center space-y-3 p-4">
          <AlertCircle className="w-6 h-6 text-red-500" />
          {!isCollapsed && (
            <div className="text-center">
              <span className="text-sm text-red-600 dark:text-red-400">Error loading repositories</span>
              <button
                onClick={fetchRepositories}
                className="block mt-2 text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
              >
                Try again
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <>
      <div className={`${isCollapsed ? 'w-16' : 'w-72'} h-full bg-white/95 dark:bg-gray-900/95 backdrop-blur-xl border-r border-gray-200/50 dark:border-gray-700/50 transition-all duration-300 flex flex-col relative z-10`}>

        {/* Header */}
        <div className="p-3 border-b border-gray-200/50 dark:border-gray-700/50">
          <div className="flex items-center justify-between">
            {!isCollapsed && (
              <div className="flex items-center space-x-2">
                <div className="w-7 h-7 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center shadow-lg">
                  <Sparkles className="w-4 h-4 text-white" />
                </div>
                <div>
                  <span className="text-sm font-bold text-gray-900 dark:text-white">CodeScrybe</span>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Legacy Code Intelligence</p>
                </div>
              </div>
            )}
            <button
              onClick={onToggleCollapse}
              className="p-1.5 rounded-lg hover:bg-gray-100/70 dark:hover:bg-gray-800/70 text-gray-600 dark:text-gray-400 transition-all duration-200 hover:scale-110"
            >
              {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
            </button>
          </div>

          {!isCollapsed && (
            <div className="flex space-x-2 mt-3">
              <button
                onClick={onAddRepository}
                className={`flex-1 rounded-lg px-3 py-2 flex items-center justify-center space-x-2 transition-all duration-200 hover:scale-[1.02] shadow-lg hover:shadow-xl text-sm font-medium ${currentScreen === 'setup'
                    ? 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white'
                    : 'bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white'
                  }`}
              >
                <Plus className="w-4 h-4" />
                <span>Add Repo</span>
              </button>
              <button
                onClick={fetchRepositories}
                className="px-3 py-2 rounded-lg bg-gray-100/70 dark:bg-gray-800/70 hover:bg-gray-200/70 dark:hover:bg-gray-700/70 text-gray-600 dark:text-gray-400 transition-all duration-200 hover:scale-110"
                title="Refresh repositories"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>

        {/* Search */}
        {!isCollapsed && (
          <div className="p-3 border-b border-gray-200/50 dark:border-gray-700/50">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-gray-400" />
              <input
                type="text"
                placeholder="Search repositories..."
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
                className="w-full pl-10 pr-3 py-2 bg-gray-50/70 dark:bg-gray-800/70 border border-gray-200/50 dark:border-gray-700/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/50 text-sm text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-all duration-200"
              />
            </div>
          </div>
        )}

        {/* Repository List */}
        <div className="flex-1 overflow-y-auto p-2 scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600">
          {filteredRepos.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400">
              <FolderGit2 className="w-8 h-8 mb-2" />
              {!isCollapsed && <span className="text-sm">No repositories found</span>}
            </div>
          ) : isCollapsed ? (
            <div className="space-y-2">
              {filteredRepos.map((repo) => (
                <div key={repo.id} className="relative group">
                  <button
                    onClick={() => onRepoSelect(repo)}
                    className={`w-full p-2.5 rounded-lg flex items-center justify-center relative transition-all duration-200 ${activeRepo?.id === repo.id && currentScreen === 'chat'
                        ? 'bg-blue-100/80 dark:bg-blue-900/30 border border-blue-300/50 dark:border-blue-700/50 shadow-md'
                        : 'hover:bg-gray-100/70 dark:hover:bg-gray-800/70 hover:scale-105'
                      }`}
                  >
                    <div className="text-gray-700 dark:text-gray-300">
                      {getLanguageIcon(repo.language)}
                    </div>
                    <div className={`absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full ${getStatusColor(repo.status)} shadow-sm`}></div>

                    <div className="absolute left-full ml-2 px-2 py-1 bg-gray-900/90 dark:bg-gray-100/90 text-white dark:text-gray-900 text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 backdrop-blur-sm">
                      {repo.name}
                    </div>
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {filteredRepos.map((repo) => (
                <div key={repo.id} className="relative group">
                  <button
                    onClick={() => onRepoSelect(repo)}
                    className={`w-full p-3 rounded-lg text-left transition-all duration-200 ${activeRepo?.id === repo.id && currentScreen === 'chat'
                        ? 'bg-blue-50/80 dark:bg-blue-900/20 border border-blue-200/50 dark:border-blue-800/50 shadow-md scale-[1.02]'
                        : 'hover:bg-gray-50/70 dark:hover:bg-gray-800/50 hover:scale-[1.01] hover:shadow-sm'
                      }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-2.5">
                        <div className="p-1.5 bg-gray-100/80 dark:bg-gray-800/80 rounded-md backdrop-blur-sm">
                          <div className="text-gray-700 dark:text-gray-300">
                            {getLanguageIcon(repo.language)}
                          </div>
                        </div>
                        <div className="flex-1 min-w-0">
                          <span className="font-medium text-sm text-gray-900 dark:text-white block truncate">
                            {repo.name}
                          </span>
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {repo.language}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-1">
                        <div className={`w-2.5 h-2.5 rounded-full ${getStatusColor(repo.status)} flex-shrink-0 shadow-sm`}></div>
                        {graphStates[repo.id] && (
                          <div className={`w-2 h-2 rounded-full ${graphStates[repo.id].graph_loaded ? 'bg-green-500' : 'bg-gray-300'} flex-shrink-0`} title={`Graph ${graphStates[repo.id].graph_loaded ? 'loaded' : 'not loaded'}`}></div>
                        )}
                      </div>
                    </div>

                    <p className="text-xs text-gray-600 dark:text-gray-400 mb-3 line-clamp-2 leading-relaxed">
                      {repo.description}
                    </p>

                    <div className="flex items-center justify-between text-xs mb-2">
                      <div className="flex items-center space-x-3">
                        <span className="flex items-center space-x-1 text-gray-600 dark:text-gray-300">
                          <MessageCircle className="w-3 h-3" />
                          <span className="font-medium">{repo.messageCount}</span>
                        </span>
                        <span className="flex items-center space-x-1 text-gray-600 dark:text-gray-300">
                          <FileText className="w-3 h-3" />
                          <span className="font-medium">{repo.filesAnalyzed}</span>
                        </span>
                      </div>
                      <span className="text-gray-600 dark:text-gray-300 text-xs font-medium">
                        {repo.lastAnalyzed}
                      </span>
                    </div>

                    {/* Action buttons */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-1">
                        {/* Graph Load/Clear Button */}
                        {graphStates[repo.id] && (
                          <button
                            onClick={graphStates[repo.id].graph_loaded ?
                              (e) => clearGraph(repo.id, e) :
                              (e) => loadGraph(repo.id, e)
                            }
                            disabled={loadingStates[repo.id] === 'loading' || loadingStates[repo.id] === 'clearing'}
                            className={`p-1.5 rounded-md transition-all duration-200 hover:scale-110 ${graphStates[repo.id].graph_loaded
                                ? 'bg-red-100/80 dark:bg-red-900/30 text-red-600 dark:text-red-400 hover:bg-red-200/80 dark:hover:bg-red-900/50'
                                : 'bg-green-100/80 dark:bg-green-900/30 text-green-600 dark:text-green-400 hover:bg-green-200/80 dark:hover:bg-green-900/50'
                              }`}
                            title={graphStates[repo.id].graph_loaded ? 'Clear graph' : 'Load graph'}
                          >
                            {loadingStates[repo.id] === 'loading' || loadingStates[repo.id] === 'clearing' ? (
                              <Loader2 className="w-3 h-3 animate-spin" />
                            ) : graphStates[repo.id].graph_loaded ? (
                              <Square className="w-3 h-3" />
                            ) : (
                              <Play className="w-3 h-3" />
                            )}
                          </button>
                        )}

                        {/* Insights Button */}
                        <button
                          onClick={(e) => showGraphInsights(repo.id, e)}
                          className="p-1.5 rounded-md bg-blue-100/80 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-200/80 dark:hover:bg-blue-900/50 transition-all duration-200 hover:scale-110"
                          title="View graph insights"
                        >
                          <TrendingUp className="w-3 h-3" />
                        </button>
                      </div>

                      {/* Delete Button */}
                      <button
                        onClick={(e) => deleteRepository(repo.id, e)}
                        disabled={loadingStates[repo.id] === 'deleting'}
                        className="p-1.5 rounded-md bg-red-100/80 dark:bg-red-900/30 text-red-600 dark:text-red-400 hover:bg-red-200/80 dark:hover:bg-red-900/50 transition-all duration-200 hover:scale-110"
                        title="Delete repository"
                      >
                        {loadingStates[repo.id] === 'deleting' ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : (
                          <Trash2 className="w-3 h-3" />
                        )}
                      </button>
                    </div>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-gray-200/50 dark:border-gray-700/50">
          <div className={`flex ${isCollapsed ? 'justify-center' : 'justify-between'} items-center`}>
            <button
              onClick={onThemeToggle}
              className="p-2 rounded-lg hover:bg-gray-100/70 dark:hover:bg-gray-800/70 text-gray-600 dark:text-gray-400 transition-all duration-200 hover:scale-110"
              title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            >
              {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>

            {!isCollapsed && (
              <div className="flex space-x-1">
                {[Settings, Download, Share].map((Icon, index) => (
                  <button key={index} className="p-2 rounded-lg hover:bg-gray-100/70 dark:hover:bg-gray-800/70 text-gray-600 dark:text-gray-400 transition-all duration-200 hover:scale-110">
                    <Icon className="w-4 h-4" />
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Insights Modal */}
      {showInsights && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-blue-100/80 dark:bg-blue-900/30 rounded-lg">
                    <TrendingUp className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Graph Insights</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {repositories.find(r => r.id === showInsights)?.name}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setShowInsights(null)}
                  className="p-2 rounded-lg hover:bg-gray-100/70 dark:hover:bg-gray-800/70 text-gray-600 dark:text-gray-400 transition-all duration-200"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {insightsLoading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="flex flex-col items-center space-y-3">
                    <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
                    <span className="text-sm text-gray-500 dark:text-gray-400">Loading insights...</span>
                  </div>
                </div>
              ) : insights ? (
                <div className="space-y-6">
                  {/* Statistics */}
                  {insights.insights?.stats && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">Repository Statistics</h4>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        {Object.entries(insights.insights.stats).map(([key, value]) => (
                          <div key={key} className="bg-gray-50/70 dark:bg-gray-800/70 rounded-lg p-3">
                            <div className="text-2xl font-bold text-gray-900 dark:text-white">{value}</div>
                            <div className="text-xs text-gray-500 dark:text-gray-400 capitalize">{key}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Most Connected Features */}
                  {insights.insights?.most_connected_features && insights.insights.most_connected_features.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">Most Connected Features</h4>
                      <div className="space-y-2">
                        {insights.insights.most_connected_features.map((feature, index) => (
                          <div key={index} className="flex items-center justify-between p-3 bg-gray-50/70 dark:bg-gray-800/70 rounded-lg">
                            <span className="text-sm text-gray-900 dark:text-white font-medium">{feature.feature}</span>
                            <span className="text-xs text-gray-500 dark:text-gray-400">{feature.connections} connections</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Empty state */}
                  {(!insights.insights?.stats && !insights.insights?.most_connected_features) && (
                    <div className="text-center py-8">
                      <AlertCircle className="w-8 h-8 mx-auto text-gray-400 mb-2" />
                      <p className="text-sm text-gray-500 dark:text-gray-400">No insights available</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8">
                  <AlertCircle className="w-8 h-8 mx-auto text-red-400 mb-2" />
                  <p className="text-sm text-red-500">Failed to load insights</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
})

export default EnhancedSidebar;