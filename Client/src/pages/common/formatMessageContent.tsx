import React, { useState, useCallback, useMemo } from 'react';
import { Copy, Check, ExternalLink, Quote, AlertCircle, Info, CheckCircle, XCircle, Zap, Lightbulb, Target, Settings, BarChart3, Flame, ChevronDown, ChevronUp, Eye, EyeOff } from 'lucide-react';

// Enhanced inline text formatting with comprehensive support
const formatInlineText = (text) => {
  if (!text || typeof text !== 'string') return '';
  
  // Handle multiple formatting types with proper nesting
  const formatText = (content) => {
    if (!content || typeof content !== 'string') return content;
    
    let result = content;
    let elementIndex = 0;
    
    // Enhanced regex patterns for better matching (in order of priority)
    const patterns = [
      // Code spans (highest priority) - improved to handle edge cases
      { 
        regex: /`([^`\n]+(?:\n[^`]*)*?)`/g, 
        component: (match, content, key) => (
          <code key={key} className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded text-sm font-mono text-red-600 dark:text-red-400 border whitespace-pre-wrap">
            {content}
          </code>
        )
      },
      // Markdown-style links [text](url) - Enhanced with better URL handling
      { 
        regex: /\[([^\]]+)\]\(([^)]+)\)/g,
        component: (match, text, url, key) => {
          // Handle relative URLs and ensure protocol
          let fullUrl = url;
          if (url.startsWith('http://') || url.startsWith('https://')) {
            fullUrl = url;
          } else if (url.startsWith('www.')) {
            fullUrl = `https://${url}`;
          } else if (url.startsWith('/')) {
            fullUrl = url; // Keep relative URLs as-is
          } else if (!url.includes('://')) {
            fullUrl = `https://${url}`;
          }
          
          return (
            <a 
              key={key} 
              href={fullUrl} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 underline decoration-2 underline-offset-2 hover:decoration-blue-600 dark:hover:decoration-blue-400 transition-colors duration-200 inline-flex items-center gap-1"
            >
              {text}
              <ExternalLink className="w-3 h-3" />
            </a>
          );
        }
      },
      // Enhanced URLs - more comprehensive pattern
      { 
        regex: /(?:https?:\/\/)?(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&=]*)/g,
        component: (match, url, key) => {
          // Skip if this URL is already part of a markdown link
          const fullUrl = url.startsWith('http') ? url : `https://${url}`;
          return (
            <a 
              key={key} 
              href={fullUrl} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 underline decoration-2 underline-offset-2 hover:decoration-blue-600 dark:hover:decoration-blue-400 transition-colors duration-200 inline-flex items-center gap-1"
            >
              {url}
              <ExternalLink className="w-3 h-3" />
            </a>
          );
        }
      },
      // GitHub links (specific pattern)
      { 
        regex: /(?:https?:\/\/)?github\.com\/[\w\-\.]+\/[\w\-\.]+(?:\/[^\s]*)?/g,
        component: (match, url, key) => {
          const fullUrl = url.startsWith('http') ? url : `https://${url}`;
          return (
            <a 
              key={key} 
              href={fullUrl} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-purple-600 dark:text-purple-400 hover:text-purple-800 dark:hover:text-purple-300 underline decoration-2 underline-offset-2 hover:decoration-purple-600 dark:hover:decoration-purple-400 transition-colors duration-200 inline-flex items-center gap-1 font-medium"
            >
              <span className="text-xs bg-purple-100 dark:bg-purple-900 px-1 rounded mr-1">GitHub</span>
              {url}
              <ExternalLink className="w-3 h-3" />
            </a>
          );
        }
      },
      // Email addresses
      { 
        regex: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, 
        component: (match, email, key) => (
          <a 
            key={key} 
            href={`mailto:${email}`}
            className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 underline decoration-2 underline-offset-2"
          >
            {email}
          </a>
        )
      },
      // Bold text - improved pattern to handle edge cases
      { 
        regex: /\*\*([^*\n]+(?:\*(?!\*)[^*\n]*)*)\*\*/g,
        component: (match, content, key) => (
          <strong key={key} className="font-bold text-gray-900 dark:text-gray-100">
            {content}
          </strong>
        )
      },
      // Italic text - improved to avoid conflicts
      { 
        regex: /(?<!\*)\*([^*\n]+)\*(?!\*)/g,
        component: (match, content, key) => (
          <em key={key} className="italic text-gray-700 dark:text-gray-300">
            {content}
          </em>
        )
      },
      // Strikethrough
      { 
        regex: /~~([^~\n]+)~~/g,
        component: (match, content, key) => (
          <del key={key} className="line-through text-gray-600 dark:text-gray-400">
            {content}
          </del>
        )
      },
      // Highlight/mark text
      { 
        regex: /==([^=\n]+)==/g,
        component: (match, content, key) => (
          <mark key={key} className="bg-yellow-200 dark:bg-yellow-800 px-1 rounded">
            {content}
          </mark>
        )
      }
    ];
    
    // Process each pattern sequentially
    patterns.forEach(({ regex, component }) => {
      if (typeof result === 'string') {
        const parts = [];
        let lastIndex = 0;
        let match;
        
        // Create a new regex instance to avoid lastIndex issues
        const newRegex = new RegExp(regex.source, regex.flags);
        
        while ((match = newRegex.exec(result)) !== null) {
          // Add text before match
          if (match.index > lastIndex) {
            const textBefore = result.slice(lastIndex, match.index);
            if (textBefore) {
              parts.push(textBefore);
            }
          }
          
          // Add formatted element
          const args = match.slice(1); // Remove the full match
          parts.push(component(match[0], ...args, `elem-${elementIndex++}`));
          lastIndex = match.index + match[0].length;
          
          // Prevent infinite loop on zero-length matches
          if (match.index === newRegex.lastIndex) {
            newRegex.lastIndex++;
          }
        }
        
        // Add remaining text
        if (lastIndex < result.length) {
          parts.push(result.slice(lastIndex));
        }
        
        // Update result if we found matches
        if (parts.length > 0) {
          result = parts;
        }
      }
    });
    
    return Array.isArray(result) ? result : [result];
  };
  
  const formatted = formatText(text);
  return Array.isArray(formatted) ? formatted : [formatted];
};

