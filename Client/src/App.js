import './App.css';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import AIDiscoveryLayout from './pages/Layout';
import LeaderboardLanding from './pages/landingPage';
import ErrorPage from "./pages/common/errorPage"; // Import the new ErrorPage component

function AppRoutes() {
    return (
        <Routes>
            <Route path="/" element={<LeaderboardLanding />} />
            <Route path="/dashboard" element={<AIDiscoveryLayout></AIDiscoveryLayout>} />
           
            {/* Default Route: Display ErrorPage for any other routes */}
            <Route path="*" element={<ErrorPage />} />
        </Routes>
    );
}

function App() {
    return (
        <Router>
                      <AppRoutes />
                </Router>
    );
}

export default App;