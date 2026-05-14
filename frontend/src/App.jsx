import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import useAuthStore from './store/authStore';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ChatPage from './pages/ChatPage';
import GalaxyBackground from './components/GalaxyBackground';

const pageVariants = {
  initial: { opacity: 0, filter: 'blur(4px)', scale: 0.99 },
  animate: { opacity: 1, filter: 'blur(0px)', scale: 1 },
  exit:    { opacity: 0, filter: 'blur(4px)', scale: 0.99 },
};

const pageTransition = {
  duration: 0.5,
  ease: [0.16, 1, 0.3, 1],
};

function AnimatedRoutes() {
  const location = useLocation();
  const { isAuthenticated } = useAuthStore();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route
          path="/login"
          element={
            isAuthenticated ? (
              <Navigate to="/dashboard" replace />
            ) : (
              <motion.div style={{ width: '100%', height: '100%' }}
                variants={pageVariants} initial="initial" animate="animate" exit="exit"
                transition={pageTransition}>
                <LoginPage />
              </motion.div>
            )
          }
        />
        <Route
          path="/dashboard"
          element={
            !isAuthenticated ? (
              <Navigate to="/login" replace />
            ) : (
              <motion.div style={{ width: '100%', height: '100%' }}
                variants={pageVariants} initial="initial" animate="animate" exit="exit"
                transition={pageTransition}>
                <DashboardPage />
              </motion.div>
            )
          }
        />
        <Route
          path="/chat"
          element={
            !isAuthenticated ? (
              <Navigate to="/login" replace />
            ) : (
              <motion.div style={{ width: '100%', height: '100%' }}
                variants={pageVariants} initial="initial" animate="animate" exit="exit"
                transition={pageTransition}>
                <ChatPage />
              </motion.div>
            )
          }
        />
        <Route path="/" element={<Navigate to={isAuthenticated ? '/dashboard' : '/login'} replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AnimatePresence>
  );
}

function App() {
  const { initFromStorage, isAuthenticated } = useAuthStore();
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    const init = async () => {
      await initFromStorage();
      setIsInitializing(false);
    };
    init();
  }, [initFromStorage]);

  if (isInitializing) {
    return (
      <div className="app-loading">
        <span style={{ letterSpacing: '0.15em', textTransform: 'uppercase', fontSize: '0.72rem' }}>
          Loading
        </span>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <div style={{ position: 'relative', height: '100vh', overflow: 'hidden' }}>
        <AnimatedRoutes />
      </div>
    </BrowserRouter>
  );
}

export default App;
