import React, { useState, useEffect } from 'react';
import { 
  Github, 
  Zap, 
  Brain, 
  MessageCircle, 
  Upload, 
  Network, 
  Code, 
  Search,
  ArrowRight,
  Moon,
  Sun,
  Menu,
  X,
  Play,
  Star,
  Users,
  Clock,
  Shield
} from 'lucide-react';
import { Navigate, useNavigate } from 'react-router-dom';

const LandingPage = () => {
  const [theme, setTheme] = useState('dark');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeFeature, setActiveFeature] = useState(0);
  const navigate = useNavigate();
  const goToDashboard = ()=>{
    navigate("/dashboard")
  }

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);
    document.documentElement.classList.toggle('dark', savedTheme === 'dark');
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.classList.toggle('dark', newTheme === 'dark');
  };

  const features = [
    {
      icon: <Upload className="w-8 h-8" />,
      title: "Smart Repository Upload",
      description: "Simply paste your GitHub repository URL and let our AI analyze your legacy codebase automatically.",
      color: "from-blue-500 to-cyan-500"
    },
    {
      icon: <Network className="w-8 h-8" />,
      title: "Knowledge Graph Generation",
      description: "Transform complex code relationships into interactive visual graphs that reveal hidden dependencies.",
      color: "from-purple-500 to-pink-500"
    },
    {
      icon: <MessageCircle className="w-8 h-8" />,
      title: "Intelligent Chat Interface",
      description: "Ask natural language questions about your code and get instant, contextual answers from our AI.",
      color: "from-green-500 to-emerald-500"
    },
    {
      icon: <Brain className="w-8 h-8" />,
      title: "Legacy Code Understanding",
      description: "Specialized in COBOL, C++, SAS, and other legacy languages that traditional tools struggle with.",
      color: "from-orange-500 to-red-500"
    }
  ];

  const codeLanguages = ['COBOL', 'C++', 'SAS', 'FORTRAN', 'Pascal', 'Assembly'];
  const stats = [
    { icon: <Users className="w-6 h-6" />, label: 'Active Users', value: 'NA' },
    { icon: <Code className="w-6 h-6" />, label: 'Repositories Analyzed', value: 'NA' },
    { icon: <Clock className="w-6 h-6" />, label: 'Hours Saved', value: 'NA' },
    { icon: <Star className="w-6 h-6" />, label: 'Satisfaction Rate', value: 'NA' }
  ];

  return (
    <div className={`min-h-screen transition-colors duration-300 ${theme === 'dark' ? 'dark bg-gray-900' : 'bg-white'}`}>
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 backdrop-blur-lg bg-white/10 dark:bg-gray-900/10 border-b border-white/20 dark:border-gray-800/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Brain className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
              CodeScrybe
              </span>
            </div>
            
            <div className="hidden md:flex items-center space-x-8">
              <a href="#features" className="text-gray-600 dark:text-gray-300 hover:text-blue-500 transition-colors">Features</a>
              <a href="#how-it-works" className="text-gray-600 dark:text-gray-300 hover:text-blue-500 transition-colors">How it Works</a>
              <a href="#pricing" className="text-gray-600 dark:text-gray-300 hover:text-blue-500 transition-colors">Pricing</a>
              <button onClick={toggleTheme} className="p-2 dark:text-white rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
                {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>
              <button onClick={goToDashboard} className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-6 py-2 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all transform hover:scale-105">
                Get Started
              </button>
            </div>

            <button 
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)} 
              className="md:hidden p-2 rounded-lg bg-gray-100 dark:bg-gray-800"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-white/95 dark:bg-gray-900/95 backdrop-blur-lg border-t border-gray-200 dark:border-gray-800">
            <div className="px-4 py-6 space-y-4">
              <a href="#features" className="block text-gray-600 dark:text-gray-300">Features</a>
              <a href="#how-it-works" className="block text-gray-600 dark:text-gray-300">How it Works</a>
              <a href="#pricing" className="block text-gray-600 dark:text-gray-300">Pricing</a>
              <button onClick={toggleTheme} className="flex items-center space-x-2 text-gray-600 dark:text-gray-300">
                {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                <span>Toggle Theme</span>
              </button>
              <button className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white px-6 py-3 rounded-lg">
                Get Started
              </button>
            </div>
          </div>
        )}
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 via-purple-500/10 to-pink-500/10 dark:from-blue-500/5 dark:via-purple-500/5 dark:to-pink-500/5"></div>
        <div className="absolute top-20 left-10 w-20 h-20 bg-blue-500/20 rounded-full blur-xl animate-pulse"></div>
        <div className="absolute bottom-20 right-10 w-32 h-32 bg-purple-500/20 rounded-full blur-xl animate-pulse delay-1000"></div>
        
        <div className="max-w-7xl mx-auto text-center relative z-10">
          <div className="inline-flex items-center space-x-2 bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-full px-4 py-2 mb-8">
            <Zap className="w-4 h-4 text-blue-500" />
            <span className="text-sm font-medium text-blue-600 dark:text-blue-400">Powered by Advanced AI</span>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold mb-8 leading-tight">
            <span className="bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
              Unlock the Secrets of
            </span>
            <br />
            <span className="bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">
              Legacy Code
            </span>
          </h1>
          
          <p className="text-xl md:text-2xl text-gray-600 dark:text-gray-300 mb-12 max-w-4xl mx-auto leading-relaxed">
            Transform your legacy codebase into interactive knowledge graphs. 
            Chat with your code, understand dependencies, and modernize with confidence.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16">
            <button onClick={goToDashboard} className="group bg-gradient-to-r from-blue-500 to-purple-600 text-white px-8 py-4 rounded-xl text-lg font-semibold hover:from-blue-600 hover:to-purple-700 transition-all transform hover:scale-105 shadow-lg hover:shadow-xl flex items-center space-x-2">
              <span>Start Analyzing Code</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
            
            <button className="group bg-white/10 dark:bg-gray-800/50 backdrop-blur-lg text-gray-900 dark:text-white px-8 py-4 rounded-xl text-lg font-semibold border border-gray-200 dark:border-gray-700 hover:bg-white/20 dark:hover:bg-gray-800/70 transition-all flex items-center space-x-2">
              <Play className="w-5 h-5" />
              <span>Watch Demo</span>
            </button>
          </div>

          {/* Supported Languages */}
          <div className="flex flex-wrap justify-center gap-3 mb-16">
            {codeLanguages.map((lang, index) => (
              <span key={index} className="px-4 py-2 bg-white/10 dark:bg-gray-800/50 backdrop-blur-lg rounded-full text-sm font-medium text-gray-700 dark:text-gray-300 border border-gray-200/50 dark:border-gray-700/50">
                {lang}
              </span>
            ))}
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="flex justify-center mb-2 text-blue-500">
                  {stat.icon}
                </div>
                <div className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-1">
                  {stat.value}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 px-4 bg-gray-50/50 dark:bg-gray-800/20">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-6">
              Powerful Features for
              <span className="bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent"> Code Discovery</span>
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
              Our AI-powered platform transforms how you understand and work with legacy codebases
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <div 
                key={index}
                className="group p-8 bg-white/50 dark:bg-gray-800/50 backdrop-blur-lg rounded-2xl border border-gray-200/50 dark:border-gray-700/50 hover:border-gray-300 dark:hover:border-gray-600 transition-all duration-300 hover:transform hover:scale-105 hover:shadow-xl"
                onMouseEnter={() => setActiveFeature(index)}
              >
                <div className={`w-16 h-16 bg-gradient-to-r ${feature.color} rounded-xl flex items-center justify-center text-white mb-6 group-hover:scale-110 transition-transform`}>
                  {feature.icon}
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                  {feature.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-24 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-6">
              How It Works
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
              Transform your legacy code in three simple steps
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-12">
            {[
              {
                step: "01",
                title: "Upload Repository",
                description: "Paste your GitHub repository URL and our AI begins analyzing your codebase automatically.",
                icon: <Github className="w-8 h-8" />
              },
              {
                step: "02", 
                title: "AI Analysis",
                description: "Our advanced AI processes your code, identifies patterns, and builds comprehensive knowledge graphs.",
                icon: <Brain className="w-8 h-8" />
              },
              {
                step: "03",
                title: "Interactive Discovery",
                description: "Chat with your code, explore dependencies, and gain deep insights through our intuitive interface.",
                icon: <Search className="w-8 h-8" />
              }
            ].map((step, index) => (
              <div key={index} className="text-center relative">
                <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white mx-auto mb-6 relative z-10">
                  {step.icon}
                </div>
                <div className="absolute top-10 left-1/2 transform -translate-x-1/2 text-6xl font-bold text-gray-100 dark:text-gray-800 -z-10">
                  {step.step}
                </div>
                <h3 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
                  {step.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                  {step.description}
                </p>
                {index < 2 && (
                  <div className="hidden md:block absolute top-10 left-full w-full h-0.5 bg-gradient-to-r from-blue-500 to-purple-600 opacity-30"></div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-4 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 relative overflow-hidden">
        <div className="absolute inset-0 bg-black/20"></div>
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <h2 className="text-4xl md:text-6xl font-bold text-white mb-8">
            Ready to Discover Your Code?
          </h2>
          <p className="text-xl text-white/90 mb-12 leading-relaxed">
            Join thousands of developers who are already transforming their legacy codebases with AI-powered insights.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button onClick={goToDashboard} className="bg-white text-gray-900 px-8 py-4 rounded-xl text-lg font-semibold hover:bg-gray-100 transition-all transform hover:scale-105 shadow-lg hover:shadow-xl flex items-center justify-center space-x-2">
              <span>Start Free Trial</span>
              <ArrowRight className="w-5 h-5" />
            </button>
            <button className="bg-white/10 backdrop-blur-lg text-white px-8 py-4 rounded-xl text-lg font-semibold border border-white/20 hover:bg-white/20 transition-all flex items-center justify-center space-x-2">
              <Github className="w-5 h-5" />
              <span>View on GitHub</span>
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-16 px-4 bg-gray-900 dark:bg-black">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-12">
            <div>
              <div className="flex items-center space-x-2 mb-6">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <Brain className="w-5 h-5 text-white" />
                </div>
                <span className="text-xl font-bold text-white">CodeScrybe</span>
              </div>
              <p className="text-gray-400 leading-relaxed">
                Transforming legacy code understanding through the power of artificial intelligence.
              </p>
            </div>
            
            {[
              {
                title: "Product",
                links: ["Features", "Pricing", "Demo", "Documentation"]
              },
              {
                title: "Company", 
                links: ["About", "Careers", "Contact", "Blog"]
              },
              {
                title: "Legal",
                links: ["Privacy", "Terms", "Security", "Compliance"]
              }
            ].map((column, index) => (
              <div key={index}>
                <h4 className="text-white font-semibold mb-6">{column.title}</h4>
                <ul className="space-y-3">
                  {column.links.map((link, linkIndex) => (
                    <li key={linkIndex}>
                      <a href="#" className="text-gray-400 hover:text-white transition-colors">
                        {link}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          
          <div className="border-t border-gray-800 pt-8 flex flex-col md:flex-row justify-between items-center">
            <p className="text-gray-400 mb-4 md:mb-0">
              © 2025 CodeScrybe. All rights reserved.
            </p>
            <div className="flex space-x-6">
              <a href="#" className="text-gray-400 hover:text-white transition-colors">
                <Github className="w-5 h-5" />
              </a>
              <button onClick={toggleTheme} className="p-1 text-gray-400 hover:text-white transition-colors">
                {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;