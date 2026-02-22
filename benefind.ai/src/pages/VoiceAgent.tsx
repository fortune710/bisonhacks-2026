import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useConversation } from '@11labs/react';
import { motion, AnimatePresence } from 'motion/react';
import {
    Mic,
    MicOff,
    MessageSquare,
    Phone,
    PhoneOff,
    Send,
    ChevronLeft,
    ShoppingBasket,
    Volume2,
    VolumeX,
    ToggleLeft,
    ToggleRight,
} from 'lucide-react';

const AGENT_ID = import.meta.env.VITE_ELEVENLABS_AGENT_ID || '';

interface Message {
    id: string;
    role: 'user' | 'agent';
    text: string;
    timestamp: Date;
}

export default function VoiceAgent() {
    const navigate = useNavigate();
    const [messages, setMessages] = useState<Message[]>([]);
    const [isTextMode, setIsTextMode] = useState(false);
    const [textInput, setTextInput] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    const addMessage = useCallback((role: 'user' | 'agent', text: string) => {
        setMessages((prev) => [
            ...prev,
            {
                id: `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
                role,
                text,
                timestamp: new Date(),
            },
        ]);
    }, []);

    const conversation = useConversation({
        onMessage: (message: { message: string; source: string }) => {
            if (message.source === 'ai') {
                addMessage('agent', message.message);
            } else if (message.source === 'user') {
                addMessage('user', message.message);
            }
        },
        onError: (error: string) => {
            console.error('Eleven Labs error:', error);
        },
    });

    const { status, isSpeaking } = conversation;
    const isConnected = status === 'connected';

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Focus input in text mode
    useEffect(() => {
        if (isTextMode && isConnected) {
            inputRef.current?.focus();
        }
    }, [isTextMode, isConnected]);

    const handleStartSession = async () => {
        console.log('Starting session...');
        try {
            await navigator.mediaDevices.getUserMedia({ audio: true });
            await conversation.startSession({
                agentId: AGENT_ID,
                ...(isTextMode ? {} : {}),
            });
        } catch (err) {
            console.error('Failed to start session:', err);
        }
    };

    const handleEndSession = async () => {
        try {
            await conversation.endSession();
        } catch (err) {
            console.error('Failed to end session:', err);
        }
    };

    const handleToggleMode = async () => {
        const wasConnected = isConnected;
        if (wasConnected) {
            await handleEndSession();
        }
        setIsTextMode((prev) => !prev);
        // If was connected, restart in new mode after a small delay
        if (wasConnected) {
            setTimeout(() => {
                handleStartSession();
            }, 300);
        }
    };

    const handleSendText = () => {
        if (!textInput.trim() || !isConnected) return;
        addMessage('user', textInput.trim());
        conversation.sendUserMessage(textInput.trim());
        setTextInput('');
        inputRef.current?.focus();
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendText();
        }
    };

    return (
        <div className="min-h-screen bg-[#0a0a0f] text-white font-sans flex flex-col">
            {/* Header */}
            <header className="border-b border-white/5 bg-[#0a0a0f]/90 backdrop-blur-xl sticky top-0 z-50">
                <div className="max-w-4xl mx-auto px-6 h-16 flex items-center justify-between">
                    <button
                        onClick={() => navigate('/')}
                        className="flex items-center gap-2 text-white/50 hover:text-white transition-colors"
                    >
                        <ChevronLeft className="w-4 h-4" />
                        <div className="flex items-center gap-2">
                            <div className="w-7 h-7 bg-emerald-600 rounded-lg flex items-center justify-center">
                                <ShoppingBasket className="text-white w-4 h-4" />
                            </div>
                            <span className="font-bold text-white/90">
                                benefind<span className="text-emerald-500">.ai</span>
                            </span>
                        </div>
                    </button>

                    {/* Voice / Text Toggle */}
                    <button
                        onClick={handleToggleMode}
                        className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 transition-all text-sm"
                    >
                        {isTextMode ? (
                            <>
                                <MessageSquare className="w-4 h-4 text-emerald-400" />
                                <span className="text-white/70">Text</span>
                                <ToggleRight className="w-5 h-5 text-emerald-400" />
                            </>
                        ) : (
                            <>
                                <Mic className="w-4 h-4 text-emerald-400" />
                                <span className="text-white/70">Voice</span>
                                <ToggleLeft className="w-5 h-5 text-white/40" />
                            </>
                        )}
                    </button>
                </div>
            </header>

            {/* Main Content */}
            <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full px-6">
                {/* Audio Visualizer (voice mode only) */}
                {!isTextMode && isConnected && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex items-center justify-center py-8"
                    >
                        <div className="flex items-end gap-1.5 h-20">
                            {Array.from({ length: 24 }).map((_, i) => (
                                <motion.div
                                    key={i}
                                    className="w-1.5 rounded-full"
                                    style={{
                                        background: `linear-gradient(to top, #10b981, #34d399)`,
                                    }}
                                    animate={{
                                        height: isSpeaking
                                            ? [
                                                8 + Math.random() * 12,
                                                20 + Math.random() * 50,
                                                8 + Math.random() * 12,
                                            ]
                                            : [6, 10, 6],
                                        opacity: isSpeaking ? [0.6, 1, 0.6] : [0.15, 0.25, 0.15],
                                    }}
                                    transition={{
                                        duration: isSpeaking ? 0.4 + Math.random() * 0.3 : 2,
                                        repeat: Infinity,
                                        ease: 'easeInOut',
                                        delay: i * 0.04,
                                    }}
                                />
                            ))}
                        </div>
                        <div className="ml-4 flex items-center gap-2">
                            {isSpeaking ? (
                                <Volume2 className="w-5 h-5 text-emerald-400 animate-pulse" />
                            ) : (
                                <VolumeX className="w-5 h-5 text-white/20" />
                            )}
                            <span className="text-xs text-white/40 uppercase tracking-widest font-medium">
                                {isSpeaking ? 'Speaking' : 'Listening'}
                            </span>
                        </div>
                    </motion.div>
                )}

                {/* Connection Control */}
                {!isConnected && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="flex-1 flex flex-col items-center justify-center gap-8 py-20"
                    >
                        <div className="text-center space-y-3">
                            <h1 className="text-3xl font-bold">
                                AI Food Assistance
                            </h1>
                            <p className="text-white/40 max-w-md">
                                {isTextMode
                                    ? 'Type your questions about SNAP eligibility, food resources, and more.'
                                    : 'Speak with our AI assistant about SNAP eligibility, nearby food resources, and more.'}
                            </p>
                        </div>
                        <button
                            onClick={handleStartSession}
                            className="group relative"
                        >
                            {/* Pulse rings */}
                            <div className="absolute inset-0 rounded-full bg-emerald-500/20 animate-ping" />
                            <div className="absolute -inset-3 rounded-full bg-emerald-500/10 animate-pulse" />
                            <div className="relative w-24 h-24 rounded-full bg-gradient-to-br from-emerald-500 to-emerald-700 flex items-center justify-center shadow-2xl shadow-emerald-500/30 group-hover:scale-110 transition-transform">
                                {isTextMode ? (
                                    <MessageSquare className="w-10 h-10 text-white" />
                                ) : (
                                    <Phone className="w-10 h-10 text-white" />
                                )}
                            </div>
                        </button>
                        <span className="text-sm text-white/30 uppercase tracking-widest">
                            Tap to {isTextMode ? 'start chat' : 'start conversation'}
                        </span>
                    </motion.div>
                )}

                {/* Messages Feed */}
                {isConnected && (
                    <div className="flex-1 overflow-y-auto py-4 space-y-4 min-h-0">
                        <AnimatePresence initial={false}>
                            {messages.map((msg) => (
                                <motion.div
                                    key={msg.id}
                                    initial={{ opacity: 0, y: 10, scale: 0.97 }}
                                    animate={{ opacity: 1, y: 0, scale: 1 }}
                                    transition={{ duration: 0.25 }}
                                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                                >
                                    <div
                                        className={`max-w-[80%] px-5 py-3 rounded-2xl ${msg.role === 'user'
                                            ? 'bg-emerald-600 text-white rounded-br-sm'
                                            : 'bg-white/5 border border-white/10 text-white/90 rounded-bl-sm'
                                            }`}
                                    >
                                        <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                                        <p className="text-[10px] mt-1 opacity-40">
                                            {msg.timestamp.toLocaleTimeString([], {
                                                hour: '2-digit',
                                                minute: '2-digit',
                                            })}
                                        </p>
                                    </div>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                        <div ref={messagesEndRef} />
                    </div>
                )}

                {/* Bottom Controls */}
                {isConnected && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="sticky bottom-0 py-4 bg-gradient-to-t from-[#0a0a0f] via-[#0a0a0f] to-transparent"
                    >
                        {isTextMode ? (
                            /* Text Input */
                            <div className="flex items-center gap-3">
                                <div className="flex-1 relative">
                                    <input
                                        ref={inputRef}
                                        type="text"
                                        value={textInput}
                                        onChange={(e) => setTextInput(e.target.value)}
                                        onKeyDown={handleKeyDown}
                                        placeholder="Type your message..."
                                        className="w-full bg-white/5 border border-white/10 rounded-2xl px-5 py-4 text-white placeholder-white/30 focus:ring-2 focus:ring-emerald-500/50 focus:border-transparent outline-none transition-all"
                                    />
                                </div>
                                <button
                                    onClick={handleSendText}
                                    disabled={!textInput.trim()}
                                    className="w-12 h-12 rounded-xl bg-emerald-600 hover:bg-emerald-700 disabled:bg-white/5 disabled:text-white/20 text-white flex items-center justify-center transition-all"
                                >
                                    <Send className="w-5 h-5" />
                                </button>
                                <button
                                    onClick={handleEndSession}
                                    className="w-12 h-12 rounded-xl bg-red-500/20 hover:bg-red-500/30 text-red-400 flex items-center justify-center transition-all"
                                >
                                    <PhoneOff className="w-5 h-5" />
                                </button>
                            </div>
                        ) : (
                            /* Voice Controls */
                            <div className="flex items-center justify-center gap-6">
                                <div className="flex items-center gap-3 px-5 py-3 rounded-2xl bg-white/5 border border-white/10">
                                    <div
                                        className={`w-3 h-3 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-white/20'
                                            }`}
                                    />
                                    <span className="text-sm text-white/50">
                                        {isSpeaking ? 'Agent speaking...' : 'Listening...'}
                                    </span>
                                </div>
                                <button
                                    onClick={handleEndSession}
                                    className="w-14 h-14 rounded-full bg-red-500 hover:bg-red-600 text-white flex items-center justify-center shadow-lg shadow-red-500/30 transition-all hover:scale-110"
                                >
                                    <PhoneOff className="w-6 h-6" />
                                </button>
                            </div>
                        )}
                    </motion.div>
                )}
            </div>
        </div>
    );
}
