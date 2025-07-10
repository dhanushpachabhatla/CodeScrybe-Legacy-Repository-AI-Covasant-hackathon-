import React, { useState } from 'react';
import { 
  Github, 
  ChevronLeft, 
  Network,
  BarChart3,
  Code,
  Sparkles,
  CheckCircle,
  Loader2,
  Shield,
  AlertCircle,
  RefreshCw
} from 'lucide-react';

const RepositorySetupScreen = ({ onBack, onRepositoryAdded }) => {
  const [repoUrl, setRepoUrl] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState(null); // 'success', 'error', 'exists'
  const [statusMessage, setStatusMessage] = useState('');

  const handleSubmitRepo = async () => {
    if (!repoUrl.trim()) return;

    setIsSubmitting(true);
    setSubmitStatus(null);
    setStatusMessage('');

    try {
      const response = await fetch('http://localhost:8000/repositories', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          repo_url: repoUrl.trim(),
          description: description.trim() || undefined
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to create repository');
      }

      if (data.status === 'exists') {
        setSubmitStatus('exists');
        setStatusMessage('Repository already exists in the system');
      } else if (data.status === 'invalid') {
        setSubmitStatus('invalid');
        setStatusMessage('Invalid Repository Url');
      } else if (data.status === 'created') {
        setSubmitStatus('success');
        setStatusMessage('Repository added successfully! Analysis running in background.');
        
        // Add to parent component's state
        onRepositoryAdded?.({
          id: data.repository_id,
          name: repoUrl.split('/').pop()?.replace('.git', '') || 'new-repo',
          url: repoUrl,
          language: 'Unknown',
          status: 'pending',
          messageCount: 0,
          stars: 0,
          lastAnalyzed: 'analyzing...',
          description: description || 'Recently added repository'
        });

        // Reset form after success
        setTimeout(() => {
          setRepoUrl('');
          setDescription('');
          setSubmitStatus(null);
          setStatusMessage('');
        }, 2000);
      }
    } catch (error) {
      setSubmitStatus('error');
      setStatusMessage(error.message || 'Failed to add repository');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    setSubmitStatus(null);
    setStatusMessage('');
    setRepoUrl('');
    setDescription('');
  };

  const getStatusDisplay = () => {
    switch (submitStatus) {
      case 'success':
        return {
          icon: CheckCircle,
          className: 'text-emerald-600 dark:text-emerald-400',
          bgClassName: 'bg-emerald-50/80 dark:bg-emerald-900/20 border-emerald-200/50 dark:border-emerald-800/50'
        };
      case 'exists':
        return {
          icon: AlertCircle,
          className: 'text-amber-600 dark:text-amber-400',
          bgClassName: 'bg-amber-50/80 dark:bg-amber-900/20 border-amber-200/50 dark:border-amber-800/50'
        };
      case 'error':
        return {
          icon: AlertCircle,
          className: 'text-red-600 dark:text-red-400',
          bgClassName: 'bg-red-50/80 dark:bg-red-900/20 border-red-200/50 dark:border-red-800/50'
        };
      case 'invalid':
          return {
            icon: AlertCircle,
            className: 'text-red-600 dark:text-red-400',
            bgClassName: 'bg-red-50/80 dark:bg-red-900/20 border-red-200/50 dark:border-red-800/50'
          };
      default:
        return null;
    }
  };

  const statusDisplay = getStatusDisplay();
  
  return (
    <div className="h-full flex flex-col relative overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-50/30 via-transparent to-purple-50/30 dark:from-blue-950/20 dark:via-transparent dark:to-purple-950/20"></div>
      
      <div className="relative z-10 flex-1 flex flex-col">
        {/* Compact Header */}
        <div className="bg-white/90 dark:bg-gray-900/90 backdrop-blur-xl border-b border-gray-200/50 dark:border-gray-700/50 px-6 py-4">
          <div className="flex items-center space-x-4">
            <button
              onClick={onBack}
              className="p-2 rounded-lg hover:bg-gray-100/70 dark:hover:bg-gray-800/70 text-gray-600 dark:text-gray-400 transition-colors"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
                Add Repository
              </h1>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                Connect your codebase for AI analysis
              </p>
            </div>
          </div>
        </div>

        {/* Main Content - No Scrolling */}
        <div className="flex-1 p-6 flex items-center justify-center">
          <div className="w-full max-w-4xl">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
              
              {/* Repository Form */}
              <div className="lg:col-span-2 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-2xl p-6 border border-gray-200/50 dark:border-gray-700/50 shadow-xl">
                <div className="flex items-center space-x-3 mb-6">
                  <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl flex items-center justify-center shadow-lg">
                    <Github className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-gray-900 dark:text-white">
                      Repository Details
                    </h2>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Analysis starts immediately after adding
                    </p>
                  </div>
                </div>

                <div className="space-y-4">
                  {/* Repository URL */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Repository URL *
                    </label>
                    <div className="relative">
                      <input
                        type="url"
                        value={repoUrl}
                        onChange={(e) => setRepoUrl(e.target.value)}
                        placeholder="https://github.com/username/repository"
                        className="w-full px-4 py-3 bg-gray-50/70 dark:bg-gray-900/70 border border-gray-200/50 dark:border-gray-700/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-all duration-200"
                        disabled={isSubmitting}
                      />
                      <Github className="absolute right-3 top-3 w-5 h-5 text-gray-400" />
                    </div>
                  </div>

                  {/* Description */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Description (Optional)
                    </label>
                    <textarea
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="Brief description of the repository..."
                      rows={3}
                      className="w-full px-4 py-3 bg-gray-50/70 dark:bg-gray-900/70 border border-gray-200/50 dark:border-gray-700/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-all duration-200 resize-none"
                      disabled={isSubmitting}
                    />
                  </div>

                  {/* Status Message */}
                  {statusMessage && statusDisplay && (
                    <div className={`p-4 rounded-lg border ${statusDisplay.bgClassName} flex items-center space-x-3`}>
                      <statusDisplay.icon className={`w-5 h-5 ${statusDisplay.className}`} />
                      <div className="flex-1">
                        <p className={`text-sm font-medium ${statusDisplay.className}`}>
                          {statusMessage}
                        </p>
                      </div>
                      {submitStatus === 'error' && (
                        <button
                          onClick={handleReset}
                          className="p-1 hover:bg-gray-100/50 dark:hover:bg-gray-800/50 rounded transition-colors"
                        >
                          <RefreshCw className="w-4 h-4 text-gray-500" />
                        </button>
                      )}
                    </div>
                  )}

                  {/* Submit Button */}
                  <button
                    onClick={handleSubmitRepo}
                    disabled={!repoUrl.trim() || isSubmitting}
                    className={`w-full py-3 rounded-lg font-medium transition-all duration-200 ${
                      repoUrl.trim() && !isSubmitting
                        ? 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white shadow-lg hover:shadow-xl hover:scale-[1.02]'
                        : 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
                    }`}
                  >
                    <div className="flex items-center justify-center space-x-2">
                      {isSubmitting ? (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin" />
                          <span>Adding Repository...</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-5 h-5" />
                          <span>Add Repository</span>
                        </>
                      )}
                    </div>
                  </button>
                </div>
              </div>

              {/* Features Info */}
              <div className="space-y-4">
                <div className="bg-white/60 dark:bg-gray-800/60 backdrop-blur-sm rounded-xl p-4 border border-gray-200/30 dark:border-gray-700/30">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-3 text-sm">
                    What happens next?
                  </h3>
                  <div className="space-y-3">
                    {[
                      { icon: Code, title: 'Code Analysis', desc: 'Structure & patterns' },
                      { icon: Shield, title: 'Security Scan', desc: 'Vulnerability check' },
                      { icon: Network, title: 'Dependencies', desc: 'Dependency mapping' },
                      { icon: BarChart3, title: 'AI Insights', desc: 'Smart recommendations' }
                    ].map((feature, index) => (
                      <div key={index} className="flex items-center space-x-3">
                        <div className="p-1.5 bg-blue-100/80 dark:bg-blue-900/30 rounded-md">
                          <feature.icon className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
                        </div>
                        <div>
                          <h4 className="font-medium text-gray-900 dark:text-white text-xs">{feature.title}</h4>
                          <p className="text-xs text-gray-600 dark:text-gray-400">{feature.desc}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-gradient-to-r from-blue-50/80 to-purple-50/80 dark:from-blue-950/30 dark:to-purple-950/30 rounded-xl p-4 border border-blue-200/30 dark:border-blue-800/30">
                  <div className="flex items-center space-x-2 mb-2">
                    <Sparkles className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                    <h3 className="font-semibold text-blue-900 dark:text-blue-100 text-sm">
                      Background Processing
                    </h3>
                  </div>
                  <p className="text-xs text-blue-700 dark:text-blue-300">
                    Analysis runs in the background. You can continue using the app while your repository is being processed.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RepositorySetupScreen;