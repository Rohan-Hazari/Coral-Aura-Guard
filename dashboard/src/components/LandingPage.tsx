import { Activity, ArrowRight, Building2, Clock, GitBranch, Network, Shield, Sparkles, Zap } from 'lucide-react';
import heroImage from '../assets/hero.png';

interface LandingPageProps {
  onStart: () => void;
}

const moments = [
  'Spot the first signal',
  'Follow the trail',
  'Share a clear answer',
];

const features = [
  {
    icon: <Activity className="w-5 h-5" />,
    title: 'Incident triage',
    desc: 'Start with the failing service, inspect logs, connect recent commits, and produce a root-cause report with a suggested fix.',
  },
  {
    icon: <Network className="w-5 h-5" />,
    title: 'Blast radius',
    desc: 'Trace which downstream repositories, pull requests, and teams may be affected before a risky change spreads.',
  },
  {
    icon: <Building2 className="w-5 h-5" />,
    title: 'Organization scan',
    desc: 'Audit repositories across an owner or organization and surface vulnerable dependencies and risky active work.',
  },
];

export default function LandingPage({ onStart }: LandingPageProps) {
  return (
    <div className="min-h-screen bg-[#08111f] text-slate-100 font-sans overflow-x-hidden selection:bg-sky-300/30">
      <nav className="fixed top-0 w-full z-50 bg-[#08111f]/85 backdrop-blur-md border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-sky-400/15 p-2 rounded-lg border border-sky-300/20">
              <Shield className="w-6 h-6 text-sky-200" />
            </div>
            <span className="font-bold text-xl tracking-tight">Aura Guard</span>
          </div>
          <button
            onClick={onStart}
            className="bg-sky-300 hover:bg-sky-200 text-slate-950 px-5 py-2.5 rounded-full font-black text-sm transition-all shadow-lg shadow-sky-950/40 flex items-center gap-2 group active:scale-95"
          >
            Open Demo
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
      </nav>

      <section className="relative min-h-[92vh] px-6 pt-28 pb-16 flex items-end overflow-hidden">
        <img
          src={heroImage}
          alt=""
          className="absolute inset-0 h-full w-full object-cover opacity-45"
        />
        <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(8,17,31,0.96)_0%,rgba(8,17,31,0.82)_44%,rgba(8,17,31,0.42)_100%)]" />
        <div className="absolute inset-x-0 bottom-0 h-40 bg-[linear-gradient(0deg,#08111f_0%,rgba(8,17,31,0)_100%)]" />

        <div className="relative z-10 max-w-7xl mx-auto w-full grid lg:grid-cols-[1.05fr_0.95fr] gap-12 items-end">
          <div className="max-w-3xl pb-10">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 border border-white/15 text-sky-100 text-xs font-bold mb-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
              <Sparkles className="w-4 h-4" />
              Calm incident response for busy teams
            </div>
            <h1 className="text-5xl md:text-7xl font-black leading-[0.95] tracking-tight mb-8 animate-in fade-in slide-in-from-bottom-6 duration-700">
              Turn messy outages into clear answers.
            </h1>
            <p className="text-lg md:text-xl text-slate-200 max-w-2xl leading-8 mb-10 animate-in fade-in slide-in-from-bottom-8 duration-1000">
              Aura Guard helps you understand what broke, what changed, and what to do next, without making your team dig through five different tools.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 animate-in fade-in slide-in-from-bottom-10 duration-1000">
              <button
                onClick={onStart}
                className="bg-sky-300 hover:bg-sky-200 text-slate-950 px-8 py-4 rounded-xl font-black text-base transition-all shadow-2xl shadow-sky-950/40 flex items-center justify-center gap-3 group active:scale-95"
              >
                Try the demo
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>
              <a
                href="#how-it-feels"
                className="bg-white/10 hover:bg-white/15 border border-white/15 text-white px-8 py-4 rounded-xl font-bold text-base transition-all flex items-center justify-center gap-3"
              >
                See how it helps
              </a>
            </div>
          </div>

          <div className="hidden lg:block pb-14">
            <div className="animate-hero-float rounded-2xl border border-white/15 bg-slate-950/70 backdrop-blur-xl p-5 shadow-2xl shadow-black/40">
              <div className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-red-400/15 text-red-200 flex items-center justify-center">
                    <Zap className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-sm font-black">Payment API slowing down</div>
                    <div className="text-xs text-slate-400">High confidence root cause found</div>
                  </div>
                </div>
                <Clock className="w-5 h-5 text-slate-400" />
              </div>
              <div className="space-y-3">
                {moments.map((moment, index) => (
                  <div key={moment} className="flex items-center gap-3">
                    <div className="w-6 h-6 rounded-full bg-sky-300 text-slate-950 text-xs font-black flex items-center justify-center">
                      {index + 1}
                    </div>
                    <div className="h-10 flex-1 rounded-lg bg-white/8 border border-white/10 px-4 flex items-center text-sm text-slate-200">
                      {moment}
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-5 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                <div className="h-full w-3/4 bg-sky-300 animate-soft-pulse origin-left" />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="how-it-feels" className="px-6 py-24 bg-[#08111f]">
        <div className="max-w-7xl mx-auto">
          <div className="max-w-2xl mb-12">
            <h2 className="text-3xl md:text-5xl font-black tracking-tight mb-5">Three workflows, one evidence trail.</h2>
            <p className="text-slate-300 text-lg leading-8">
              Aura Guard uses Coral as the connective layer across GitHub, CloudWatch, Linear, and OSV, so each report is grounded in the systems your team already uses.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-5">
            {features.map((item) => (
              <div key={item.title} className="rounded-2xl bg-white/[0.06] border border-white/10 p-6 hover:bg-white/[0.09] transition-colors">
                <div className="w-11 h-11 rounded-xl bg-sky-300/15 text-sky-200 flex items-center justify-center mb-6">
                  {item.icon}
                </div>
                <h3 className="text-xl font-black mb-3">{item.title}</h3>
                <p className="text-slate-300 leading-7">{item.desc}</p>
              </div>
            ))}
          </div>
          <div className="mt-6 rounded-2xl bg-sky-300/10 border border-sky-300/20 p-6 flex flex-col md:flex-row gap-5 md:items-center">
            <div className="w-12 h-12 rounded-xl bg-sky-300 text-slate-950 flex items-center justify-center shrink-0">
              <GitBranch className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-xl font-black mb-2">How Coral fits in</h3>
              <p className="text-slate-300 leading-7">
                Coral exposes the live tool data through one queryable MCP layer. Aura Guard asks targeted questions, pulls the evidence, and turns those results into a readable security or incident report.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="px-6 py-20 bg-slate-100 text-slate-950">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-8">
          <div>
            <h2 className="text-3xl md:text-5xl font-black tracking-tight mb-4">Open the control room.</h2>
            <p className="text-slate-600 text-lg">Run a sample incident and see the report view in action.</p>
          </div>
          <button
            onClick={onStart}
            className="bg-slate-950 hover:bg-slate-800 text-white px-8 py-4 rounded-xl font-black transition-all flex items-center gap-3 active:scale-95"
          >
            Launch demo
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </section>
    </div>
  );
}
