import { Shield, Zap, Activity, Globe, CheckCircle2, ArrowRight, Terminal, Search, Lock, Cpu, Database, Layout, BarChart3, Workflow, AlertCircle } from 'lucide-react';
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface LandingPageProps {
  onStart: () => void;
}

export default function LandingPage({ onStart }: LandingPageProps) {
  return (
    <div className="min-h-screen bg-[#0d0d0f] text-white font-sans overflow-x-hidden selection:bg-primary/30">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 bg-[#0d0d0f]/80 backdrop-blur-md border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-primary/20 p-2 rounded-lg">
              <Shield className="w-6 h-6 text-primary" />
            </div>
            <span className="font-bold text-xl tracking-tight uppercase">Aura Guard</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-muted/60 uppercase tracking-widest text-[10px]">
            <a href="#features" className="hover:text-primary transition-colors">Features</a>
            <a href="#operational-modes" className="hover:text-primary transition-colors">Operational Modes</a>
            <a href="#interop" className="hover:text-primary transition-colors">Interoperability</a>
          </div>
          <button 
            onClick={onStart}
            className="bg-primary hover:bg-primary/90 text-white px-6 py-2.5 rounded-full font-bold text-sm transition-all shadow-lg shadow-primary/20 flex items-center gap-2 group active:scale-95"
          >
            Launch Terminal
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-48 pb-32 px-6 overflow-hidden">
        {/* Background Gradients */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1200px] h-[700px] bg-primary/10 blur-[150px] rounded-full pointer-events-none -z-10" />
        <div className="absolute bottom-0 right-0 w-[600px] h-[600px] bg-accent/5 blur-[120px] rounded-full pointer-events-none -z-10" />

        <div className="max-w-6xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-primary text-[10px] font-black uppercase tracking-[0.2em] mb-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
            </span>
            Federated SRE Command Center
          </div>
          <h1 className="text-6xl md:text-8xl font-black tracking-tighter leading-[0.85] mb-10 animate-in fade-in slide-in-from-bottom-6 duration-700 max-w-5xl mx-auto">
            THE INTELLIGENT <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-primary/80 to-accent">WAR ROOM</span> FOR MODERN INFRASTRUCTURE
          </h1>
          <p className="text-xl md:text-2xl text-muted/50 max-w-3xl mx-auto mb-16 animate-in fade-in slide-in-from-bottom-8 duration-1000 leading-relaxed">
            Stop digging through dashboards. Aura Guard uses <span className="text-white/80 font-bold">Native MCP Federation</span> to reconstruct causality across your entire toolchain in seconds.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6 animate-in fade-in slide-in-from-bottom-10 duration-1000">
            <button 
              onClick={onStart}
              className="w-full sm:w-auto bg-primary hover:bg-primary/90 text-white px-12 py-5 rounded-2xl font-black text-xl transition-all shadow-2xl shadow-primary/30 flex items-center justify-center gap-4 group active:scale-95"
            >
              Enter Control Room
              <Play className="w-6 h-6 group-hover:translate-x-1 transition-transform fill-current" />
            </button>
            <button className="w-full sm:w-auto bg-white/5 hover:bg-white/10 border border-white/10 text-white px-12 py-5 rounded-2xl font-bold text-xl transition-all flex items-center justify-center gap-4">
              Documentation
            </button>
          </div>
        </div>

        {/* Dynamic Ticker */}
        <div className="max-w-7xl mx-auto mt-32 border-y border-white/5 py-6 overflow-hidden flex whitespace-nowrap gap-12 opacity-30 select-none">
            {[1,2,3].map(i => (
                <div key={i} className="flex gap-12 items-center animate-scroll">
                    <TickerItem icon={<Terminal className="w-4 h-4" />} label="L4 FEDERATION ACTIVE" />
                    <TickerItem icon={<Database className="w-4 h-4" />} label="CORAL_MCP_STDI0 CONNECTED" />
                    <TickerItem icon={<Globe className="w-4 h-4" />} label="AWS-US-EAST-1 HEALTHY" />
                    <TickerItem icon={<Shield className="w-4 h-4" />} label="CVE_OSV_SYNC_COMPLETE" />
                    <TickerItem icon={<Activity className="w-4 h-4" />} label="REALTIME_WS_STREAM_OK" />
                </div>
            ))}
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-40 px-6 relative bg-[#09090b]">
        <div className="max-w-7xl mx-auto">
          <div className="mb-24 text-center max-w-3xl mx-auto">
            <h2 className="text-xs font-black text-primary uppercase tracking-[0.4em] mb-6">Core Architecture</h2>
            <h3 className="text-5xl md:text-6xl font-black tracking-tight mb-8">EVIDENCE-FIRST INVESTIGATION</h3>
            <p className="text-muted/50 text-lg">We moved beyond the "CLI wrapper" hack. Aura Guard implements the gold standard of agentic observability.</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            <FeatureCard 
                icon={<Cpu className="w-10 h-10 text-primary" />}
                title="Native MCP Federation"
                desc="Aura Guard talks to Coral as a living MCP server. This enables dynamic tool discovery and high-performance cross-source joins that static CLI wrappers can't match."
            />
            <FeatureCard 
                icon={<Workflow className="w-10 h-10 text-accent" />}
                title="Incremental Discovery"
                desc="Stop using fragile Mega Joins. Our agent uses Chain of Thought to perform targeted sequential queries (Logs → Time → Commits), mimicking a senior SRE's brain."
            />
            <FeatureCard 
                icon={<Lock className="w-10 h-10 text-primary" />}
                title="Evidence-Based Reporting"
                desc="Zero hallucinations. Every finding is cited with [CloudWatch] or [GitHub] prefixes and tagged with Confidence Levels based on temporal alignment."
            />
          </div>
        </div>
      </section>

      {/* Operational Modes */}
      <section id="operational-modes" className="py-40 px-6 bg-[#0d0d0f] relative overflow-hidden">
        <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-accent/5 blur-[150px] rounded-full pointer-events-none" />
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-24 items-center">
            <div>
                <h2 className="text-xs font-black text-accent uppercase tracking-[0.4em] mb-6">Execution Contexts</h2>
                <h3 className="text-5xl font-black tracking-tight mb-8 leading-tight text-white/90">BUILT FOR DEMOS.<br/>HARDENED FOR PROD.</h3>
                <div className="space-y-8 mt-12">
                    <div className="flex gap-6 p-6 rounded-2xl bg-white/[0.02] border border-white/5 hover:bg-white/[0.04] transition-colors">
                        <div className="p-3 bg-accent/20 rounded-xl h-fit mt-1"><Layout className="w-6 h-6 text-accent" /></div>
                        <div>
                            <h4 className="text-xl font-bold mb-2">Live Federation Mode</h4>
                            <p className="text-muted/50 text-sm leading-relaxed text-white/40 font-medium">Real-time connection to AWS, GitHub, and Linear via Coral. Best for actual incident response and automated triage in production environments.</p>
                        </div>
                    </div>
                    <div className="flex gap-6 p-6 rounded-2xl bg-white/[0.02] border border-white/5 hover:bg-white/[0.04] transition-colors">
                        <div className="p-3 bg-primary/20 rounded-xl h-fit mt-1"><BarChart3 className="w-6 h-6 text-primary" /></div>
                        <div>
                            <h4 className="text-xl font-bold mb-2">Resilient Fixtures Mode</h4>
                            <p className="text-muted/50 text-sm leading-relaxed text-white/40 font-medium">Automatic fallback to curated JSON fixtures when APIs are unreachable or for low-latency demonstrations. Ensures your war room never goes dark.</p>
                        </div>
                    </div>
                </div>
            </div>
            <div className="relative group">
                <div className="absolute inset-0 bg-primary/20 blur-3xl group-hover:bg-primary/30 transition-all duration-1000 -z-10 opacity-30" />
                <div className="glass-panel p-2 rounded-3xl border border-white/10 overflow-hidden shadow-2xl">
                    <div className="bg-[#09090b] rounded-2xl p-6 font-mono text-[10px] space-y-3 opacity-90 grayscale group-hover:grayscale-0 transition-all duration-700">
                        <div className="flex justify-between items-center opacity-40">
                            <span>MODE: PRODUCTION_READY</span>
                            <span>latency: 142ms</span>
                        </div>
                        <div className="space-y-1">
                            <div className="text-primary font-bold">SQL_INTERCEPTOR: intercepting_query_042</div>
                            <div className="text-white/30">&gt; checking_cache... MISSED</div>
                            <div className="text-white/30">&gt; querying_coral_mcp... [SUCCESS]</div>
                            <div className="text-accent">&gt; 12 rows joined from [github, cloudwatch]</div>
                        </div>
                        <div className="h-24 w-full bg-white/5 rounded border border-white/5 flex items-center justify-center text-white/10 italic">
                            CAUSAL_GRAPH_RENDERING...
                        </div>
                    </div>
                </div>
            </div>
        </div>
      </section>

      {/* System Interoperability */}
      <section id="interop" className="py-40 px-6 bg-[#09090b]">
          <div className="max-w-7xl mx-auto">
            <div className="flex flex-col md:flex-row justify-between items-end gap-12 mb-24">
                <div className="max-w-2xl">
                    <h2 className="text-xs font-black text-primary uppercase tracking-[0.4em] mb-6">Interoperability</h2>
                    <h3 className="text-5xl font-black tracking-tight text-white/90">THE ENTIRE STACK, ONE INTERFACE.</h3>
                </div>
                <div className="text-muted/40 font-mono text-[10px] uppercase tracking-widest pb-2 border-b border-white/5">
                    Supported Federations: 12+ Sources
                </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <InteropCard icon={<CloudWatchIcon />} label="CloudWatch" />
                <InteropCard icon={<GitHubIcon />} label="GitHub" />
                <InteropCard icon={<LinearIcon />} label="Linear" />
                <InteropCard icon={<OSVIcon />} label="OSV.dev" />
                <InteropCard icon={<SlackIcon />} label="Slack" />
                <InteropCard icon={<DatadogIcon />} label="Datadog" />
                <InteropCard icon={<SentryIcon />} label="Sentry" />
                <InteropCard icon={<PagerDutyIcon />} label="PagerDuty" />
            </div>
          </div>
      </section>

      {/* Actionable Triage Section */}
      <section className="py-40 px-6 bg-[#0d0d0f] relative border-t border-white/5">
          <div className="max-w-4xl mx-auto text-center">
              <div className="bg-primary/20 w-20 h-20 rounded-3xl flex items-center justify-center mb-12 mx-auto shadow-2xl shadow-primary/20">
                  <Zap className="w-10 h-10 text-primary" />
              </div>
              <h2 className="text-5xl md:text-6xl font-black tracking-tight mb-8 leading-[1.1]">FROM ROOT CAUSE TO <span className="text-accent italic">AUTO-REMEDIATION</span></h2>
              <p className="text-muted/50 text-xl mb-16 max-w-2xl mx-auto">Aura Guard doesn't just tell you what's wrong. It generates the exact shell commands needed to stabilize your environment.</p>
              <div className="p-8 rounded-3xl bg-white/[0.02] border border-white/5 font-mono text-sm text-left max-w-xl mx-auto shadow-inner">
                  <div className="flex gap-2 mb-6">
                      <div className="w-2 h-2 rounded-full bg-red-500/50" />
                      <div className="w-2 h-2 rounded-full bg-yellow-500/50" />
                      <div className="w-2 h-2 rounded-full bg-green-500/50" />
                  </div>
                  <div className="text-white/40 mb-2">// Suggested Rollback for [api-billing]</div>
                  <div className="text-primary font-bold text-lg animate-pulse">$ git revert 8f2d9c1</div>
                  <div className="mt-6 flex justify-between items-center opacity-40 text-[10px]">
                      <span>Confidence: HIGH (98%)</span>
                      <span>Source: GitHub-Commits</span>
                  </div>
              </div>
          </div>
      </section>

      {/* Final CTA */}
      <section className="py-40 px-6 relative overflow-hidden bg-primary/5">
        <div className="absolute inset-0 bg-gradient-to-b from-[#0d0d0f] to-transparent pointer-events-none" />
        <div className="max-w-5xl mx-auto text-center relative z-10">
          <h2 className="text-5xl md:text-7xl font-black tracking-tighter mb-12">READY TO DEPLOY?</h2>
          <button 
            onClick={onStart}
            className="bg-primary hover:bg-primary/90 text-white px-16 py-6 rounded-2xl font-black text-2xl transition-all shadow-2xl shadow-primary/40 flex items-center justify-center gap-6 mx-auto group active:scale-95"
          >
            Launch SRE Terminal
            <ArrowRight className="w-8 h-8 group-hover:translate-x-2 transition-transform" />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-20 border-t border-white/5 px-6 bg-[#09090b]">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-12">
            <div className="flex flex-col items-center md:items-start gap-4">
                <div className="flex items-center gap-3 opacity-80">
                    <Shield className="w-8 h-8 text-primary" />
                    <span className="font-bold text-2xl uppercase tracking-tighter">Aura Guard</span>
                </div>
                <p className="text-muted/30 text-[10px] font-black uppercase tracking-[0.3em]">Next-Gen Incident Response</p>
            </div>
            
            <div className="flex flex-col items-center md:items-end gap-6">
                <div className="flex gap-12 text-muted/40 text-[10px] font-black uppercase tracking-widest">
                    <a href="#" className="hover:text-primary transition-colors">GitHub</a>
                    <a href="#" className="hover:text-primary transition-colors">Documentation</a>
                    <a href="#" className="hover:text-primary transition-colors">Terms</a>
                </div>
                <div className="text-muted/20 text-[9px] font-mono">
                    COPYRIGHT &copy; 2026 CORAL_HACKATHON_CHALLENGE // ALL_SYSTEMS_OPERATIONAL
                </div>
            </div>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({ icon, title, desc }: any) {
    return (
        <div className="p-10 rounded-3xl bg-white/[0.02] border border-white/5 hover:border-primary/20 transition-all group relative overflow-hidden shadow-2xl">
            <div className="absolute top-0 right-0 p-8 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity duration-1000 -mr-4 -mt-4">
                {icon}
            </div>
            <div className="mb-10 group-hover:scale-110 transition-transform duration-500 origin-left">{icon}</div>
            <h4 className="text-2xl font-bold mb-4 tracking-tight">{title}</h4>
            <p className="text-muted/50 text-base leading-relaxed font-medium">{desc}</p>
        </div>
    );
}

function InteropCard({ icon, label }: any) {
    return (
        <div className="p-8 rounded-2xl bg-white/[0.02] border border-white/5 flex flex-col items-center gap-4 hover:bg-white/[0.05] hover:border-white/10 transition-all group grayscale opacity-40 hover:grayscale-0 hover:opacity-100 shadow-lg">
            <div className="w-12 h-12 flex items-center justify-center mb-2 group-hover:scale-110 transition-transform duration-500 text-white/80 group-hover:text-primary">
                {icon}
            </div>
            <span className="text-[10px] font-black uppercase tracking-widest text-muted/60 group-hover:text-white transition-colors">{label}</span>
        </div>
    );
}

function TickerItem({ icon, label }: any) {
    return (
        <div className="flex items-center gap-3">
            {icon}
            <span className="font-mono font-bold text-[11px] tracking-widest">{label}</span>
            <span className="text-white/20">///</span>
        </div>
    );
}

function Play({ className, ...props }: any) {
    return (
        <svg 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="3" 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            className={className} 
            {...props}
        >
            <polygon points="6 3 20 12 6 21 6 3" />
        </svg>
    );
}

// --- Icons (SVG Placeholders) ---
function CloudWatchIcon() { return <Activity />; }
function GitHubIcon() { return <Globe />; }
function LinearIcon() { return <Layout />; }
function OSVIcon() { return <Shield />; }
function SlackIcon() { return <Activity />; }
function DatadogIcon() { return <BarChart3 />; }
function SentryIcon() { return <AlertCircle />; }
function PagerDutyIcon() { return <Zap />; }
