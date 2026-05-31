import { useState, useEffect, useRef, useCallback } from 'react';
import { Shield, Zap, Terminal, AlertTriangle, CheckCircle2, Loader2, BarChart3, Activity, Command, Cpu, Globe, History, Play, RotateCcw, ArrowRight, Database, Bell, Settings, Brain } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import DependencyGraph from './components/DependencyGraph';
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
  const [loadings, setLoadings] = useState<Record<string, boolean>>({});
  const [reports, setReports] = useState<Record<string, Report | null>>({});
  const [errors, setErrors] = useState<Record<string, string | null>>({});
  const [remediating, setRemediating] = useState(false);
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [sidebarWidth, setSidebarWidth] = useState(300);
  const [isResizing, setIsResizing] = useState(false);
  const [scanRecentPrs, setScanRecentPrs] = useState(false);
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
        tab: "supply-chain",
        params: {owner: "Rohan-Hazari", repo: "aura-guard-node-service", pr: "recent"}
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

  // Resize Logic
  const startResizing = useCallback(() => setIsResizing(true), []);
  const stopResizing = useCallback(() => setIsResizing(false), []);
  const resize = useCallback((e: MouseEvent) => {
    if (isResizing) setSidebarWidth(e.clientX);
  }, [isResizing]);

  useEffect(() => {
    window.addEventListener("mousemove", resize);
    window.addEventListener("mouseup", stopResizing);
    return () => {
      window.removeEventListener("mousemove", resize);
      window.removeEventListener("mouseup", stopResizing);
    };
  }, [resize, stopResizing]);

  // WebSocket Connection
  useEffect(() => {
    const ws = new WebSocket(WS_BASE);
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      setEvents(prev => [{ ...data, timestamp: new Date().toLocaleTimeString() }, ...prev].slice(0, 50));
    };
    return () => ws.close();
  }, []);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = 0;
  }, [events]);

  const handleRunScan = async (overrideParams?: any, overrideTab?: Tab) => {
    setLoading(true);
    setError(null);
    setReport(null);
    setRemediating(false);

    const targetTab = overrideTab || activeTab;
    const targetOwner = overrideParams?.owner || owner;

    try {
      let endpoint = '';
      let params = `owner=${targetOwner}`;

      if (targetTab === 'org-scan') {
        endpoint = '/api/org-scan';
      } else if (targetTab === 'supply-chain') {
        endpoint = '/api/supply-chain';
        const targetRepo = overrideParams?.repo || repo;
        const targetPr = overrideParams?.pr || (scanRecentPrs ? 'recent' : pr);
        params += `&repo=${targetRepo}&pr=${targetPr}`;
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
      setReport(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
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
    setReport(prev => prev ? { ...prev, remediation_status: 'SUCCESS' } as any : null);
    setRemediating(false);
  };

  if (route !== '/demo') {
    return <LandingPage onStart={navigateToDemo} />;
  }

  return (
    <div className={cn("flex h-screen bg-background text-white font-sans overflow-hidden", isResizing && "cursor-col-resize select-none")}>
      {/* Sidebar */}
      <aside style={{ width: sidebarWidth }} className="bg-card border-r border-white/5 flex flex-col shrink-0 relative transition-[width] duration-75">
        <div onMouseDown={startResizing} className={cn("absolute top-0 right-0 w-1 h-full cursor-col-resize hover:bg-primary/50 transition-colors z-50", isResizing && "bg-primary/50")} />
        
        <div className="p-6 flex items-center gap-3 border-b border-white/5">
          <div className="bg-primary/20 p-2 rounded-lg">
            <Shield className="w-6 h-6 text-primary" />
          </div>
          <h1 className="font-bold text-lg tracking-tight uppercase">Aura Guard <span className="text-[10px] text-primary/60 align-top">MCP</span></h1>
        </div>

        <nav className="p-4 space-y-2 overflow-y-auto flex-1">
          <div className="px-2 mb-4">
              <h3 className="text-[10px] font-black text-muted/40 uppercase tracking-[0.2em] mb-4">Core Workflows</h3>
              <div className="space-y-2">
                <TabButton active={activeTab === 'configuration'} onClick={() => setActiveTab('configuration')} icon={<Settings className="w-4 h-4" />} label="Configuration" desc="Global scan parameters" />
                <TabButton active={activeTab === 'org-scan'} onClick={() => setActiveTab('org-scan')} icon={<Globe className="w-4 h-4" />} label="Comprehensive Scan" desc="Org & PR Security Audit" />
                <TabButton active={activeTab === 'blast-radius'} onClick={() => setActiveTab('blast-radius')} icon={<Zap className="w-4 h-4" />} label="Blast Radius" desc="Downstream Impact Analysis" />
                <TabButton active={activeTab === 'incident-response'} onClick={() => setActiveTab('incident-response')} icon={<Activity className="w-4 h-4" />} label="Incident Triage" desc="Autonomous Root Cause" />
              </div>
          </div>
          
          <div className="border-t border-white/5 pt-6 px-2">
            <h3 className="text-[10px] font-bold text-muted uppercase tracking-widest flex items-center gap-2 mb-4">
              <History className="w-3 h-3" />
              Reasoning Trace
            </h3>
            <div ref={scrollRef} className="space-y-3 font-mono text-[10px]">
              {events.length === 0 && <div className="text-muted/30 italic">Awaiting telemetry...</div>}
              {events.map((ev, i) => (
                <div key={i} className={cn("p-2 rounded border border-white/5 bg-white/[0.01]", ev.type === 'query_error' ? "border-red-500/20 bg-red-500/5" : ev.type === 'query_success' ? "border-accent/10" : "")}>
                  <div className="flex justify-between mb-1 opacity-40">
                    <div className="flex gap-2 items-center">
                      <span>[{ev.timestamp}]</span>
                      {ev.agentic && <span className="bg-primary/20 text-primary px-1 rounded-[2px] font-black text-[7px] border border-primary/20 flex items-center gap-0.5"><Brain className="w-2 h-2" /> AGENT</span>}
                    </div>
                    <span>{ev.type.toUpperCase()}</span>
                  </div>
                  {ev.sql && <div className="text-primary/70 break-words line-clamp-2 text-[9px]">{ev.sql}</div>}
                  {ev.elapsed_ms !== undefined && <div className="text-accent/60 flex items-center gap-1 mt-1"><Database className="w-2.5 h-2.5" /> {ev.elapsed_ms}ms</div>}
                  {ev.error && <div className="text-red-400/80">{ev.error}</div>}
                </div>
              ))}
            </div>
          </div>
        </nav>

        <div className="p-4 bg-secondary/20 border-t border-white/5">
          <div className="grid grid-cols-2 gap-2">
            <HealthStat label="Coral" status="online" />
            <HealthStat label="Agent" status="online" />
          </div>
        </div>
      </aside>

      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 border-b border-white/5 flex items-center justify-between px-8 bg-card/50 backdrop-blur-sm shrink-0">
          <div className="flex items-center gap-6">
            <h2 className="text-sm font-black text-white/40 uppercase tracking-widest flex items-center gap-3">
              <Terminal className="w-4 h-4" />
              {activeTab.replace('-', ' ')}
            </h2>
          </div>
          <div className="flex gap-4">
            <SystemBadge icon={<Cpu className="w-3 h-3" />} label="NATIVE_MCP_ACTIVE" />
            <SystemBadge icon={<Globe className="w-3 h-3" />} label="AWS_PROD" />
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-10 bg-[#0d0d0f]">
          <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-10">
            <div className="lg:col-span-4 space-y-6">
              <section className="terminal-card p-6 shadow-2xl bg-white/[0.01]">
                <h3 className="text-[10px] font-black mb-6 flex items-center gap-2 text-primary uppercase tracking-[0.2em]">
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
                      <div className="p-4 bg-secondary/20 rounded-xl border border-white/5 space-y-3">
                        <div className="flex justify-between text-[10px] uppercase font-bold tracking-tight">
                          <span className="opacity-40">Context</span>
                          <span className="text-primary">{owner} / {repo}</span>
                        </div>
                        {activeTab === 'incident-response' && (
                          <div className="flex justify-between text-[10px] uppercase font-bold tracking-tight">
                            <span className="opacity-40">Service</span>
                            <span className="text-accent">{service}</span>
                          </div>
                        )}
                        <button onClick={() => setActiveTab('configuration')} className="w-full text-[9px] text-center font-black text-primary/60 hover:text-primary transition-colors uppercase pt-2 border-t border-white/5">
                          Modify Global Config
                        </button>
                      </div>

                      {activeTab === 'org-scan' && (
                        <div className="p-4 bg-primary/5 border border-primary/10 rounded-xl text-[10px] text-primary/70 leading-relaxed italic shadow-inner">
                          Performing comprehensive L4 audit. Aura Guard will dynamically discover all repositories and audit both vulnerabilities and active PRs.
                        </div>
                      )}

                      <button onClick={() => handleRunScan()} disabled={loading} className="w-full bg-primary hover:bg-primary/90 disabled:bg-primary/50 text-white font-black py-4 rounded-xl transition-all flex items-center justify-center gap-3 mt-6 shadow-xl shadow-primary/20 group uppercase text-xs tracking-widest">
                        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current group-hover:translate-x-1 transition-transform" />}
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

              {activeTab !== 'configuration' && !report && !loading && !error && (
                <div className="space-y-8 animate-in fade-in duration-1000">
                    <div className="flex items-center justify-between">
                        <h3 className="text-xs font-black uppercase tracking-[0.3em] text-white/30 flex items-center gap-2">
                            <Bell className="w-4 h-4" />
                            System Intelligence / Smart Alerts
                        </h3>
                        <span className="text-[9px] font-mono text-white/10 uppercase">Refresh in 12s</span>
                    </div>

                    <div className="grid grid-cols-1 gap-4">
                        {discoveryItems?.map(item => (
                            <button 
                                key={item.id}
                                onClick={() => handleDiscoveryAction(item)}
                                className="group text-left p-6 rounded-3xl bg-white/[0.02] border border-white/5 hover:border-primary/30 transition-all hover:bg-white/[0.04] flex items-center gap-6 shadow-lg shadow-black/50"
                            >
                                <div className={cn("p-4 rounded-2xl shrink-0 group-hover:scale-110 transition-transform", 
                                    item.type === 'error' ? "bg-red-500/10 text-red-500" : 
                                    item.type === 'audit' ? "bg-yellow-500/10 text-yellow-500" : "bg-primary/10 text-primary")}>
                                    {item.type === 'error' ? <Activity className="w-6 h-6" /> : 
                                     item.type === 'audit' ? <Shield className="w-6 h-6" /> : <Zap className="w-6 h-6" />}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="font-bold text-lg mb-1 group-hover:text-primary transition-colors">{item.title}</div>
                                    <p className="text-muted/40 text-xs leading-relaxed truncate">{item.description}</p>
                                </div>
                                <ArrowRight className="w-5 h-5 text-white/10 group-hover:text-primary group-hover:translate-x-1 transition-all" />
                            </button>
                        ))}
                    </div>

                    <div className="h-[300px] flex flex-col items-center justify-center text-center p-12 terminal-card border-dashed bg-white/[0.005]">
                        <BarChart3 className="w-12 h-12 text-white/5 mb-6" />
                        <h3 className="text-sm font-bold text-white/20 uppercase tracking-widest">Idle Intelligence Mode</h3>
                        <p className="text-[10px] text-white/10 max-w-sm mt-3 leading-relaxed uppercase tracking-tighter">Monitoring US-EAST-1 for drift and anomalies. Configure targets on the left or select an alert above to begin.</p>
                    </div>
                </div>
              )}

              {loading && (
                <div className="h-[600px] flex flex-col items-center justify-center text-center p-12 terminal-card bg-white/[0.01]">
                  <div className="relative mb-8">
                    <Loader2 className="w-20 h-20 text-primary animate-spin" />
                    <Shield className="w-8 h-8 text-primary absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                  </div>
                  <h3 className="text-xl font-bold tracking-tight uppercase">Agentic Reasoning in Progress...</h3>
                  <div className="mt-8 flex flex-col gap-3 font-mono text-[9px] text-primary/40 uppercase tracking-widest">
                    <div className="animate-pulse flex items-center justify-center gap-2">
                        <div className="w-1 h-1 bg-primary rounded-full" />
                        Analyzing Multi-Source causal graphs
                    </div>
                    <div className="animate-pulse delay-75 flex items-center justify-center gap-2 text-white/20">
                         Synthesizing evidence-first triage report
                    </div>
                  </div>
                </div>
              )}

              {error && (
                <div className="p-10 border border-red-500/20 bg-red-500/5 rounded-3xl flex gap-8 items-start shadow-2xl shadow-red-500/5">
                  <AlertTriangle className="w-10 h-10 text-red-500 flex-shrink-0" />
                  <div>
                    <h3 className="text-red-500 font-black text-xl tracking-tighter uppercase mb-2">Analysis Interrupted</h3>
                    <p className="text-red-400/60 text-sm font-mono leading-relaxed">{error}</p>
                    <button onClick={() => handleRunScan()} className="mt-6 text-[10px] font-black text-red-500 hover:underline uppercase tracking-widest flex items-center gap-2">
                        <RotateCcw className="w-3 h-3" /> Retry Investigation
                    </button>
                  </div>
                </div>
              )}

              {report && (
                <div className="space-y-8 animate-in fade-in slide-in-from-bottom-6 duration-700">
                  <div className={cn("p-6 rounded-3xl flex items-center justify-between border shadow-2xl bg-white/[0.02]", report.status === 'clean' ? "border-accent/20 shadow-accent/5" : "border-red-500/20 shadow-red-500/5")}>
                    <div className="flex items-center gap-5">
                      <div className={cn("p-3 rounded-2xl", report.status === 'clean' ? "bg-accent/10 text-accent" : "bg-red-500/10 text-red-500")}>
                        {report.status === 'clean' ? <CheckCircle2 className="w-6 h-6" /> : <AlertTriangle className="w-6 h-6" />}
                      </div>
                      <div>
                        <div className="text-[10px] font-black uppercase tracking-[0.3em] opacity-30 mb-1">Triaged Outcome</div>
                        <div className={cn("font-bold text-xl leading-tight uppercase tracking-tight", report.status === 'clean' ? "text-accent" : "text-red-500")}>Status: {report.status}</div>
                      </div>
                    </div>
                    {report.remediation && (
                      <button onClick={handleRemediate} disabled={remediating || (report as any).remediation_status === 'SUCCESS'} className={cn("px-6 py-3 rounded-2xl font-black text-xs flex items-center gap-3 transition-all shadow-xl", (report as any).remediation_status === 'SUCCESS' ? "bg-accent text-white" : "bg-red-500 hover:bg-red-600 text-white shadow-red-500/20 active:scale-95")}>
                        {remediating ? <Loader2 className="w-4 h-4 animate-spin" /> : (report as any).remediation_status === 'SUCCESS' ? <CheckCircle2 className="w-4 h-4" /> : <RotateCcw className="w-4 h-4" />}
                        {(report as any).remediation_status === 'SUCCESS' ? 'ROLLBACK SUCCESSFUL' : 'AUTO-ROLLBACK'}
                      </button>
                    )}
                  </div>
                  <div className="terminal-card p-12 report-content prose prose-invert max-w-none shadow-2xl relative overflow-hidden bg-[#121214] border-white/5">
                    <div className="absolute top-0 right-0 p-6 opacity-5"><Shield className="w-48 h-48" /></div>
                    {activeTab === 'blast-radius' && report.rows && (
                      <div className="mb-12">
                        <h3 className="text-xs font-black text-primary uppercase tracking-[0.2em] mb-6">Downstream Dependency Graph</h3>
                        <DependencyGraph data={report.rows} rootLabel={libFile} />
                      </div>
                    )}
                    <div className="relative z-10">
                        <ReactMarkdown>{report.report}</ReactMarkdown>
                    </div>
                    {report.remediation && (
                      <div className="mt-16 pt-10 border-t border-white/5 relative z-10">
                        <h4 className="text-[10px] font-black text-primary mb-6 flex items-center gap-3 uppercase tracking-[0.2em]"><Command className="w-4 h-4" />Proposed Remediation</h4>
                        <div className="bg-black/50 p-6 rounded-2xl border border-white/5 font-mono text-sm text-green-400 flex items-center justify-between group shadow-inner">
                          <span>$ {report.remediation}</span>
                          <button className="text-[9px] bg-white/10 px-3 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-all font-sans font-bold hover:bg-white/20">COPY COMMAND</button>
                        </div>
                        {(report as any).remediation_status === 'SUCCESS' && (
                          <div className="mt-6 p-4 bg-accent/10 border border-accent/20 rounded-2xl text-accent text-[11px] font-bold animate-in fade-in slide-in-from-top-2 flex items-center gap-3">
                            <Activity className="w-4 h-4" />
                            [SYSTEM] Pipeline instruction executed. Environment stabilization in progress.
                          </div>
                        )}
                      </div>
                    )}
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

function TabButton({ active, onClick, icon, label, desc }: any) {
  return (
    <button onClick={onClick} className={cn("w-full flex items-center gap-4 p-4 rounded-2xl transition-all text-left group", active ? "bg-primary/10 text-primary border border-primary/20 shadow-inner" : "hover:bg-white/[0.03] text-muted/50")}>
      <div className={cn("p-3 rounded-xl shrink-0 transition-transform group-hover:scale-110", active ? "bg-primary text-white shadow-lg shadow-primary/20" : "bg-secondary/40")}>{icon}</div>
      <div className="min-w-0">
        <div className={cn("text-xs font-black truncate uppercase tracking-tight", active ? "text-primary" : "text-white/70")}>{label}</div>
        <div className="text-[9px] font-medium opacity-30 leading-tight uppercase tracking-widest truncate mt-0.5">{desc}</div>
      </div>
    </button>
  );
}

function InputField({ label, value, onChange, placeholder }: any) {
  return (
    <div className="space-y-3">
      <label className="text-[10px] font-black text-white/20 tracking-[0.2em] uppercase ml-1">{label}</label>
      <input type="text" value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} className="w-full bg-secondary/40 border border-white/5 rounded-2xl px-5 py-4 text-xs focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all font-mono placeholder:text-white/5 shadow-inner" />
    </div>
  );
}

function HealthStat({ label, status }: any) {
  return (
    <div className="flex items-center justify-between p-3 bg-white/[0.02] rounded-xl border border-white/5 font-mono text-[9px] shadow-sm">
      <span className="text-white/30 uppercase font-bold">{label}</span>
      <span className={cn("flex items-center gap-2", status === 'online' ? "text-accent" : "text-red-400")}>
        <div className="w-1.5 h-1.5 bg-current rounded-full animate-pulse shadow-[0_0_8px_currentColor]" />
        {status.toUpperCase()}
      </span>
    </div>
  );
}

function SystemBadge({ icon, label }: any) {
  return (
    <div className="flex items-center gap-3 bg-white/[0.03] border border-white/5 px-4 py-2 rounded-2xl text-[9px] font-black text-white/40 tracking-widest">
      {icon}
      {label}
    </div>
  );
}
