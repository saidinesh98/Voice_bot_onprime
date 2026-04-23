import { motion, AnimatePresence } from "motion/react";
import {
  Mic, ArrowRight, Mail, Lock,
  MessageSquare, Volume2, Grid3X3,
  MessageCircle, Phone
} from "lucide-react";
import { useState, useEffect } from "react";
import logo from "./aura-logo.png";

const FloatingAuras = () => {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
      <motion.div
        animate={{
          x: [0, 80, -40, 0],
          y: [0, -60, 40, 0],
        }}
        transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
        className="absolute top-0 right-0 w-[500px] h-[500px] bg-sky-500/5 rounded-full blur-[120px]"
      />
      <motion.div
        animate={{
          x: [0, -60, 40, 0],
          y: [0, 80, -40, 0],
        }}
        transition={{ duration: 18, repeat: Infinity, ease: "linear" }}
        className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-blue-600/10 rounded-full blur-[100px]"
      />
    </div>
  );
};

const VoiceWave = ({ count = 20, className = "" }) => {
  return (
    <div className={`flex items-center gap-1 ${className}`}>
      {[...Array(count)].map((_, i) => (
        <motion.div
          key={i}
          className="w-1 bg-brand rounded-full"
          animate={{
            height: [10, 30, 20, 40, 15],
          }}
          transition={{
            duration: 1.2,
            repeat: Infinity,
            delay: i * 0.05,
            ease: "easeInOut",
          }}
        />
      ))}
    </div>
  );
};

