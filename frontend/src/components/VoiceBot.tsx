import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Mic, MicOff, Volume2, VolumeX, Settings, MessageSquare, Sparkles, Power, Loader2, LogOut, User, Activity } from 'lucide-react';
import { LocalVoiceBotClient } from '@/lib/local-voicebot-client';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { ScrollArea } from '@/components/ui/scroll-area';

const VOICES = ['Puck', 'Charon', 'Zephyr'] as const;

export default function VoiceBot() {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(80);
  const [prevVolume, setPrevVolume] = useState(80);
  const [transcript, setTranscript] = useState<{ role: 'user' | 'bot', text: string }[]>([]);
  const [currentBotText, setCurrentBotText] = useState('');
  const [voice, setVoice] = useState<typeof VOICES[number]>('Zephyr');
  const [audioLevel, setAudioLevel] = useState(0);
  const [latency, setLatency] = useState(0.12);
  const [isThinking, setIsThinking] = useState(false);
  const { token, username, logout } = useAuth();

  const [useLocalBackend, setUseLocalBackend] = useState(true);

  const clientRef = useRef<LocalVoiceBotClient | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<Float32Array[]>([]);
  const isPlayingRef = useRef(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const masterGainRef = useRef<GainNode | null>(null);

  // Audio Playback logic
  const playNextInQueue = useCallback(() => {
    if (audioQueueRef.current.length === 0 || isPlayingRef.current || !audioContextRef.current) {
      isPlayingRef.current = false;
      if (audioQueueRef.current.length === 0) {
        setAudioLevel(0);
        // Resume listening when bot finishes speaking, respecting manual mute state
        clientRef.current?.setRecordingEnabled(!isMuted);
        // Signal backend to start accepting audio again if not muted
        if (!isMuted) {
          clientRef.current?.send({ type: "resume_listening" });
        }
      }
      return;
    }

    const audioData = audioQueueRef.current.shift()!;
    isPlayingRef.current = true;

    // Calculate audio level for visualization
    const sum = audioData.reduce((a, b) => a + Math.abs(b), 0);
    setAudioLevel(Math.min(1, (sum / audioData.length) * 5));

    const source = audioContextRef.current.createBufferSource();
    const buffer = audioContextRef.current.createBuffer(1, audioData.length, 24000);
    buffer.getChannelData(0).set(audioData);
    source.buffer = buffer;

    // Connect through the persistent master gain node
    if (masterGainRef.current) {
      source.connect(masterGainRef.current);
    } else {
      // Fallback if master gain isn't ready
      const gainNode = audioContextRef.current.createGain();
      gainNode.gain.value = volume / 100;
      source.connect(gainNode);
      gainNode.connect(audioContextRef.current.destination);
    }

    source.onended = () => {
      isPlayingRef.current = false;
      playNextInQueue();
    };

    source.start();
  }, [volume]);

  // Update volume instantly when slider moves
  useEffect(() => {
    if (masterGainRef.current && audioContextRef.current) {
      // Direct update for better responsiveness
      masterGainRef.current.gain.setTargetAtTime(volume / 100, audioContextRef.current.currentTime, 0.05);
    }
  }, [volume]);

  const handleConnect = async () => {
    if (isConnected) {
      clientRef.current?.disconnect();
      setIsConnected(false);
      return;
    }

    setIsConnecting(true);
    try {
      if (!audioContextRef.current) {
        audioContextRef.current = new AudioContext({ sampleRate: 24000 });
      }

      if (audioContextRef.current.state === 'suspended') {
        await audioContextRef.current.resume();
      }

      // Initialize persistent master gain node
      const masterGain = audioContextRef.current.createGain();
      masterGain.gain.value = volume / 100;
      masterGain.connect(audioContextRef.current.destination);
      masterGainRef.current = masterGain;

      const callbacks = {
        onTranscription: (text: string) => {
          setTranscript(prev => [...prev, { role: 'user', text }]);
          // Pause listening while bot is thinking/responding
          clientRef.current?.setRecordingEnabled(false);
          setIsThinking(true);
        },
        onMessage: (text: string) => {
          // Ensure recording is paused if we get text stream
          clientRef.current?.setRecordingEnabled(false);
          setIsThinking(false);
          setCurrentBotText(prev => prev + text);
          setTranscript(prev => {
            const last = prev[prev.length - 1];
            if (last?.role === 'bot') {
              return [...prev.slice(0, -1), { role: 'bot', text: last.text + text }];
            }
            return [...prev, { role: 'bot', text }];
          });
        },
        onAudio: (data: Float32Array) => {
          // Double check recording is paused during audio playback
          clientRef.current?.setRecordingEnabled(false);
          setIsThinking(false);
          audioQueueRef.current.push(data);
          playNextInQueue();
        },
        onError: (err: any) => {
          console.error("VoiceBot Error:", err);
          setIsConnected(false);
          setIsThinking(false);
          setAudioLevel(0);
        }
      };

      clientRef.current = new LocalVoiceBotClient();
      await (clientRef.current as LocalVoiceBotClient).connect({
        voiceName: voice,
        audioContext: audioContextRef.current,
        token: token || undefined, // Pass Keycloak JWT
      }, callbacks);
      await (clientRef.current as LocalVoiceBotClient).startMicrophone();

      setIsConnected(true);
      console.log("🎤 Microphone started for local backend");
    } catch (err) {
      console.error("Connection failed:", err);
      alert("Failed to start Voice Bot. Please ensure you have granted microphone permissions, and if accessing remotely, that you are using HTTPS or localhost.");
    } finally {
      setIsConnecting(false);
    }
  };

  useEffect(() => {
    if (currentBotText && !isPlayingRef.current && audioQueueRef.current.length === 0) {
      setTranscript(prev => [...prev, { role: 'bot', text: currentBotText }]);
      setCurrentBotText('');
    }
  }, [currentBotText]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [transcript, currentBotText]);

  return (
    <div className="min-h-screen bg-[#050508] text-[#e2e8f0] font-sans selection:bg-blue-500/30 overflow-hidden flex flex-col relative">
      {/* Immersive Background */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,#0f172a_0%,#050508_100%)] pointer-events-none" />

      {/* Header */}
      <header className="relative z-10 px-8 py-6 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3 group cursor-pointer">
            <div className="relative flex items-center justify-center">
              <div className="absolute inset-0 bg-gradient-to-br from-[#3b82f6] to-[#8b5cf6] rounded-lg blur-md opacity-40 group-hover:opacity-80 transition-opacity duration-500" />
              <div className="relative w-8 h-8 rounded-lg bg-[#0f172a] border border-white/10 flex items-center justify-center overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-t from-blue-500/10 to-transparent pointer-events-none" />
              </div>
            </div>
            <h1 className="text-lg font-bold tracking-widest uppercase bg-clip-text text-transparent bg-gradient-to-r from-white to-white/60 group-hover:from-white group-hover:to-white transition-all duration-500">Aura AI</h1>
          </div>

          <div className="h-6 w-[1px] bg-white/10" />

          <div className="flex items-center gap-2 px-3 py-1 bg-white/5 rounded-full border border-white/10">
            <User className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-[10px] font-mono text-gray-400 uppercase tracking-wider">{username || 'Guest'}</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className={`glass-panel px-4 py-1.5 rounded-full flex items-center gap-2 text-xs font-medium transition-all duration-500 ${isConnected ? 'opacity-100' : 'opacity-40'}`}>
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-[#10b981] shadow-[0_0_10px_#10b981]' : 'bg-white/20'}`} />
            <span>{isConnected ? (useLocalBackend ? 'Local Bot Active' : 'Gemini Active') : 'Bot Offline'}</span>
          </div>

          <button
            onClick={() => logout()}
            className="p-2 rounded-full bg-white/5 border border-white/10 hover:bg-red-500/20 hover:border-red-500/30 transition-all group"
            title="Logout"
          >
            <LogOut className="w-4 h-4 text-gray-400 group-hover:text-red-400" />
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-8 py-4">

        {/* Visualizer Area */}
        <div className="relative w-[300px] h-[300px] flex items-center justify-center">
          {/* Concentric Rings */}
          <motion.div
            animate={{ scale: isConnected ? [1, 1.05, 1] : 1, opacity: isConnected ? 0.5 : 0.2 }}
            transition={{ duration: 4, repeat: Infinity }}
            className="absolute w-full h-full border border-white/10 rounded-full"
          />
          <motion.div
            animate={{ scale: isConnected ? [1, 1.08, 1] : 1, opacity: isConnected ? 0.3 : 0.1 }}
            transition={{ duration: 5, repeat: Infinity, delay: 0.5 }}
            className="absolute w-[85%] h-[85%] border border-[#3b82f6]/20 rounded-full"
          />
          <motion.div
            animate={{ scale: isConnected ? [1, 1.1, 1] : 1, opacity: isConnected ? 0.2 : 0.05 }}
            transition={{ duration: 6, repeat: Infinity, delay: 1 }}
            className="absolute w-[70%] h-[70%] border border-[#8b5cf6]/20 rounded-full"
          />

          {/* Core Orb */}
          <motion.div
            animate={{
              scale: isConnected ? 1 + audioLevel * 0.4 : 1,
              boxShadow: isConnected
                ? [`0 0 40px 15px rgba(59,130,246,0.4), 0 0 70px 30px rgba(139,92,246,0.2)`, `0 0 60px 25px rgba(59,130,246,0.6), 0 0 90px 40px rgba(139,92,246,0.3)`, `0 0 40px 15px rgba(59,130,246,0.4), 0 0 70px 30px rgba(139,92,246,0.2)`]
                : `0 0 30px 5px rgba(255,255,255,0.05)`
            }}
            transition={{
              scale: { type: "spring", stiffness: 300, damping: 20 },
              boxShadow: { duration: 2, repeat: Infinity }
            }}
            className="w-[120px] h-[120px] rounded-full z-10 flex items-center justify-center relative overflow-hidden group/orb cursor-pointer"
          >
            <img
              src="/aura-logo.png"
              alt="Aura Logo"
              className={`w-full h-full object-contain transition-all duration-700 ${isConnected ? 'opacity-100 scale-100' : 'opacity-60 scale-95'}`}
            />
          </motion.div>

          {/* Wave Bars */}
          <div className="absolute -bottom-12 flex gap-1.5 items-end h-[40px]">
            {[...Array(8)].map((_, i) => (
              <motion.div
                key={i}
                animate={{
                  height: isConnected ? [8, 15 + Math.random() * 30 * audioLevel, 8] : 4,
                  opacity: isConnected ? 0.6 : 0.2
                }}
                transition={{ duration: 0.3 + Math.random() * 0.3, repeat: Infinity }}
                className="w-1 bg-gradient-to-t from-[#3b82f6] to-[#8b5cf6] rounded-full"
              />
            ))}
          </div>
        </div>

        {/* Feedback Area */}
        <div className="mt-16 text-center max-w-[600px] min-h-[100px]">
          <AnimatePresence mode="wait">
            {isConnected ? (
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="space-y-4"
              >
                {/* Speaker Indicator */}
                <div className="flex items-center justify-center gap-2 mb-2">
                  {currentBotText || (transcript.length > 0 && transcript[transcript.length - 1].role === 'bot') ? (
                    <>
                      <Sparkles className="w-4 h-4 text-[#3b82f6]" />
                      <span className="text-[10px] font-bold tracking-[3px] text-[#3b82f6] uppercase">Aura</span>
                    </>
                  ) : transcript.length > 0 ? (
                    <>
                      <MessageSquare className="w-4 h-4 text-[#8b5cf6]" />
                      <span className="text-[10px] font-bold tracking-[3px] text-[#8b5cf6] uppercase">You</span>
                    </>
                  ) : null}
                </div>

                <p className="text-2xl font-light leading-tight text-white min-h-[1.5em]">
                  {currentBotText || (transcript.length > 0 ? transcript[transcript.length - 1].text : "I'm listening...")}
                </p>
                <p className="text-base text-[#64748b] italic">
                  {currentBotText
                    ? "Aura is speaking..."
                    : isThinking
                      ? "Aura is thinking..."
                      : "Waiting for your voice..."}
                </p>
              </motion.div>
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-4 flex flex-col items-center"
              >
                <div className="space-y-1">
                  <p className="text-xl font-light text-white/60">Aura is ready</p>
                  <p className="text-xs text-[#64748b]">
                    {useLocalBackend ? 'Connected to local Python backend' : 'Real-time voice conversation powered by Gemini'}
                  </p>
                </div>
                <button
                  onClick={handleConnect}
                  disabled={isConnecting}
                  className="px-6 py-3 bg-white text-[#050508] rounded-full font-bold tracking-wider hover:scale-105 active:scale-95 transition-all flex items-center gap-2 shadow-[0_0_20px_rgba(255,255,255,0.15)] disabled:opacity-50 text-sm"
                >
                  {isConnecting ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Sparkles className="w-5 h-5" />
                  )}
                  {isConnecting ? 'Initializing...' : 'Start Aura'}
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Side Stats */}
        <div className="absolute right-10 top-1/2 -translate-y-1/2 hidden lg:flex flex-col gap-10 text-right">
          <div className="space-y-1">
            <p className="text-[10px] font-mono text-[#3b82f6] uppercase tracking-[2px]">{latency.toFixed(2)}s</p>
            <p className="text-sm text-[#64748b]">Latency</p>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-mono text-[#3b82f6] uppercase tracking-[2px]">24.0kHz</p>
            <p className="text-sm text-[#64748b]">Sample Rate</p>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-mono text-[#3b82f6] uppercase tracking-[2px]">99.4%</p>
            <p className="text-sm text-[#64748b]">Confidence</p>
          </div>
        </div>
      </main>

      {/* Footer Controls */}
      <footer className="relative z-10 px-8 py-10 flex justify-center">
        <div className="glass-panel px-10 py-5 rounded-[32px] flex items-center gap-10 shadow-2xl border-white/5">
          <TooltipProvider>
            {/* Input Group */}
            <div className="flex items-center gap-4">
              <Tooltip>
                <TooltipTrigger
                  onClick={() => {
                    const nextMuted = !isMuted;
                    setIsMuted(nextMuted);
                    // Also update the actual recording state immediately
                    if (clientRef.current) {
                      clientRef.current.setRecordingEnabled(!nextMuted);
                    }
                  }}
                  className={`w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 ${isMuted ? 'bg-red-500/80 border border-red-400' : 'bg-white/5 border border-white/10 hover:bg-white/10'}`}
                >
                  {isMuted ? <MicOff className="w-5 h-5 text-white" /> : <Mic className="w-5 h-5 text-white" />}
                </TooltipTrigger>
                <TooltipContent>Toggle Microphone</TooltipContent>
              </Tooltip>

              <button
                onClick={handleConnect}
                disabled={isConnecting}
                className={`w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 ${isConnected ? 'bg-red-500/80 border border-red-400 hover:scale-105' : 'bg-white/10 border border-white/20 hover:bg-white/20 hover:scale-105'}`}
              >
                {isConnecting ? (
                  <Loader2 className="w-5 h-5 animate-spin text-white" />
                ) : isConnected ? (
                  <Power className="w-5 h-5 text-white" />
                ) : (
                  <Sparkles className="w-5 h-5 text-white" />
                )}
              </button>
            </div>

            <div className="h-10 w-[1px] bg-white/10 mx-2" />

            {/* Volume Group */}
            <div className="flex items-center gap-6 min-w-[200px] shrink-0">
              <Tooltip>
                <TooltipTrigger
                  onClick={() => {
                    if (volume > 0) {
                      setPrevVolume(volume);
                      setVolume(0);
                    } else {
                      setVolume(prevVolume || 80);
                    }
                  }}
                  className="flex items-center justify-center group cursor-pointer shrink-0"
                >
                  {volume === 0 ? (
                    <VolumeX className="w-6 h-6 text-red-400 transition-all group-hover:scale-110" />
                  ) : (
                    <Volume2 className="w-6 h-6 text-[#64748b] transition-all group-hover:scale-110 group-hover:text-white" />
                  )}
                </TooltipTrigger>
                <TooltipContent>Click to Mute</TooltipContent>
              </Tooltip>

              <div className="relative flex items-center w-32 group">
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={volume}
                  onChange={(e) => {
                    const val = parseInt(e.target.value);
                    setVolume(val);
                    if (val > 0) setPrevVolume(val);
                  }}
                  className="w-full h-1 bg-white/10 rounded-full appearance-none cursor-pointer accent-[#3b82f6] hover:bg-white/20 transition-colors"
                  style={{
                    background: `linear-gradient(to right, #3b82f6 ${volume}%, rgba(255,255,255,0.1) ${volume}%)`
                  }}
                />
              </div>
            </div>

            <div className="h-10 w-[1px] bg-white/10 mx-2" />

            {/* Config Group */}
            <div className="flex items-center gap-6">
              <div className="flex gap-3">
                {VOICES.slice(0, 3).map(v => (
                  <button
                    key={v}
                    onClick={() => setVoice(v)}
                    className={`px-4 py-2 rounded-xl text-[10px] font-bold tracking-tighter transition-all duration-300 ${voice === v ? 'bg-[#3b82f6] text-white shadow-[0_0_15px_rgba(59,130,246,0.5)]' : 'bg-white/5 text-[#64748b] hover:bg-white/10'
                      }`}
                  >
                    {v.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>
          </TooltipProvider>
        </div>
      </footer>
    </div>
  );
}
