import { useState, useEffect, useRef, useCallback } from 'react';
import { Shield, Zap, Terminal, AlertTriangle, CheckCircle2, Loader2, BarChart3, Activity, Command, Cpu, Globe, History, Play, RotateCcw, ArrowRight, Database, Bell, Settings, Brain } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import LandingPage from './components/LandingPage';

// --- Utils ---
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// --- Types ---
type Tab = 'configuration' | 'org-scan' | 'blast-radius' | 'incident-response';
interface Report {
  report: string;
  status: 'clean' | 'vulnerable' | 'impacted' | 'investigating';
  count?: number;
  impact_score?: number;
  remediation?: string;
  remediation_status?: 'SUCCESS' | 'PENDING';
  rows?: any[];
  tech_stack?: string;
}

interface StreamEvent {
  type: 'query_start' | 'query_success' | 'query_error';
  sql?: string;
  elapsed_ms?: number;
  row_count?: number;
  error?: string;
  agentic?: boolean;
  timestamp: string;
}

interface DiscoveryItem {
  id: string;
  type: 'error' | 'audit' | 'impact';
  title: string;
  description: string;
  tab: Tab;
  params: any;
}

const API_BASE = 'http://localhost:8000';
const WS_BASE = 'ws://localhost:8000/ws/stream';

