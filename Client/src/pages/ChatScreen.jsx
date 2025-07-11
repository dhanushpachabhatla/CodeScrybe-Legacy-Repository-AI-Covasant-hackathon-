import React, { useState, useRef, useEffect } from 'react';
import { 
  Code, 
  Zap, 
  Network, 
  Download, 
  Share, 
  MoreVertical, 
  MessageCircle, 
  Send, 
  Paperclip, 
  BarChart3, 
  Copy, 
  ThumbsUp, 
  ThumbsDown, 
  FileText,
  Shield,
  Layers,
  Clock,
  User,
  Bot,
  Image,
  Loader2,
  Trash2,
  AlertCircle
} from 'lucide-react';
import { apiUrl } from '../constants.ts';

const ChatScreen = ({ activeRepo, onBack }) => {
  const [chatMessages, setChatMessages] = useState([]);
  const [messageInput, setMessageInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Format message content with advanced markdown-like syntax
  const formatMessageContent = (content) => {
    if (!content) return '';
    
    // Split content into sections while preserving structure
    const sections = content.split(/\n\n+/);
    
    return sections.map((section, sIndex) => {
      // Handle code blocks first (triple backticks)
      if (section.includes('```')) {
        const parts = section.split(/```(\w*)\n?/);
        const elements = [];
        
        for (let i = 0; i < parts.length; i++) {
          if (i % 3 === 0) {
            // Regular content
            if (parts[i].trim()) {
              elements.push(
                <div key={`text-${i}`} className="mb-2">
                  {formatInlineText(parts[i])}
                </div>
              );
            }
          } else if (i % 3 === 1) {
            // Language identifier
            continue;
          } else if (i % 3 === 2) {
            // Code block content
            const language = parts[i - 1] || '';
            const code = parts[i];
            elements.push(
              <div key={`code-${i}`} className="relative group mb-4">
                <div className="flex items-center justify-between bg-gray-100 dark:bg-gray-800 px-4 py-2 rounded-t-lg border-b border-gray-200 dark:border-gray-700">
                  <span className="text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide">
                    {language || 'code'}
                  </span>
                  <button
                    onClick={() => navigator.clipboard.writeText(code)}
                    className="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-md hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                    title="Copy code"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                </div>
                <pre className="bg-gray-50 dark:bg-gray-900 p-4 rounded-b-lg overflow-x-auto text-sm border border-gray-200 dark:border-gray-700 border-t-0">
                  <code className="text-gray-800 dark:text-gray-200 font-mono">{code}</code>
                </pre>
              </div>
            );
          }
        }
        
        return (
          <div key={sIndex} className="mb-4">
            {elements}
          </div>
        );
      }
      
      // Handle bullet lists with better styling
      if (section.match(/^[\s]*[•*-]\s/m)) {
        const items = section.split('\n').filter(line => line.trim());
        const listItems = items.map((item, index) => {
          if (item.match(/^[\s]*[•*-]\s/)) {
            let formatted = item.replace(/^[\s]*[•*-]\s/, '');
            const indent = (item.match(/^(\s*)/)?.[1]?.length || 0) / 2;
            return (
              <li key={index} className={`flex items-start space-x-2 mb-2 ${indent > 0 ? `ml-${indent * 4}` : ''}`}>
                <span className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0"></span>
                <span className="flex-1">{formatInlineText(formatted)}</span>
              </li>
            );
          }
          return null;
        }).filter(Boolean);
        
        return (
          <ul key={sIndex} className="mb-4 space-y-1">
            {listItems}
          </ul>
        );
      }
      
      // Handle numbered lists
      if (section.match(/^\d+\.\s/m)) {
        const items = section.split('\n').filter(line => line.trim());
        const listItems = items.map((item, index) => {
          if (item.match(/^\d+\.\s/)) {
            let formatted = item.replace(/^\d+\.\s/, '');
            return (
              <li key={index} className="flex items-start space-x-3 mb-3">
                <span className="w-6 h-6 bg-blue-500 text-white text-xs font-bold rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  {index + 1}
                </span>
                <span className="flex-1 pt-0.5">{formatInlineText(formatted)}</span>
              </li>
            );
          }
          return null;
        }).filter(Boolean);
        
        return (
          <ol key={sIndex} className="mb-4 space-y-2">
            {listItems}
          </ol>
        );
      }
      
      // Handle any section that starts with an emoji and bold text (generic callout boxes)
      const calloutMatch = section.match(/^([^\s]+)\s*\*\*(.*?)\*\*(.*)/s);
      if (calloutMatch) {
        const [, emoji, title, content] = calloutMatch;
        
        // Determine color scheme based on emoji or content
        let colorScheme = 'blue'; // default
        if (emoji.includes('🔧') || emoji.includes('⚙️')) colorScheme = 'blue';
        else if (emoji.includes('📊') || emoji.includes('📈')) colorScheme = 'green';
        else if (emoji.includes('⚠️') || emoji.includes('❌')) colorScheme = 'red';
        else if (emoji.includes('💡') || emoji.includes('✨')) colorScheme = 'yellow';
        else if (emoji.includes('🔥') || emoji.includes('⚡')) colorScheme = 'orange';
        else if (emoji.includes('🎯') || emoji.includes('🎪')) colorScheme = 'purple';
        
        const colorMap = {
          blue: 'from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border-blue-200 dark:border-blue-800 text-blue-900 dark:text-blue-100',
          green: 'from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border-green-200 dark:border-green-800 text-green-900 dark:text-green-100',
          red: 'from-red-50 to-rose-50 dark:from-red-900/20 dark:to-rose-900/20 border-red-200 dark:border-red-800 text-red-900 dark:text-red-100',
          yellow: 'from-yellow-50 to-amber-50 dark:from-yellow-900/20 dark:to-amber-900/20 border-yellow-200 dark:border-yellow-800 text-yellow-900 dark:text-yellow-100',
          orange: 'from-orange-50 to-red-50 dark:from-orange-900/20 dark:to-red-900/20 border-orange-200 dark:border-orange-800 text-orange-900 dark:text-orange-100',
          purple: 'from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 border-purple-200 dark:border-purple-800 text-purple-900 dark:text-purple-100'
        };
        
        return (
          <div key={sIndex} className={`mb-4 p-4 bg-gradient-to-r ${colorMap[colorScheme]} rounded-lg border`}>
            <div className="flex items-center space-x-2">
              <span className="text-lg">{emoji}</span>
              <span className="font-bold">{title}</span>
            </div>
            {content.trim() && (
              <div className="text-sm">
                {formatInlineText(content)}
              </div>
            )}
          </div>
        );
      }
      
      // Regular paragraphs with better typography
      return (
        <div key={sIndex} className="mb-4 leading-relaxed">
          {formatInlineText(section)}
        </div>
      );
    });
  };

  const formatInlineText = (text) => {
    if (!text) return '';
    
    // Handle bold text
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Handle italic text
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Handle inline code
    text = text.replace(/`(.*?)`/g, '<code class="bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded text-sm">$1</code>');
    
    // Handle headers
    text = text.replace(/^### (.*$)/gm, '<h3 class="text-lg font-semibold mb-2">$1</h3>');
    text = text.replace(/^## (.*$)/gm, '<h2 class="text-xl font-semibold mb-2">$1</h2>');
    text = text.replace(/^# (.*$)/gm, '<h1 class="text-2xl font-bold mb-2">$1</h1>');
    
    return <span dangerouslySetInnerHTML={{ __html: text }} />;
  };

  // Load chat history
  const loadChatHistory = async () => {
    if (!activeRepo?.id) return;
    
    try {
      setIsLoading(true);
      const response = await fetch(`${apiUrl}/repositories/${activeRepo.id}/chat`);
      if (response.ok) {
        const data = await response.json();
        setChatMessages(data.messages || []);
        setShowSuggestions(data.messages.length === 0);
      }
    } catch (err) {
      setError('Failed to load chat history');
      console.error('Error loading chat history:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Clear chat history
  const clearChatHistory = async () => {
    if (!activeRepo?.id) return;
    
    try {
      const response = await fetch(`${apiUrl}/repositories/${activeRepo.id}/chat`, {
        method: 'DELETE'
      });
      if (response.ok) {
        setChatMessages([]);
        setShowSuggestions(true);
      }
    } catch (err) {
      setError('Failed to clear chat history');
      console.error('Error clearing chat history:', err);
    }
  };

  // Send message
  const sendMessage = async (message) => {
    if (!activeRepo?.id || !message.trim()) return;
    
    try {
      const response = await fetch(`${apiUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message.trim(),
          repository_id: activeRepo.id
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        return data;
      } else {
        throw new Error('Failed to send message');
      }
    } catch (err) {
      setError('Failed to send message');
      console.error('Error sending message:', err);
      return null;
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    loadChatHistory();
  }, [activeRepo?.id]);

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages, isTyping]);

  const handleSendMessage = async () => {
    if (!messageInput.trim() || isTyping) return;

    const userMessage = {
      id: `temp_${Date.now()}`,
      type: 'user',
      content: messageInput,
      timestamp: new Date().toISOString()
    };

    setChatMessages(prev => [...prev, userMessage]);
    setMessageInput('');
    setIsTyping(true);
    setShowSuggestions(false);
    setError(null);

    const response = await sendMessage(messageInput);
    
    if (response) {
      const aiMessage = {
        id: response.message_id,
        type: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
        metadata: response.metadata
      };
      
      setChatMessages(prev => [...prev, aiMessage]);
    } else {
      // Add error message
      const errorMessage = {
        id: `error_${Date.now()}`,
        type: 'assistant',
        content: 'Sorry, I encountered an error while processing your request. Please try again.',
        timestamp: new Date().toISOString(),
        isError: true
      };
      setChatMessages(prev => [...prev, errorMessage]);
    }
    
    setIsTyping(false);
  };

  const handleSuggestionClick = (suggestionText) => {
    setMessageInput(suggestionText);
    inputRef.current?.focus();
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'now';
    if (diff < 3600000) return Math.floor(diff / 60000) + 'm ago';
    if (diff < 86400000) return Math.floor(diff / 3600000) + 'h ago';
    return date.toLocaleDateString();
  };

  const suggestions = [
    { text: "Explain the architecture", icon: Layers, color: "from-blue-500 to-cyan-500" },
    { text: "Show dependencies", icon: Network, color: "from-purple-500 to-pink-500" },
    { text: "Find vulnerabilities", icon: Shield, color: "from-red-500 to-orange-500" },
    { text: "Code quality analysis", icon: BarChart3, color: "from-green-500 to-emerald-500" },
    { text: "Performance insights", icon: Zap, color: "from-yellow-500 to-amber-500" },
    { text: "Generate documentation", icon: FileText, color: "from-indigo-500 to-purple-500" }
  ];

  const MessageBubble = ({ message, isLast }) => (
    <div className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'} mb-3`}>
      <div className={`group max-w-[85%] ${message.type === 'user' ? 'mr-2' : 'ml-2'}`}>
        <div className={`flex items-start space-x-2 ${message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
          {/* Avatar */}
          <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${
            message.type === 'user' 
              ? 'bg-gradient-to-r from-blue-500 to-purple-600' 
              : message.isError
              ? 'bg-gradient-to-r from-red-500 to-orange-600'
              : 'bg-gradient-to-r from-emerald-500 to-teal-600'
          }`}>
            {message.type === 'user' ? (
              <User className="w-4 h-4 text-white" />
            ) : message.isError ? (
              <AlertCircle className="w-4 h-4 text-white" />
            ) : (
              <Bot className="w-4 h-4 text-white" />
            )}
          </div>
          
          {/* Message Content */}
          <div className="flex-1 min-w-0">
            <div className={`relative ${
              message.type === 'user'
                ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-2xl rounded-br-md'
                : message.isError
                ? 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 rounded-2xl rounded-bl-md border border-red-200 dark:border-red-800'
                : 'bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm text-gray-900 dark:text-white rounded-2xl rounded-bl-md border border-gray-200/50 dark:border-gray-700/50'
            } px-4 py-3 shadow-lg`}>
              <div className="text-sm leading-relaxed">
                {message.type === 'user' ? (
                  <div className="whitespace-pre-wrap">{message.content}</div>
                ) : (
                  <div className="prose prose-sm max-w-none dark:prose-invert">
                    {formatMessageContent(message.content)}
                  </div>
                )}
              </div>
              
              {/* Metadata for AI messages */}
              {message.type === 'assistant' && message.metadata && !message.isError && (
                <div className="mt-3 pt-3 border-t border-gray-200/50 dark:border-gray-700/50">
                  <div className="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
                    <span className="flex items-center space-x-1">
                      <FileText className="w-3 h-3" />
                      <span>{message.metadata.files_analyzed || 0} files</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <Clock className="w-3 h-3" />
                      <span>{message.metadata.execution_time || 'N/A'}</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <Zap className="w-3 h-3" />
                      <span>{Math.round((message.metadata.confidence || 0) * 100)}% confidence</span>
                    </span>
                  </div>
                </div>
              )}
            </div>
            
            {/* Message Actions */}
            <div className={`flex items-center mt-2 space-x-2 opacity-0 group-hover:opacity-100 transition-opacity ${
              message.type === 'user' ? 'justify-end' : 'justify-start'
            }`}>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {formatTimestamp(message.timestamp)}
              </span>
              {message.type === 'assistant' && !message.isError && (
                <div className="flex items-center space-x-1">
                  <button 
                    onClick={() => navigator.clipboard.writeText(message.content)}
                    className="p-1 rounded-lg hover:bg-gray-100/70 dark:hover:bg-gray-800/70 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                  >
                    <Copy className="w-3 h-3" />
                  </button>
                  <button className="p-1 rounded-lg hover:bg-gray-100/70 dark:hover:bg-gray-800/70 text-gray-400 hover:text-green-500 transition-colors">
                    <ThumbsUp className="w-3 h-3" />
                  </button>
                  <button className="p-1 rounded-lg hover:bg-gray-100/70 dark:hover:bg-gray-800/70 text-gray-400 hover:text-red-500 transition-colors">
                    <ThumbsDown className="w-3 h-3" />
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading chat history...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col relative overflow-hidden">
      {/* Header */}
      <div className="bg-white/95 dark:bg-gray-900/95 backdrop-blur-xl border-b border-gray-200/50 dark:border-gray-700/50 px-4 py-3 relative z-10">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-lg">
                <Code className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="min-w-0">
                <h1 className="text-lg font-bold text-gray-900 dark:text-white truncate">
                  {activeRepo?.name || 'Repository'}
                </h1>
                <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
                  {activeRepo?.description || 'No description'}
                </p>
              </div>
            </div>
            <div className={`px-2.5 py-1 rounded-full text-xs font-medium flex items-center space-x-1.5 ${
              activeRepo?.status === 'analyzed' 
                ? 'bg-emerald-100/80 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'
                : 'bg-amber-100/80 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'
            }`}>
              <Zap className="w-3 h-3" />
              <span className="capitalize">{activeRepo?.status || 'unknown'}</span>
            </div>
          </div>
          
          <div className="flex items-center space-x-1">
            <button
              onClick={clearChatHistory}
              className="p-2 rounded-lg hover:bg-gray-100/70 dark:hover:bg-gray-800/70 text-gray-600 dark:text-gray-400 transition-all duration-200 hover:scale-110"
              title="Clear chat history"
            >
              <Trash2 className="w-4 h-4" />
            </button>
            {[Network, Download, Share, MoreVertical].map((Icon, index) => (
              <button
                key={index}
                className="p-2 rounded-lg hover:bg-gray-100/70 dark:hover:bg-gray-800/70 text-gray-600 dark:text-gray-400 transition-all duration-200 hover:scale-110"
              >
                <Icon className="w-4 h-4" />
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800 px-4 py-2">
          <div className="flex items-center space-x-2 text-red-700 dark:text-red-400">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm">{error}</span>
            <button
              onClick={() => setError(null)}
              className="ml-auto text-red-500 hover:text-red-700 dark:hover:text-red-300"
            >
              <span className="sr-only">Close</span>
              ×
            </button>
          </div>
        </div>
      )}

      {/* Messages Container */}
      <div className="flex-1 overflow-hidden relative">
        <div className="h-full overflow-y-auto px-4 py-3 scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600">
          {chatMessages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-md">
                <div className="w-16 h-16 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
                  <MessageCircle className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                  Start exploring {activeRepo?.name || 'your repository'}
                </h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm mb-6">
                  Ask questions about the codebase, architecture, or get insights
                </p>
              </div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto">
              {chatMessages.map((message, index) => (
                <MessageBubble 
                  key={message.id} 
                  message={message} 
                  isLast={index === chatMessages.length - 1}
                />
              ))}
              
              {isTyping && (
                <div className="flex justify-start mb-3">
                  <div className="flex items-start space-x-2 ml-2">
                    <div className="w-7 h-7 rounded-full bg-gradient-to-r from-emerald-500 to-teal-600 flex items-center justify-center flex-shrink-0">
                      <Bot className="w-4 h-4 text-white" />
                    </div>
                    <div className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm border border-gray-200/50 dark:border-gray-700/50 rounded-2xl rounded-bl-md px-4 py-3 shadow-lg">
                      <div className="flex items-center space-x-2">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce delay-100"></div>
                          <div className="w-2 h-2 bg-pink-500 rounded-full animate-bounce delay-200"></div>
                        </div>
                        <span className="text-sm text-gray-500 dark:text-gray-400">Analyzing...</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Suggestions */}
      {showSuggestions && chatMessages.length === 0 && (
        <div className="px-4 py-2 border-t border-gray-200/50 dark:border-gray-700/50 bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm">
          <div className="max-w-4xl mx-auto">
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-2">
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestionClick(suggestion.text)}
                  className="p-3 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border border-gray-200/50 dark:border-gray-700/50 rounded-xl hover:border-blue-300/50 dark:hover:border-blue-600/50 text-left transition-all duration-200 hover:scale-[1.02] group"
                >
                  <div className="flex items-center space-x-2">
                    <div className={`p-1.5 rounded-lg bg-gradient-to-r ${suggestion.color} bg-opacity-10`}>
                      <suggestion.icon className="w-4 h-4 text-gray-600 dark:text-gray-400 group-hover:scale-110 transition-transform" />
                    </div>
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300 truncate">
                      {suggestion.text}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Input Bar */}
      <div className="bg-white/95 dark:bg-gray-900/95 backdrop-blur-xl border-t border-gray-200/50 dark:border-gray-700/50 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center space-x-3">
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                type="text"
                value={messageInput}
                onChange={(e) => setMessageInput(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                placeholder={`Ask about ${activeRepo?.name || 'the repository'}...`}
                className="w-full px-4 py-3 pr-24 bg-gray-50/80 dark:bg-gray-800/80 border border-gray-200/50 dark:border-gray-700/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-all duration-200"
                disabled={isTyping}
              />
              <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center space-x-1">
                <button 
                  className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors rounded-lg hover:bg-gray-100/50 dark:hover:bg-gray-700/50"
                  disabled={isTyping}
                >
                  <Image className="w-4 h-4" />
                </button>
                <button 
                  className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors rounded-lg hover:bg-gray-100/50 dark:hover:bg-gray-700/50"
                  disabled={isTyping}
                >
                  <Paperclip className="w-4 h-4" />
                </button>
              </div>
            </div>
            <button
              onClick={handleSendMessage}
              disabled={!messageInput.trim() || isTyping}
              className={`p-3 rounded-xl transition-all duration-200 ${
                messageInput.trim() && !isTyping
                  ? 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white shadow-lg hover:shadow-xl hover:scale-105'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
              }`}
            >
              {isTyping ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatScreen;