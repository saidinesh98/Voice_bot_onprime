import React, { createContext, useContext, useEffect, useState, useRef } from 'react';
import Keycloak from 'keycloak-js';

interface AuthContextType {
  keycloak: Keycloak | null;
  authenticated: boolean;
  token: string | null;
  username: string | null;
  login: () => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within an AuthProvider");
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [keycloak, setKeycloak] = useState<Keycloak | null>(null);
  const [authenticated, setAuthenticated] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [username, setUsername] = useState<string | null>(null);
  const isInitialized = useRef(false);

  useEffect(() => {
    if (isInitialized.current) return;
    isInitialized.current = true;

    const kc = new Keycloak({
      url: window.location.origin, // Tunnel URL / Nginx Gateway
      realm: 'aura-ai',
      clientId: 'aura-client',
    });

    kc.init({ 
      onLoad: 'login-required', // Forces login immediately
      checkLoginIframe: false,
      pkceMethod: 'S256'
    }).then((auth) => {
      setKeycloak(kc);
      setAuthenticated(auth);
      if (auth) {
        setToken(kc.token || null);
        setUsername(kc.tokenParsed?.preferred_username || null);
        console.log("✅ Keycloak Authenticated:", kc.tokenParsed?.preferred_username);
      }
    }).catch(err => {
      console.error("❌ Keycloak Initialization Failed:", err);
    });

    // Token refresh logic
    const interval = setInterval(() => {
      if (kc.authenticated) {
        kc.updateToken(70).then((refreshed) => {
          if (refreshed) {
            setToken(kc.token || null);
            console.log("♻️ Token refreshed");
          }
        });
      }
    }, 60000);

    return () => clearInterval(interval);
  }, []);

  const login = () => keycloak?.login();
  const logout = () => keycloak?.logout();

  return (
    <AuthContext.Provider value={{ keycloak, authenticated, token, username, login, logout }}>
      {authenticated ? children : (
        <div className="min-h-screen bg-[#050508] flex items-center justify-center">
            <div className="text-white text-center space-y-4">
                <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-xl font-light tracking-widest uppercase animate-pulse">Initializing Aura AI...</p>
                <p className="text-sm text-gray-500">Connecting to Keycloak</p>
            </div>
        </div>
      )}
    </AuthContext.Provider>
  );
};