const PhoneMockup = () => {
  return (
    <div className="relative mx-auto w-[280px] h-[580px] bg-zinc-900 rounded-[3rem] border-8 border-zinc-800 shadow-2xl overflow-hidden">
      {/* Notch */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-6 bg-zinc-800 rounded-b-2xl z-20" />

      {/* Screen Content */}
      <div className="relative h-full w-full bg-gradient-to-b from-blue-900 to-black p-6 flex flex-col items-center justify-between z-10">
        <div className="flex flex-col items-center mt-12 w-full">
          <div className="w-20 h-20 bg-brand/20 rounded-full flex items-center justify-center border border-brand/30 mb-4 bg-[radial-gradient(circle_at_center,#38bdf8,transparent_70%)]">
            <Mic size={32} className="text-brand" />
          </div>
          <h3 className="text-xl font-semibold text-white">Aura AI</h3>
          <span className="text-brand text-sm font-mono mt-1">04:21</span>
        </div>

        {/* Waves inside phone */}
        <div className="w-full flex justify-center py-8">
          <VoiceWave count={12} className="h-16" />
        </div>

        {/* Call Controls */}
        <div className="grid grid-cols-3 gap-6 mb-8 w-full px-4 text-white/70">
          <div className="flex flex-col items-center gap-2">
            <div className="w-12 h-12 rounded-full bg-white/10 flex items-center justify-center hover:bg-white/20 transition-colors cursor-pointer">
              <Mic size={20} />
            </div>
            <span className="text-[10px] uppercase font-bold tracking-widest">Mute</span>
          </div>
          <div className="flex flex-col items-center gap-2">
            <div className="w-12 h-12 rounded-full bg-white/10 flex items-center justify-center hover:bg-white/20 transition-colors cursor-pointer">
              <Grid3X3 size={20} />
            </div>
            <span className="text-[10px] uppercase font-bold tracking-widest">Keypad</span>
          </div>
          <div className="flex flex-col items-center gap-2">
            <div className="w-12 h-12 rounded-full bg-white/10 flex items-center justify-center hover:bg-white/20 transition-colors cursor-pointer">
              <Volume2 size={20} />
            </div>
            <span className="text-[10px] uppercase font-bold tracking-widest">Speaker</span>
          </div>
        </div>

        {/* End Call Button */}
        <button className="w-16 h-16 bg-red-500 rounded-full flex items-center justify-center shadow-lg shadow-red-500/20 mb-6 active:scale-95 transition-transform">
          <Phone className="text-white rotate-[135deg]" size={24} fill="currentColor" />
        </button>
      </div>

      {/* Decorative Reflections */}
      <div className="absolute top-0 left-0 w-full h-full bg-white/5 pointer-events-none" />
    </div>
  );
};

export default function App() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  return (
    <div className="min-h-screen w-screen selection:bg-brand/30 selection:text-white relative bg-gradient-to-b from-[#0a192f] to-[#040d21]">
      <FloatingAuras />

      {/* Navigation */}
      <nav className="fixed top-0 left-0 w-full px-8 md:px-12 py-6 flex justify-between items-center z-[100] glass-dark border-b border-white/5">
        <div className="flex items-center gap-3">
          <img src={logo} alt="Aura AI" className="h-14 w-auto object-contain" />
          <span className="text-2xl font-bold tracking-tighter text-white">AURA AI</span>
        </div>

        <div className="flex items-center gap-4">
          <button className="hidden md:flex items-center gap-2 px-8 py-3 rounded-full bg-brand text-white text-[10px] font-black uppercase tracking-widest hover:bg-brand-muted transition-all shadow-lg shadow-brand/20 active:scale-95">
            Get Started
          </button>
        </div>
      </nav>

      <main className="relative z-10 max-w-7xl mx-auto px-8 pt-32 pb-12 md:py-20">
        <div className="flex flex-col lg:flex-row items-center lg:items-start justify-center gap-16 xl:gap-24">

          {/* Left: Hero Content */}
          <div className="flex-1 flex flex-col items-center lg:items-start text-center lg:text-left relative">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
              className="w-full"
            >
              <span className="inline-block px-4 py-1.5 rounded-full bg-brand/10 border border-brand/20 text-brand text-[10px] font-black uppercase tracking-[0.2em] mb-8">
                Vocal Intelligence v3.2
              </span>
              <h1 className="text-5xl md:text-7xl lg:text-8xl font-black text-white mb-10 tracking-tighter leading-[0.9]">
                Conversations that <br />
                <span className="text-brand italic font-light drop-shadow-[0_0_20px_rgba(56,189,248,0.4)]">transcend technology.</span>
              </h1>
              <p className="text-white/70 text-lg md:text-xl mb-12 max-w-xl leading-relaxed">
                Experience the next generation of Aura AI. Human-grade responses with sub-200ms latency, supporting 40+ languages natively.
              </p>
            </motion.div>

            <div className="relative mt-8">
              <PhoneMockup />

              {/* Floating Elements */}
              <motion.div
                animate={{ y: [0, -10, 0] }}
                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                className="absolute -left-20 xl:-left-40 bottom-1/2 glass p-4 rounded-2xl flex items-center gap-4 backdrop-blur-md hidden xl:flex border-white/20 whitespace-nowrap z-20"
              >
                <div className="w-12 h-12 bg-indigo-600 rounded-xl flex items-center justify-center text-white shadow-xl shadow-indigo-500/20">
                  <MessageCircle size={24} />
                </div>
                <div className="pr-4">
                  <div className="text-[10px] text-white/50 font-bold uppercase tracking-widest">Neural Status</div>
                  <div className="text-sm text-white font-black">ANALYZING...</div>
                </div>
              </motion.div>
            </div>
          </div>

          {/* Right: Login Card */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="w-full lg:w-[420px] lg:mt-24 sticky top-32"
          >
            <div className="glass p-10 rounded-[3rem] shadow-2xl relative overflow-hidden backdrop-blur-3xl border-white/20 bg-gradient-to-br from-white/10 to-transparent">
              <div className="relative z-10">
                <h2 className="text-3xl font-black text-white mb-2 uppercase tracking-tight">Access Node</h2>
                <p className="text-white/50 text-xs font-bold uppercase tracking-[0.2em] mb-10">Secured Neural Gateway</p>

                <form className="space-y-6" onSubmit={(e) => e.preventDefault()}>
                  <div className="space-y-2">
                    <label className="text-[10px] font-black text-white/60 uppercase tracking-widest ml-1">Identity Protocol</label>
                    <div className="relative">
                      <Mail className="absolute left-5 top-1/2 -translate-y-1/2 text-white/40" size={18} />
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="w-full bg-white/5 border border-white/10 rounded-2xl py-4.5 pl-14 pr-6 text-white focus:outline-none focus:ring-2 focus:ring-brand/40 transition-all placeholder:text-white/20"
                        placeholder="Neural ID"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-black text-white/60 uppercase tracking-widest ml-1">Secure Token</label>
                    <div className="relative">
                      <Lock className="absolute left-5 top-1/2 -translate-y-1/2 text-white/40" size={18} />
                      <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="w-full bg-white/5 border border-white/10 rounded-2xl py-4.5 pl-14 pr-6 text-white focus:outline-none focus:ring-2 focus:ring-brand/40 transition-all placeholder:text-white/20"
                        placeholder="••••••••"
                      />
                    </div>
                  </div>
                  <button className="w-full bg-brand text-white font-black uppercase tracking-[0.2em] py-5 rounded-2xl hover:bg-brand-muted transition-all transform active:scale-95 shadow-2xl shadow-brand/20 flex items-center justify-center gap-3 group mt-4">
                    INITIALIZE NODE
                    <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                  </button>
                </form>

                <div className="mt-10 pt-10 border-t border-white/5 flex flex-col gap-6 items-center">
                  <button className="text-xs text-white/40 hover:text-white transition-colors uppercase tracking-[0.2em] font-black">Forgot Access Code?</button>
                  <p className="text-[10px] text-white/20 uppercase tracking-[0.2em]">
                    New instance? <span className="text-brand font-black cursor-pointer hover:underline">Provision ID</span>
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </main>
    </div>
  );
}
