<#import "template.ftl" as layout>
<@layout.registrationLayout displayInfo=(social.displayInfo)!false; section>
    <#if section = "header">
        <div class="custom-nav">
            <div class="brand-wrapper" style="display: flex; align-items: center; gap: 12px;">
                <img src="${url.resourcesPath}/img/aura-logo.png" alt="Aura AI" style="height: 48px; width: auto; object-fit: contain;">
                <span class="brand-text" style="font-size: 24px; font-weight: 700; color: white; letter-spacing: -0.02em;">AURA AI</span>
            </div>
        </div>
    <#elseif section = "form">
        <div class="aura-bg">
            <div class="aura-1"></div>
            <div class="aura-2"></div>
        </div>

        <main class="main-layout">
            
            <#-- Left: Hero Content -->
            <div class="hero-content">
                <#-- Floating Neural Status Bubble -->
                <div class="floating-bubble">
                    <div class="bubble-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 1 1-7.6-7.6 8.38 8.38 0 0 1 3.8.9L21 3z"/></svg>
                    </div>
                    <div class="bubble-labels">
                        <div class="bubble-tag">Neural Status</div>
                        <div class="bubble-value">ANALYZING...</div>
                    </div>
                </div>

                <span class="vocal-intel-tag">Vocal Intelligence v3.2</span>
                <h1 class="hero-title">Conversations that <br><span>transcend technology.</span></h1>
                <p class="hero-description">Experience the next generation of Aura AI. Human-grade responses with sub-200ms latency, supporting 40+ languages natively.</p>
                
                <#-- Decorative Phone Mockup -->
                <div class="phone-mockup" style="margin-top: 20px;">
                    <div class="phone-notch"></div>
                    <div class="phone-screen">
                        <div style="margin-top: 48px; text-align: center;">
                            <div style="width: 80px; height: 80px; background: rgba(56,189,248,0.2); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto; border: 1px solid rgba(56,189,248,0.3);">
                                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
                            </div>
                            <h3 style="color: white; margin-top: 16px; font-weight: 600; font-size: 20px;">Aura AI</h3>
                            <span style="color: #38bdf8; font-family: monospace; font-size: 14px; margin-top: 4px;">04:21</span>
                        </div>

                        <#-- Animated Voice Wave -->
                        <div class="voice-wave">
                            <div class="wave-bar"></div>
                            <div class="wave-bar"></div>
                            <div class="wave-bar"></div>
                            <div class="wave-bar"></div>
                            <div class="wave-bar"></div>
                            <div class="wave-bar"></div>
                            <div class="wave-bar"></div>
                            <div class="wave-bar"></div>
                        </div>

                        <#-- Call Controls Mockup -->
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; width: 100%; padding: 0 16px; margin-bottom: 32px;">
                            <div style="display: flex; flex-direction: column; align-items: center; gap: 8px;">
                                <div style="width: 48px; height: 48px; border-radius: 50%; background: rgba(255,255,255,0.1); display: flex; align-items: center; justify-content: center;">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" stroke-width="2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/></svg>
                                </div>
                                <span style="font-size: 8px; color: rgba(255,255,255,0.5); font-weight: 700; text-transform: uppercase;">Mute</span>
                            </div>
                            <div style="display: flex; flex-direction: column; align-items: center; gap: 8px;">
                                <div style="width: 48px; height: 48px; border-radius: 50%; background: rgba(255,255,255,0.1); display: flex; align-items: center; justify-content: center;">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/><line x1="15" y1="3" x2="15" y2="21"/></svg>
                                </div>
                                <span style="font-size: 8px; color: rgba(255,255,255,0.5); font-weight: 700; text-transform: uppercase;">Keypad</span>
                            </div>
                            <div style="display: flex; flex-direction: column; align-items: center; gap: 8px;">
                                <div style="width: 48px; height: 48px; border-radius: 50%; background: rgba(255,255,255,0.1); display: flex; align-items: center; justify-content: center;">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
                                </div>
                                <span style="font-size: 8px; color: rgba(255,255,255,0.5); font-weight: 700; text-transform: uppercase;">Speaker</span>
                            </div>
                        </div>

                        <#-- End Call Button -->
                        <div style="width: 64px; height: 64px; border-radius: 50%; background: #ef4444; display: flex; align-items: center; justify-content: center; box-shadow: 0 10px 20px rgba(239, 68, 68, 0.3); margin-bottom: 24px;">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="white" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="transform: rotate(135deg);"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l2.27-2.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
                        </div>
                    </div>
                </div>
            </div>

            <#-- Right: Login Card -->
            <div id="kc-form">
                <div id="kc-form-wrapper" class="card-pf">
                    <h1>Access Node</h1>
                    <span class="card-subtitle">Secured Neural Gateway</span>

                    <#if realm.password>
                        <form id="kc-form-login" class="space-y-6" onsubmit="login.disabled = true; return true;" action="${url.loginAction}" method="post">
                            <div class="form-group">
                                <label for="username">Identity Protocol</label>
                                <div class="input-container">
                                    <div class="input-icon">
                                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                                    </div>
                                    <input id="username" class="form-control" name="username" value="${(login.username!'')}"  type="text" autofocus autocomplete="off" placeholder="Neural ID" />
                                </div>
                            </div>

                            <div class="form-group">
                                <label for="password">Secure Token</label>
                                <div class="input-container">
                                    <div class="input-icon">
                                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                                    </div>
                                    <input id="password" class="form-control" name="password" type="password" autocomplete="off" placeholder="••••••••" />
                                </div>
                            </div>

                            <div id="kc-form-buttons">
                                <button class="btn-primary" name="login" id="kc-login" type="submit">
                                    INITIALIZE NODE
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                                </button>
                            </div>
                        </form>
                    </#if>
                    
                    <div style="margin-top: 40px; pt-10; border-top: 1px solid rgba(255,255,255,0.05); display: flex; flex-direction: column; align-items: center; gap: 24px;">
                        <button style="background: none; border: none; color: rgba(255,255,255,0.4); font-size: 10px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.2em; cursor: pointer;">Forgot Access Code?</button>
                        <p style="color: rgba(255,255,255,0.2); font-size: 9px; text-transform: uppercase; font-weight: 900; letter-spacing: 0.2em;">
                            New instance? <a href="${url.registrationUrl}" style="color: #38bdf8; text-decoration: none;">Provision ID</a>
                        </p>
                    </div>
                </div>
            </div>
        </main>
    </#if>
</@layout.registrationLayout>