// Enhanced code block component with better syntax highlighting
const CodeBlock = ({ code, language, index }) => {
  const [copied, setCopied] = useState(false);
  const [showLineNumbers, setShowLineNumbers] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  
  const copyToClipboard = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy code:', err);
    }
  }, [code]);
  
  const lines = useMemo(() => code.split('\n'), [code]);
  const shouldCollapse = lines.length > 30;
  const displayLines = shouldCollapse && !isExpanded ? lines.slice(0, 25) : lines;
  
  // Enhanced language detection and styling
  const getLanguageInfo = (lang) => {
    const languages = {
      javascript: { name: 'JavaScript', color: 'text-yellow-600 dark:text-yellow-400', bg: 'bg-yellow-50 dark:bg-yellow-900/20' },
      js: { name: 'JavaScript', color: 'text-yellow-600 dark:text-yellow-400', bg: 'bg-yellow-50 dark:bg-yellow-900/20' },
      python: { name: 'Python', color: 'text-green-600 dark:text-green-400', bg: 'bg-green-50 dark:bg-green-900/20' },
      py: { name: 'Python', color: 'text-green-600 dark:text-green-400', bg: 'bg-green-50 dark:bg-green-900/20' },
      java: { name: 'Java', color: 'text-red-600 dark:text-red-400', bg: 'bg-red-50 dark:bg-red-900/20' },
      cpp: { name: 'C++', color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-50 dark:bg-blue-900/20' },
      'c++': { name: 'C++', color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-50 dark:bg-blue-900/20' },
      c: { name: 'C', color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-50 dark:bg-blue-900/20' },
      html: { name: 'HTML', color: 'text-orange-600 dark:text-orange-400', bg: 'bg-orange-50 dark:bg-orange-900/20' },
      css: { name: 'CSS', color: 'text-purple-600 dark:text-purple-400', bg: 'bg-purple-50 dark:bg-purple-900/20' },
      sql: { name: 'SQL', color: 'text-indigo-600 dark:text-indigo-400', bg: 'bg-indigo-50 dark:bg-indigo-900/20' },
      bash: { name: 'Bash', color: 'text-gray-700 dark:text-gray-300', bg: 'bg-gray-50 dark:bg-gray-900/20' },
      shell: { name: 'Shell', color: 'text-gray-700 dark:text-gray-300', bg: 'bg-gray-50 dark:bg-gray-900/20' },
      json: { name: 'JSON', color: 'text-green-600 dark:text-green-400', bg: 'bg-green-50 dark:bg-green-900/20' },
      xml: { name: 'XML', color: 'text-orange-600 dark:text-orange-400', bg: 'bg-orange-50 dark:bg-orange-900/20' },
      markdown: { name: 'Markdown', color: 'text-gray-700 dark:text-gray-300', bg: 'bg-gray-50 dark:bg-gray-900/20' },
      md: { name: 'Markdown', color: 'text-gray-700 dark:text-gray-300', bg: 'bg-gray-50 dark:bg-gray-900/20' },
      default: { name: 'Code', color: 'text-gray-800 dark:text-gray-200', bg: 'bg-gray-50 dark:bg-gray-900/20' }
    };
    return languages[lang?.toLowerCase()] || languages.default;
  };
  
  const langInfo = getLanguageInfo(language);
  
  return (
    <div className="relative group mb-6 rounded-xl overflow-hidden border border-gray-200 dark:border-gray-700 shadow-lg">
      {/* Enhanced Header */}
      <div className={`flex items-center justify-between ${langInfo.bg} px-4 py-3 border-b border-gray-200 dark:border-gray-700`}>
        <div className="flex items-center space-x-3">
          <div className="flex space-x-1.5">
            <div className="w-3 h-3 bg-red-500 rounded-full shadow-sm"></div>
            <div className="w-3 h-3 bg-yellow-500 rounded-full shadow-sm"></div>
            <div className="w-3 h-3 bg-green-500 rounded-full shadow-sm"></div>
          </div>
          <span className={`text-sm font-semibold ${langInfo.color} uppercase tracking-wider`}>
            {langInfo.name}
          </span>
          <span className="text-xs text-gray-500 dark:text-gray-400 bg-gray-200 dark:bg-gray-700 px-2 py-1 rounded-full">
            {lines.length} lines
          </span>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowLineNumbers(!showLineNumbers)}
            className="flex items-center space-x-1 px-3 py-1.5 text-xs bg-gray-200 dark:bg-gray-700 rounded-full hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
            title="Toggle line numbers"
          >
            {showLineNumbers ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
            <span>{showLineNumbers ? 'Hide' : 'Show'} lines</span>
          </button>
          {shouldCollapse && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center space-x-1 px-3 py-1.5 text-xs bg-gray-200 dark:bg-gray-700 rounded-full hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
              title={isExpanded ? 'Collapse' : 'Expand'}
            >
              {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              <span>{isExpanded ? 'Collapse' : 'Expand'}</span>
            </button>
          )}
          <button
            onClick={copyToClipboard}
            className="flex items-center space-x-1 px-3 py-1.5 text-xs bg-blue-500 text-white rounded-full hover:bg-blue-600 transition-colors shadow-sm"
            title="Copy code"
          >
            {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
            <span>{copied ? 'Copied!' : 'Copy'}</span>
          </button>
        </div>
      </div>
      
      {/* Enhanced Code content */}
      <div className="relative">
        <pre className="bg-gray-50 dark:bg-gray-900 p-4 overflow-x-auto text-sm max-h-96 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600">
          <code className={`font-mono ${langInfo.color} block`}>
            {showLineNumbers ? (
              <div className="table w-full">
                {displayLines.map((line, i) => (
                  <div key={i} className="table-row hover:bg-gray-100 dark:hover:bg-gray-800 group">
                    <span className="table-cell text-right pr-4 text-gray-400 dark:text-gray-600 select-none user-select-none w-12 font-medium">
                      {i + 1}
                    </span>
                    <span className="table-cell whitespace-pre-wrap">{line}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="whitespace-pre-wrap">{displayLines.join('\n')}</div>
            )}
          </code>
        </pre>
        
        {/* Enhanced collapse indicator */}
        {shouldCollapse && !isExpanded && (
          <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-gray-50 dark:from-gray-900 via-gray-50/90 dark:via-gray-900/90 to-transparent flex items-end justify-center pb-3">
            <button
              onClick={() => setIsExpanded(true)}
              className="flex items-center space-x-2 px-4 py-2 text-sm bg-blue-500 text-white rounded-full hover:bg-blue-600 transition-colors shadow-lg"
            >
              <ChevronDown className="w-4 h-4" />
              <span>Show {lines.length - 25} more lines</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

// Enhanced callout component with better detection
const CalloutBox = ({ emoji, title, content, type = 'info' }) => {
  const iconMap = {
    info: Info,
    warning: AlertCircle,
    error: XCircle,
    success: CheckCircle,
    tip: Lightbulb,
    performance: Zap,
    target: Target,
    settings: Settings,
    analytics: BarChart3,
    fire: Flame
  };
  
  const colorSchemes = {
    info: {
      bg: 'from-blue-50 via-blue-50 to-indigo-50 dark:from-blue-900/20 dark:via-blue-900/20 dark:to-indigo-900/20',
      border: 'border-blue-200 dark:border-blue-800',
      text: 'text-blue-900 dark:text-blue-100',
      icon: 'text-blue-600 dark:text-blue-400',
      shadow: 'shadow-blue-100 dark:shadow-blue-900/20'
    },
    warning: {
      bg: 'from-yellow-50 via-yellow-50 to-amber-50 dark:from-yellow-900/20 dark:via-yellow-900/20 dark:to-amber-900/20',
      border: 'border-yellow-200 dark:border-yellow-800',
      text: 'text-yellow-900 dark:text-yellow-100',
      icon: 'text-yellow-600 dark:text-yellow-400',
      shadow: 'shadow-yellow-100 dark:shadow-yellow-900/20'
    },
    error: {
      bg: 'from-red-50 via-red-50 to-rose-50 dark:from-red-900/20 dark:via-red-900/20 dark:to-rose-900/20',
      border: 'border-red-200 dark:border-red-800',
      text: 'text-red-900 dark:text-red-100',
      icon: 'text-red-600 dark:text-red-400',
      shadow: 'shadow-red-100 dark:shadow-red-900/20'
    },
    success: {
      bg: 'from-green-50 via-green-50 to-emerald-50 dark:from-green-900/20 dark:via-green-900/20 dark:to-emerald-900/20',
      border: 'border-green-200 dark:border-green-800',
      text: 'text-green-900 dark:text-green-100',
      icon: 'text-green-600 dark:text-green-400',
      shadow: 'shadow-green-100 dark:shadow-green-900/20'
    },
    tip: {
      bg: 'from-purple-50 via-purple-50 to-pink-50 dark:from-purple-900/20 dark:via-purple-900/20 dark:to-pink-900/20',
      border: 'border-purple-200 dark:border-purple-800',
      text: 'text-purple-900 dark:text-purple-100',
      icon: 'text-purple-600 dark:text-purple-400',
      shadow: 'shadow-purple-100 dark:shadow-purple-900/20'
    },
    performance: {
      bg: 'from-orange-50 via-orange-50 to-red-50 dark:from-orange-900/20 dark:via-orange-900/20 dark:to-red-900/20',
      border: 'border-orange-200 dark:border-orange-800',
      text: 'text-orange-900 dark:text-orange-100',
      icon: 'text-orange-600 dark:text-orange-400',
      shadow: 'shadow-orange-100 dark:shadow-orange-900/20'
    }
  };
  
  // Enhanced type detection
  const detectType = () => {
    const emojiStr = emoji?.toString() || '';
    const titleStr = title?.toString().toLowerCase() || '';
    const contentStr = content?.toString().toLowerCase() || '';
    
    if (emojiStr.includes('⚠️') || emojiStr.includes('❗') || titleStr.includes('warning') || contentStr.includes('warning')) return 'warning';
    if (emojiStr.includes('❌') || emojiStr.includes('🚫') || titleStr.includes('error') || contentStr.includes('error')) return 'error';
    if (emojiStr.includes('✅') || emojiStr.includes('✔️') || titleStr.includes('success') || contentStr.includes('success')) return 'success';
    if (emojiStr.includes('💡') || emojiStr.includes('🔍') || titleStr.includes('tip') || titleStr.includes('note')) return 'tip';
    if (emojiStr.includes('🔥') || emojiStr.includes('⚡') || titleStr.includes('performance') || titleStr.includes('speed')) return 'performance';
    if (titleStr.includes('analysis') || titleStr.includes('result')) return 'info';
    return 'info';
  };
  
  const detectedType = detectType();
  const scheme = colorSchemes[detectedType] || colorSchemes.info;
  const IconComponent = iconMap[detectedType] || iconMap.info;
  
  return (
    <div className={`mb-6 p-5 bg-gradient-to-r ${scheme.bg} rounded-xl border ${scheme.border} shadow-lg ${scheme.shadow}`}>
      <div className="flex items-start space-x-4">
        <div className="flex-shrink-0 mt-1">
          {emoji ? (
            <span className="text-2xl drop-shadow-sm">{emoji}</span>
          ) : (
            <div className={`p-2 rounded-full bg-white/50 dark:bg-gray-800/50 ${scheme.icon}`}>
              <IconComponent className="w-5 h-5" />
            </div>
          )}
        </div>
        <div className="flex-1 min-w-0">
          {title && (
            <h4 className={`font-bold text-lg mb-3 ${scheme.text}`}>
              {formatInlineText(title)}
            </h4>
          )}
          {content && (
            <div className={`text-sm leading-relaxed ${scheme.text}`}>
              {formatInlineText(content)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Enhanced quote component
const QuoteBlock = ({ content, author }) => (
  <div className="mb-6 pl-6 border-l-4 border-blue-500 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-r-xl p-5 shadow-lg">
    <div className="flex items-start space-x-4">
      <Quote className="w-8 h-8 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-1 drop-shadow-sm" />
      <div className="flex-1">
        <div className="text-gray-800 dark:text-gray-200 italic text-lg leading-relaxed">
          {formatInlineText(content)}
        </div>
        {author && (
          <div className="text-sm text-gray-600 dark:text-gray-400 mt-3 font-medium">
            — {author}
          </div>
        )}
      </div>
    </div>
  </div>
);

// Main formatting function with enhanced parsing
const formatMessageContent = (content) => {
  // Input validation and sanitization
  if (!content || typeof content !== 'string') return null;
  
  const sanitizedContent = content.trim();
  if (!sanitizedContent) return null;
  
  try {
    // Enhanced section splitting with better regex
    const sections = sanitizedContent.split(/\n\s*\n+/);
    
    return sections.map((section, sectionIndex) => {
      const trimmedSection = section.trim();
      if (!trimmedSection) return null;
      
      // 1. Handle code blocks (triple backticks) - enhanced with better regex
      const codeBlockRegex = /```(\w*)\n?([\s\S]*?)```/g;
      if (trimmedSection.includes('```')) {
        const parts = [];
        let lastIndex = 0;
        let match;
        
        // Reset regex
        codeBlockRegex.lastIndex = 0;
        
        while ((match = codeBlockRegex.exec(trimmedSection)) !== null) {
          // Add text before code block
          if (match.index > lastIndex) {
            const textBefore = trimmedSection.slice(lastIndex, match.index).trim();
            if (textBefore) {
              parts.push(
                <div key={`text-${parts.length}`} className="mb-4 leading-relaxed">
                  {formatInlineText(textBefore)}
                </div>
              );
            }
          }
          
          // Add code block
          const [, language, code] = match;
          parts.push(
            <CodeBlock 
              key={`code-${parts.length}`} 
              code={code.trim()} 
              language={language || 'text'} 
              index={parts.length}
            />
          );
          
          lastIndex = match.index + match[0].length;
        }
        
        // Add remaining text
        if (lastIndex < trimmedSection.length) {
          const remainingText = trimmedSection.slice(lastIndex).trim();
          if (remainingText) {
            parts.push(
              <div key={`text-${parts.length}`} className="mb-4 leading-relaxed">
                {formatInlineText(remainingText)}
              </div>
            );
          }
        }
        
        return (
          <div key={`section-${sectionIndex}`} className="mb-4">
            {parts}
          </div>
        );
      }
      
      // 2. Handle block quotes
      if (trimmedSection.startsWith('>')) {
        const quoteLines = trimmedSection.split('\n')
          .filter(line => line.trim().startsWith('>'))
          .map(line => line.replace(/^>\s*/, ''));
        
        const quoteContent = quoteLines.join('\n');
        const authorMatch = quoteContent.match(/^(.*?)\s*—\s*(.+)$/s);
        
        if (authorMatch) {
          const [, content, author] = authorMatch;
          return (
            <QuoteBlock 
              key={`quote-${sectionIndex}`} 
              content={content.trim()} 
              author={author.trim()} 
            />
          );
        }
        
        return (
          <QuoteBlock 
            key={`quote-${sectionIndex}`} 
            content={quoteContent} 
          />
        );
      }
      
      // 3. Handle enhanced callout boxes - improved detection
      const calloutMatch = trimmedSection.match(/^([^\s\w]*)\s*\*\*(.*?)\*\*\s*([\s\S]*)/);
      if (calloutMatch) {
        const [, emoji, title, content] = calloutMatch;
        return (
          <CalloutBox 
            key={`callout-${sectionIndex}`}
            emoji={emoji} 
            title={title} 
            content={content.trim()} 
          />
        );
      }
      
      // 4. Handle enhanced bullet lists with better nesting
      if (trimmedSection.match(/^[\s]*[•*-]\s/m)) {
        const lines = trimmedSection.split('\n').filter(line => line.trim());
        const listItems = lines.map((line, index) => {
          const match = line.match(/^(\s*)[•*-]\s(.+)$/);
          if (match) {
            const [, indent, content] = match;
            const level = Math.floor(indent.length / 2);
            return (
              // Continuing from the bullet list item that was cut off:
              <li key={`item-${index}`} className={`flex items-start space-x-3 mb-3 ${level > 0 ? `ml-${Math.min(level * 6, 12)}` : ''}`}>
                <span className="w-2 h-2 bg-gradient-to-r from-blue-500 to-blue-600 rounded-full mt-2 flex-shrink-0"></span>
                <span className="flex-1 leading-relaxed">{formatInlineText(content)}</span>
              </li>
            );
          }
          return null;
        }).filter(Boolean);
        
        return (
          <ul key={`list-${sectionIndex}`} className="mb-6 space-y-1">
            {listItems}
          </ul>
        );
      }
      
      // 5. Handle numbered lists
      if (trimmedSection.match(/^\d+\.\s/m)) {
        const lines = trimmedSection.split('\n').filter(line => line.trim());
        const listItems = lines.map((line, index) => {
          const match = line.match(/^\d+\.\s(.+)$/);
          if (match) {
            const [, content] = match;
            return (
              <li key={`num-item-${index}`} className="flex items-start space-x-3 mb-3">
                <span className="w-7 h-7 bg-gradient-to-r from-blue-500 to-blue-600 text-white text-sm font-bold rounded-full flex items-center justify-center flex-shrink-0">
                  {index + 1}
                </span>
                <span className="flex-1 pt-1 leading-relaxed">{formatInlineText(content)}</span>
              </li>
            );
          }
          return null;
        }).filter(Boolean);
        
        return (
          <ol key={`ordered-list-${sectionIndex}`} className="mb-6 space-y-2">
            {listItems}
          </ol>
        );
      }
      
      // 6. Handle table detection (basic markdown tables)
      if (trimmedSection.includes('|') && trimmedSection.includes('---')) {
        const tableLines = trimmedSection.split('\n').filter(line => line.trim());
        if (tableLines.length >= 3) {
          const headers = tableLines[0].split('|').map(h => h.trim()).filter(h => h);
          const rows = tableLines.slice(2).map(line => 
            line.split('|').map(cell => cell.trim()).filter(cell => cell)
          );
          
          return (
            <div key={`table-${sectionIndex}`} className="mb-6 overflow-x-auto">
              <table className="w-full border-collapse border border-gray-300 dark:border-gray-700 rounded-lg overflow-hidden shadow-lg">
                <thead className="bg-gray-50 dark:bg-gray-800">
                  <tr>
                    {headers.map((header, i) => (
                      <th key={i} className="border border-gray-300 dark:border-gray-700 px-4 py-3 text-left font-semibold text-gray-900 dark:text-gray-100">
                        {formatInlineText(header)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, i) => (
                    <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                      {row.map((cell, j) => (
                        <td key={j} className="border border-gray-300 dark:border-gray-700 px-4 py-3 text-gray-800 dark:text-gray-200">
                          {formatInlineText(cell)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }
      }
      
      // 7. Handle headers
      const headerMatch = trimmedSection.match(/^(#{1,6})\s(.+)$/m);
      if (headerMatch) {
        const [, hashes, title] = headerMatch;
        const level = hashes.length;
        const HeadingTag = `h${level}`;
        const sizes = {
          1: 'text-3xl font-bold mb-6',
          2: 'text-2xl font-bold mb-5',
          3: 'text-xl font-semibold mb-4',
          4: 'text-lg font-semibold mb-3',
          5: 'text-base font-semibold mb-3',
          6: 'text-sm font-semibold mb-2'
        };
        
        return React.createElement(
          HeadingTag,
          {
            key: `header-${sectionIndex}`,
            className: `${sizes[level]} text-gray-900 dark:text-gray-100 leading-tight border-b border-gray-200 dark:border-gray-700 pb-2`
          },
          formatInlineText(title)
        );
      }
      
      // 8. Handle horizontal rules
      if (trimmedSection.match(/^---+$/)) {
        return (
          <hr key={`hr-${sectionIndex}`} className="my-8 border-0 h-px bg-gradient-to-r from-transparent via-gray-300 dark:via-gray-700 to-transparent" />
        );
      }
      
      // 9. Regular paragraphs with enhanced typography
      return (
        <div key={`paragraph-${sectionIndex}`} className="mb-4 leading-relaxed text-gray-800 dark:text-gray-200">
          {formatInlineText(trimmedSection)}
        </div>
      );
    }).filter(Boolean);
    
  } catch (error) {
    console.error('Error formatting message content:', error);
    
    // Fallback to basic formatting
    return (
      <div className="mb-4 leading-relaxed text-gray-800 dark:text-gray-200">
        {formatInlineText(content)}
      </div>
    );
  }
};

// Enhanced Message Formatter Component
const MessageFormatter = ({ content, className = '' }) => {
  const formattedContent = useMemo(() => {
    return formatMessageContent(content);
  }, [content]);
  
  if (!formattedContent) {
    return null;
  }
  
  return (
    <div className={`message-content ${className}`}>
      {formattedContent}
    </div>
  );
};

// Export the main component and utility functions
export { MessageFormatter, formatMessageContent, formatInlineText, CodeBlock, CalloutBox, QuoteBlock };