export default function App() {
  const [route, setRoute] = useState(() => window.location.pathname === '/demo' ? '/demo' : '/');
  const [activeTab, setActiveTab] = useState<Tab>('org-scan');
  
  // DECOUPLED STATE
  const [loadings, setLoadings] = useState<Record<string, boolean>>({});
  const [reports, setReports] = useState<Record<string, Report | null>>({});
  const [errors, setErrors] = useState<Record<string, string | null>>({});
  
  const [remediating, setRemediating] = useState(false);
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [sidebarWidth, setSidebarWidth] = useState(300);
  const [isResizing, setIsResizing] = useState(false);
  const [discoveryItems] = useState<DiscoveryItem[] | null>([
    {
        id: "error-1",
        type: "error",
        title: "🚨 Anomalous Error Spike in 'aura-guard-node-service'",
        description: "CloudWatch detected 12 errors in the last 15m. Suspected regression in chunking logic.",
        tab: "incident-response",
        params: {owner: "Rohan-Hazari", service: "aura-guard-node-service", logGroup: "Filegroup/processor"}
    },
    {
        id: "audit-1",
        type: "audit",
        title: "🟡 Security Audit Required: recent PRs",
        description: "Recent PRs in 'aura-guard-node-service' modify package.json. Automated delta-scan recommended.",
        tab: "org-scan",
        params: {owner: "Rohan-Hazari", repo: "aura-guard-node-service"}
    }
  ]);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Form States
  const [owner, setOwner] = useState('Rohan-Hazari');
  const [repo, setRepo] = useState('aura-guard-node-service');
  const [pr, setPr] = useState('');
  const [libFile, setLibFile] = useState('express');
  const [service, setService] = useState('aura-guard-node-service');
  const [logGroup, setLogGroup] = useState('Filegroup/processor');

  const startResizing = useCallback(() => setIsResizing(true), []);
  const stopResizing = useCallback(() => setIsResizing(false), []);
  const resize = useCallback((e: MouseEvent) => {
    if (isResizing) setSidebarWidth(e.clientX);
  }, [isResizing]);

  useEffect(() => {
    const handlePopState = () => {
      setRoute(window.location.pathname === '/demo' ? '/demo' : '/');
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigateToDemo = () => {
    if (window.location.pathname !== '/demo') {
      window.history.pushState({}, '', '/demo');
    }
    setRoute('/demo');
  };

  useEffect(() => {
    if (route !== '/demo') return;
    
    const ws = new WebSocket(WS_BASE);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const timestamp = new Date().toLocaleTimeString();
      setEvents(prev => [{ ...data, timestamp }, ...prev].slice(0, 50));
    };
    return () => ws.close();
  }, [route]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = 0;
    }
  }, [events]);

  useEffect(() => {
    window.addEventListener("mousemove", resize);
    window.addEventListener("mouseup", stopResizing);
    return () => {
      window.removeEventListener("mousemove", resize);
      window.removeEventListener("mouseup", stopResizing);
    };
  }, [resize, stopResizing]);

  const handleRunScan = async (overrideTab?: Tab, overrideParams?: any) => {
    const targetTab = overrideTab || activeTab;
    const targetOwner = overrideParams?.owner || owner;

    setLoadings(prev => ({ ...prev, [targetTab]: true }));
    setErrors(prev => ({ ...prev, [targetTab]: null }));
    setReports(prev => ({ ...prev, [targetTab]: null }));

    try {
      let endpoint = '';
      let params = `owner=${targetOwner}`;

      if (targetTab === 'org-scan') {
        endpoint = '/api/org-scan';
      } else if (targetTab === 'blast-radius') {
        endpoint = '/api/blast-radius';
        params += `&file=${overrideParams?.file || libFile}`;
      } else if (targetTab === 'incident-response') {
        endpoint = '/api/incident-triage';
        params += `&service=${overrideParams?.service || service}&log_group=${overrideParams?.logGroup || logGroup}`;
      }

      const res = await fetch(`${API_BASE}${endpoint}?${params}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rows: [] }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to run audit');
      }

      const data = await res.json();
      setReports(prev => ({ ...prev, [targetTab]: data }));
    } catch (err: any) {
      setErrors(prev => ({ ...prev, [targetTab]: err.message }));
    } finally {
      setLoadings(prev => ({ ...prev, [targetTab]: false }));
    }
  };

  const handleDiscoveryAction = (item: DiscoveryItem) => {
      setActiveTab(item.tab);
      if (item.params.owner) setOwner(item.params.owner);
      if (item.params.repo) setRepo(item.params.repo);
      if (item.params.pr) setPr(item.params.pr);
      if (item.params.file) setLibFile(item.params.file);
      if (item.params.service) setService(item.params.service);
      
      // Execute the scan for them
      handleRunScan(item.tab, item.params);
  };

  const handleRemediate = async () => {
    setRemediating(true);
    await new Promise(r => setTimeout(r, 2000));
    setReports(prev => {
        const activeReport = prev[activeTab];
        if (!activeReport) return prev;
        return {
            ...prev,
            [activeTab]: { ...activeReport, remediation_status: 'SUCCESS' }
        };
    });
    setRemediating(false);
  };

  if (route !== '/demo') {
    return <LandingPage onStart={navigateToDemo} />;
  }

  return (
    <div className={cn("flex h-screen bg-background text-slate-100 font-sans overflow-hidden", isResizing && "cursor-col-resize select-none")}>
      {/* Sidebar */}
      <aside style={{ width: sidebarWidth }} className="bg-[#111827] border-r border-slate-700/70 flex flex-col shrink-0 relative transition-[width] duration-75 shadow-2xl">
        <div onMouseDown={startResizing} className={cn("absolute top-0 right-0 w-1 h-full cursor-col-resize hover:bg-sky-400/70 transition-colors z-50", isResizing && "bg-sky-400/70")} />
        
        <div className="p-6 flex items-center gap-3 border-b border-slate-700/70">
          <div className="bg-sky-500/15 p-2 rounded-lg border border-sky-400/20">
            <Shield className="w-6 h-6 text-sky-300" />
          </div>
          <h1 className="font-bold text-lg tracking-tight">Aura Guard</h1>
        </div>

        <nav className="p-4 space-y-2 overflow-y-auto flex-1">
          <div className="px-2 mb-4">
              <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-4">Workflows</h3>
              <div className="space-y-2">
                <TabButton active={activeTab === 'configuration'} onClick={() => setActiveTab('configuration')} icon={<Settings className="w-4 h-4" />} label="Configuration" desc="Global scan parameters" />
                <TabButton active={activeTab === 'org-scan'} onClick={() => setActiveTab('org-scan')} icon={<Globe className="w-4 h-4" />} label="Comprehensive Scan" desc="Org & PR Security Audit" />
                <TabButton active={activeTab === 'blast-radius'} onClick={() => setActiveTab('blast-radius')} icon={<Zap className="w-4 h-4" />} label="Blast Radius" desc="Downstream Impact Analysis" />
                <TabButton active={activeTab === 'incident-response'} onClick={() => setActiveTab('incident-response')} icon={<Activity className="w-4 h-4" />} label="Incident Triage" desc="Autonomous Root Cause" />
              </div>
          </div>
          
          <div className="border-t border-slate-700/70 pt-6 px-2">
            <h3 className="text-[10px] font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2 mb-4">
              <History className="w-3 h-3" />
              Reasoning Trace
            </h3>
            <div ref={scrollRef} className="space-y-3 font-mono text-[10px]">
              {events.length === 0 && <div className="text-slate-400 italic">Awaiting telemetry...</div>}
              {events.map((ev, i) => (
                <div key={i} className={cn("p-3 rounded-lg border border-slate-700/70 bg-slate-950/40", ev.type === 'query_error' ? "border-red-400/40 bg-red-500/10" : ev.type === 'query_success' ? "border-emerald-400/30" : "")}>
                  <div className="flex justify-between mb-1 text-slate-400">
                    <div className="flex gap-2 items-center">
                      <span>[{ev.timestamp}]</span>
                      {ev.agentic && <span className="bg-sky-500/15 text-sky-200 px-1 rounded-[2px] font-black text-[7px] border border-sky-400/20 flex items-center gap-0.5"><Brain className="w-2 h-2" /> AGENT</span>}
                    </div>
                    <span>{ev.type.toUpperCase()}</span>
                  </div>
                  {ev.sql && <div className="text-sky-300 break-words line-clamp-2 text-[9px]">{ev.sql}</div>}
                  {ev.elapsed_ms !== undefined && <div className="text-emerald-300 flex items-center gap-1 mt-1"><Database className="w-2.5 h-2.5" /> {ev.elapsed_ms}ms</div>}
                  {ev.error && <div className="text-red-300">{ev.error}</div>}
                </div>
              ))}
            </div>
          </div>
        </nav>

        <div className="p-4 bg-slate-950/30 border-t border-slate-700/70">
          <div className="grid grid-cols-2 gap-2">
            <HealthStat label="Coral" status="online" />
            <HealthStat label="Agent" status="online" />
          </div>
        </div>
      </aside>

      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 border-b border-slate-800 flex items-center justify-between px-8 bg-[#0f172a]/80 backdrop-blur-sm shrink-0">
          <div className="flex items-center gap-6">
            <h2 className="text-sm font-black text-slate-300 uppercase tracking-widest flex items-center gap-3">
              <Terminal className="w-4 h-4" />
              {activeTab.replace('-', ' ')}
            </h2>
          </div>
          <div className="flex gap-4">
            <SystemBadge icon={<Cpu className="w-3 h-3" />} label="NATIVE_MCP_ACTIVE" />
            <SystemBadge icon={<Globe className="w-3 h-3" />} label="AWS_PROD" />
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-10 bg-[#0b1120]">
          <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-10">
            <div className="lg:col-span-4 space-y-6">
              <section className="terminal-card p-6 shadow-2xl bg-slate-900/80">
                <h3 className="text-[10px] font-black mb-6 flex items-center gap-2 text-sky-300 uppercase tracking-[0.2em]">
                  {activeTab === 'configuration' ? 'Global Parameters' : 'Target Context'}
                </h3>
                <div className="space-y-5">
                  {activeTab === 'configuration' ? (
                    <>
                      <InputField label="ORGANIZATION / USER" value={owner} onChange={setOwner} placeholder="e.g. withcoral" />
                      <InputField label="REPOSITORY" value={repo} onChange={setRepo} placeholder="e.g. aura-guard-node-service" />
                      <InputField label="PULL REQUEST #" value={pr} onChange={setPr} placeholder="e.g. 1042" />
                      <InputField label="FILE OR PACKAGE" value={libFile} onChange={setLibFile} placeholder="e.g. express" />
                      <InputField label="SERVICE NAME" value={service} onChange={setService} placeholder="e.g. aura-guard-node-service" />
                      <InputField label="CLOUDWATCH LOG GROUP" value={logGroup} onChange={setLogGroup} placeholder="e.g. api-ingestion-logs" />
                    </>
                  ) : (
                    <>
                      <div className="p-4 bg-slate-950/50 rounded-xl border border-slate-700/70 space-y-3">
                        <div className="flex justify-between text-[10px] uppercase font-bold tracking-tight">
                          <span className="text-slate-400">Context</span>
                          <span className="text-sky-300 text-right">{owner} / {repo}</span>
                        </div>
                        {activeTab === 'incident-response' && (
                          <div className="flex justify-between text-[10px] uppercase font-bold tracking-tight">
                            <span className="text-slate-400">Service</span>
                            <span className="text-emerald-300">{service}</span>
                          </div>
                        )}
                        <button onClick={() => setActiveTab('configuration')} className="w-full text-[9px] text-center font-black text-sky-300 hover:text-sky-100 transition-colors uppercase pt-2 border-t border-slate-700/70">
                          Modify Global Config
                        </button>
                      </div>

                      {activeTab === 'org-scan' && (
                        <div className="p-4 bg-sky-500/10 border border-sky-400/20 rounded-xl text-xs text-sky-100 leading-relaxed shadow-inner">
                          Performing comprehensive L4 audit. Aura Guard will dynamically discover all repositories and audit both vulnerabilities and active PRs.
                        </div>
                      )}

                      <button onClick={() => handleRunScan()} disabled={loadings[activeTab]} className="w-full bg-sky-500 hover:bg-sky-400 disabled:bg-sky-500/50 text-slate-950 font-black py-4 rounded-xl transition-all flex items-center justify-center gap-3 mt-6 shadow-xl shadow-sky-950/40 group uppercase text-xs tracking-widest">
                        {loadings[activeTab] ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current group-hover:translate-x-1 transition-transform" />}
                        Execute Analysis
                      </button>
                    </>
                  )}
                </div>
              </section>
            </div>

            <div className="lg:col-span-8">
              {activeTab === 'configuration' && (
                <div className="space-y-8 animate-in fade-in duration-1000">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-black uppercase tracking-[0.3em] text-white/30 flex items-center gap-2">
                      <Settings className="w-4 h-4" />
                      Global Command Configuration
                    </h3>
                  </div>

                  <div className="terminal-card p-12 bg-white/[0.01] border-dashed">
                    <div className="max-w-2xl mx-auto space-y-10">
                      <div className="flex gap-8 items-start">
                        <div className="bg-primary/20 p-4 rounded-3xl"><Database className="w-8 h-8 text-primary" /></div>
                        <div>
                          <h4 className="text-lg font-bold mb-2">Native MCP Federation</h4>
                          <p className="text-muted/40 text-sm leading-relaxed">Aura Guard uses these parameters to scope its autonomous investigations across GitHub, CloudWatch, and Linear. Changes here apply to all workflow executions.</p>
                        </div>
                      </div>

                      <div className="flex gap-8 items-start opacity-50">
                        <div className="bg-accent/20 p-4 rounded-3xl"><Activity className="w-8 h-8 text-accent" /></div>
                        <div>
                          <h4 className="text-lg font-bold mb-2">Telemetry Scoping</h4>
                          <p className="text-muted/40 text-sm leading-relaxed">Ensuring your log groups and service names match your AWS environment is critical for high-confidence root cause analysis.</p>
                        </div>
                      </div>

                      <div className="pt-10 border-t border-white/5">
                        <button onClick={() => setActiveTab('org-scan')} className="bg-white/5 hover:bg-white/10 text-white px-8 py-4 rounded-2xl font-black text-xs uppercase tracking-widest transition-all">
                          Return to Command Center
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab !== 'configuration' && !reports[activeTab] && !loadings[activeTab] && !errors[activeTab] && (
                <div className="space-y-8 animate-in fade-in duration-1000">
                    <div className="flex items-center justify-between">
                        <h3 className="text-xs font-black uppercase tracking-[0.3em] text-slate-300 flex items-center gap-2">
                            <Bell className="w-4 h-4" />
                            System Intelligence / Smart Alerts
                        </h3>
                        <span className="text-[9px] font-mono text-slate-500 uppercase">Ready</span>
                    </div>

                    <div className="grid grid-cols-1 gap-4">
                        {discoveryItems?.map(item => (
                            <button 
                                key={item.id}
                                onClick={() => handleDiscoveryAction(item)}
                                className="group text-left p-6 rounded-2xl bg-slate-900/80 border border-slate-700/70 hover:border-sky-400/40 transition-all hover:bg-slate-800/90 flex items-center gap-6 shadow-lg shadow-black/30"
                            >
                                <div className={cn("p-4 rounded-2xl shrink-0 group-hover:scale-110 transition-transform", 
                                    item.type === 'error' ? "bg-red-500/15 text-red-300" : 
                                    item.type === 'audit' ? "bg-amber-500/15 text-amber-200" : "bg-sky-500/15 text-sky-200")}>
                                    {item.type === 'error' ? <Activity className="w-6 h-6" /> : 
                                     item.type === 'audit' ? <Shield className="w-6 h-6" /> : <Zap className="w-6 h-6" />}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="font-bold text-lg mb-1 text-slate-100 group-hover:text-sky-200 transition-colors">{item.title}</div>
                                    <p className="text-slate-400 text-sm leading-relaxed truncate">{item.description}</p>
                                </div>
                                <ArrowRight className="w-5 h-5 text-slate-500 group-hover:text-sky-300 group-hover:translate-x-1 transition-all" />
                            </button>
                        ))}
                    </div>

                    <div className="h-[300px] flex flex-col items-center justify-center text-center p-12 terminal-card border-dashed bg-slate-900/50">
                        <BarChart3 className="w-12 h-12 text-slate-500 mb-6" />
                        <h3 className="text-sm font-bold text-slate-200 uppercase tracking-widest">Choose a workflow to begin</h3>
                        <p className="text-sm text-slate-400 max-w-sm mt-3 leading-relaxed">Run a scan, inspect an alert, or adjust the target context from the panel on the left.</p>
                    </div>
                </div>
              )}

              {loadings[activeTab] && (
                <div className="h-[600px] flex flex-col items-center justify-center text-center p-12 terminal-card bg-slate-900/80">
                  <div className="relative mb-8">
                    <Loader2 className="w-20 h-20 text-sky-300 animate-spin" />
                    <Shield className="w-8 h-8 text-sky-300 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                  </div>
                  <h3 className="text-xl font-bold tracking-tight">Building the incident report...</h3>
                  <div className="mt-8 flex flex-col gap-3 font-mono text-[10px] text-sky-200 uppercase tracking-widest">
                    <div className="animate-pulse flex items-center justify-center gap-2">
                        <div className="w-1 h-1 bg-primary rounded-full" />
                        Analyzing Multi-Source causal graphs
                    </div>
                    <div className="animate-pulse delay-75 flex items-center justify-center gap-2 text-slate-400">
                         Synthesizing evidence-first triage report
                    </div>
                  </div>
                </div>
              )}

              {errors[activeTab] && (
                <div className="p-10 border border-red-400/30 bg-red-500/10 rounded-3xl flex gap-8 items-start shadow-2xl shadow-red-950/30">
                  <AlertTriangle className="w-10 h-10 text-red-300 flex-shrink-0" />
                  <div>
                    <h3 className="text-red-200 font-black text-xl tracking-tighter uppercase mb-2">Analysis Interrupted</h3>
                    <p className="text-red-100 text-sm font-mono leading-relaxed">{errors[activeTab]}</p>
                    <button onClick={() => handleRunScan()} className="mt-6 text-[10px] font-black text-red-200 hover:text-white uppercase tracking-widest flex items-center gap-2">
                        <RotateCcw className="w-3 h-3" /> Retry Investigation
                    </button>
                  </div>
                </div>
              )}

              {reports[activeTab] && (
                <div className="space-y-8 animate-in fade-in slide-in-from-bottom-6 duration-700">
                  <div className={cn("p-6 rounded-2xl flex items-center justify-between border shadow-2xl", reports[activeTab]?.status === 'clean' ? "bg-emerald-500/10 border-emerald-300/30 shadow-emerald-950/30" : "bg-red-500/10 border-red-300/30 shadow-red-950/30")}>
                    <div className="flex items-center gap-5">
                      <div className={cn("p-3 rounded-2xl", reports[activeTab]?.status === 'clean' ? "bg-emerald-400/15 text-emerald-200" : "bg-red-400/15 text-red-200")}>
                        {reports[activeTab]?.status === 'clean' ? <CheckCircle2 className="w-6 h-6" /> : <AlertTriangle className="w-6 h-6" />}
                      </div>
                      <div>
                        <div className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-300 mb-1">Triaged Outcome</div>
                        <div className={cn("font-bold text-xl leading-tight uppercase tracking-tight", reports[activeTab]?.status === 'clean' ? "text-emerald-200" : "text-red-100")}>Status: {reports[activeTab]?.status}</div>
                      </div>
                    </div>
                    {reports[activeTab]?.remediation && (
                      <button onClick={handleRemediate} disabled={remediating || (reports[activeTab] as any).remediation_status === 'SUCCESS'} className={cn("px-6 py-3 rounded-2xl font-black text-xs flex items-center gap-3 transition-all shadow-xl", (reports[activeTab] as any).remediation_status === 'SUCCESS' ? "bg-accent text-white" : "bg-red-500 hover:bg-red-600 text-white shadow-red-500/20 active:scale-95")}>
                        {(reports[activeTab] as any).remediation_status === 'SUCCESS' ? <CheckCircle2 className="w-4 h-4" /> : <Command className="w-4 h-4" />}
                        {(reports[activeTab] as any).remediation_status === 'SUCCESS' ? 'REMEDIATION_APPLIED' : 'EXECUTE_REMEDIATION'}
                      </button>
                    )}
                  </div>

                  <div className="report-content rounded-lg border border-slate-200 bg-slate-50 p-10 text-slate-950 max-w-none shadow-2xl">
                    <ReactMarkdown>{reports[activeTab]?.report || ''}</ReactMarkdown>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function HealthStat({ label, status }: any) {
  return (
    <div className="bg-slate-950/50 border border-slate-700/70 p-3 rounded-xl flex items-center justify-between">
      <span className="text-[8px] font-black text-slate-400 uppercase tracking-widest">{label}</span>
      <div className="flex items-center gap-1.5">
        <div className={cn("w-1.5 h-1.5 rounded-full animate-pulse", status === 'online' ? "bg-emerald-300 shadow-[0_0_8px_rgba(110,231,183,0.5)]" : "bg-red-400")} />
        <span className="text-[8px] font-bold uppercase text-slate-100">{status}</span>
      </div>
    </div>
  );
}

function TabButton({ active, onClick, icon, label, desc }: any) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full p-4 rounded-2xl transition-all flex items-start gap-4 border text-left group",
        active 
          ? "bg-sky-500/15 border-sky-400/30 text-white shadow-lg shadow-sky-950/20" 
          : "bg-transparent border-transparent text-slate-400 hover:bg-slate-800/70 hover:text-slate-100"
      )}
    >
      <div className={cn(
        "p-2.5 rounded-xl transition-colors shrink-0",
        active ? "bg-sky-500 text-white" : "bg-slate-800 text-slate-400 group-hover:text-slate-100"
      )}>
        {icon}
      </div>
      <div className="min-w-0">
        <div className={cn("font-bold text-xs uppercase tracking-tight mb-0.5", active ? "text-white" : "text-slate-300")}>{label}</div>
        <div className="text-[9px] leading-tight text-slate-400 line-clamp-1">{desc}</div>
      </div>
    </button>
  );
}

function InputField({ label, value, onChange, placeholder }: any) {
  return (
    <div className="space-y-2">
      <label className="text-[8px] font-black text-slate-400 uppercase tracking-[0.2em] ml-1">{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-slate-950/50 border border-slate-700/70 rounded-xl px-4 py-3 text-sm font-medium text-slate-100 focus:outline-none focus:border-sky-400/70 transition-colors placeholder:text-slate-500"
      />
    </div>
  );
}

function SystemBadge({ icon, label }: any) {
  return (
    <div className="flex items-center gap-3 bg-slate-900 border border-slate-700 px-4 py-2 rounded-2xl text-[9px] font-black text-slate-300 tracking-widest">
      {icon}
      {label}
    </div>
  );
}
