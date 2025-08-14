import { useApplicationsPoll, ApplyOrStatusButton, ApplicationsNavBadge } from "./components/ui/ApplicationsUI";
import ApplicationsPanel from "./components/ui/ApplicationsUI";

import React, { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Briefcase, Sparkles, ExternalLink, Settings as Cog, RefreshCw, Wand2, Upload, PlayCircle, Trash2 } from 'lucide-react';
import { Card, CardContent } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Badge } from './components/ui/badge';
import { Slider } from './components/ui/slider';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './components/ui/dialog';
import { Textarea } from './components/ui/textarea';

const API = (path: string) => `http://localhost:8000${path}`;

type Job = { id: string; title: string; company: string; location: string; source: string; url: string; jd_text: string; score: number; created_at: string };

export default function App() {
  // 🔁 add 'applications' to tabs
  const [tab, setTab] = useState<'jobs'|'drafts'|'applications'>('jobs');

  const [rolesText, setRolesText] = useState('Data Scientist, ML Engineer');
  const [locationsText, setLocationsText] = useState('Remote, Bengaluru, Hyderabad');
  const [keywordsText, setKeywordsText] = useState('Python, NLP, AWS');
  const [minScore, setMinScore] = useState<number[]>([70]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [openTailor, setOpenTailor] = useState(false);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [tailorResult, setTailorResult] = useState<any>(null);

  const [drafts, setDrafts] = useState<any[]>([]);

  // ✅ Poll applications; use list for count, byUrl for per-card status, runningCount for badge
  const { list: applications, byUrl, runningCount } = useApplicationsPoll(4000);

  const splitList = (s: string) => s.split(',').map(x => x.trim()).filter(Boolean);
  const filtered = useMemo(() => jobs.filter(j => (j.score * 100) >= minScore[0]), [jobs, minScore]);

  async function fetchJobs() {
    setLoading(true); setError(null);
    try {
      const payload = { roles: splitList(rolesText), locations: splitList(locationsText), keywords: splitList(keywordsText), min_score: minScore[0] };
      const res = await fetch(API('/search/jobs'), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error('API error ' + res.status);
      setJobs(await res.json());
    } catch (e: any) { setError(e.message || 'Failed to load jobs'); } 
    finally { setLoading(false); }
  }

  async function tailorJob(job: Job) {
    setLoading(true); setError(null); setSelectedJob(job);
    try {
      const res = await fetch(API('/jobs/tailor'), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ job }) });
      if (!res.ok) throw new Error('Tailor error ' + res.status);
      const data = await res.json();
      setTailorResult(data);
      setOpenTailor(true);
    } catch (e: any) { setError(e.message || 'Failed to tailor'); } 
    finally { setLoading(false); }
  }

  async function createDraft(job: Job) {
    setLoading(true); setError(null);
    try {
      const res = await fetch(API('/applications/draft'), { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ job }) });
      if (!res.ok) throw new Error('Draft error ' + res.status);
      await fetchDrafts();
      setTab('drafts');
    } catch (e:any){ setError(e.message || 'Failed to create draft'); } 
    finally { setLoading(false); }
  }

  async function fetchDrafts() {
    const res = await fetch(API('/applications/drafts'));
    setDrafts(await res.json());
  }

  async function resumeDraft(id: string) {
    await fetch(API(`/applications/resume/${id}`), { method:'POST' });
    await fetchDrafts();
  }

  async function deleteDraft(id: string) {
    await fetch(API(`/applications/${id}`), { method:'DELETE' });
    await fetchDrafts();
  }

  useEffect(() => { fetchJobs(); fetchDrafts(); }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-white to-zinc-100">
      <header className="sticky top-0 z-30 border-b bg-white/80 backdrop-blur supports-[backdrop-filter]:bg-white/60">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl bg-zinc-900/10 p-2 text-zinc-900"><Sparkles className="h-5 w-5" /></div>
            <div>
              <div className="text-sm text-zinc-500">Agentic Job Assistant</div>
              <h1 className="text-xl font-semibold tracking-tight">Your job hunt command center</h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* shows live running tasks */}
            <ApplicationsNavBadge running={runningCount} />
            <Button variant="outline" size="sm" className="gap-2" onClick={fetchJobs}>
              <RefreshCw className="h-4 w-4" />{loading ? 'Syncing…' : 'Sync'}
            </Button>
            <Button size="sm" className="gap-2" onClick={fetchDrafts}>
              <PlayCircle className="h-4 w-4" /> Drafts
            </Button>
            <Button variant="outline" size="sm" className="gap-2"><Cog className="h-4 w-4" /> Settings</Button>
          </div>
        </div>

        {/* tabs row */}
        <div className="mx-auto max-w-7xl px-4 py-2 flex gap-2 text-sm">
          <button className={`px-3 py-1 rounded-lg ${tab==='jobs'?'bg-black text-white':'hover:bg-zinc-100'}`} onClick={()=>setTab('jobs')}>Jobs</button>
          <button className={`px-3 py-1 rounded-lg ${tab==='drafts'?'bg-black text-white':'hover:bg-zinc-100'}`} onClick={()=>{ setTab('drafts'); fetchDrafts(); }}>Drafts / Stuck</button>
          <button className={`px-3 py-1 rounded-lg ${tab==='applications'?'bg-black text-white':'hover:bg-zinc-100'}`} onClick={()=>setTab('applications')}>
            Applications <span className="ml-1 rounded-md bg-zinc-100 px-2 py-0.5 text-xs">{applications.length}</span>
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-7xl p-4">
        {tab==='jobs' && (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-12">
            {/* Search sidebar */}
            <div className="space-y-4 md:col-span-4">
              <Card className="rounded-2xl">
                <CardContent className="space-y-3">
                  <div className="text-lg font-semibold">Search</div>
                  <Input value={rolesText} onChange={e => setRolesText(e.target.value)} placeholder="Roles e.g. Data Scientist, ML Engineer" />
                  <Input value={locationsText} onChange={e => setLocationsText(e.target.value)} placeholder="Locations e.g. Remote, Bengaluru" />
                  <Input value={keywordsText} onChange={e => setKeywordsText(e.target.value)} placeholder="Keywords e.g. Python, NLP, AWS" />
                  <div>
                    <div className="mb-2 flex items-center justify-between">
                      <span className="text-sm text-zinc-500">Minimum fit score</span>
                      <Badge variant="outline" className="rounded-full">{minScore[0]}%</Badge>
                    </div>
                    <Slider value={minScore} onValueChange={setMinScore} min={0} max={100} step={1} />
                  </div>
                  <Button className="w-full gap-2" onClick={fetchJobs}>
                    <Briefcase className="h-4 w-4" />{loading ? 'Searching…' : 'Search Jobs'}
                  </Button>
                  {error && <div className="text-sm text-red-600">{error}</div>}
                </CardContent>
              </Card>
            </div>

            {/* Jobs grid */}
            <div className="space-y-3 md:col-span-8">
              <div className="text-sm text-zinc-500">Found {filtered.length} job(s)</div>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
                {filtered.map(job => (
                  <motion.div key={job.id} layout initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                    <Card className="group rounded-2xl transition-shadow hover:shadow-lg">
                      <CardContent className="space-y-3 p-4">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <h4 className="text-base font-semibold leading-tight">{job.title}</h4>
                            <div className="text-sm text-zinc-500">{job.company} • {job.location}</div>
                          </div>
                          <div className="inline-flex items-center gap-2 rounded-2xl border px-3 py-1">
                            <span className="h-2 w-2 rounded-full bg-emerald-500" />
                            <span className="text-sm font-medium">Fit {Math.round(job.score * 100)}%</span>
                          </div>
                        </div>
                        <p className="line-clamp-3 text-sm text-zinc-600">{job.jd_text}</p>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Button size="sm" className="gap-2" onClick={() => tailorJob(job)}>
                              <Wand2 className="h-4 w-4" /> Tailor
                            </Button>
                            <Button size="sm" variant="outline" className="gap-2" onClick={() => createDraft(job)}>
                              <Upload className="h-4 w-4" /> Draft
                            </Button>
                            {/* Apply / Status pill */}
                            <ApplyOrStatusButton job={job as any} current={byUrl[job.url]} />
                          </div>
                          <a href={job.url} target="_blank" className="text-sm text-blue-600 inline-flex items-center gap-1" rel="noreferrer">
                            View <ExternalLink className="h-4 w-4" />
                          </a>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        )}

        {tab==='drafts' && (
          <div className="space-y-3">
            <div className="text-sm text-zinc-500">Drafts & stuck applications ({drafts.length})</div>
            {/* your existing drafts grid here (unchanged) */}
          </div>
        )}

        {tab==='applications' && (
          <div className="space-y-3">
            {/* Full applications table with live status */}
            <ApplicationsPanel />
          </div>
        )}
      </main>

      {/* Tailor dialog */}
      <Dialog open={openTailor} onOpenChange={setOpenTailor}>
        <DialogContent className="relative">
          <button
            onClick={() => setOpenTailor(false)}
            aria-label="Close"
            className="absolute right-3 top-3 rounded-full p-2 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-800"
            title="Close"
          >
            ✕
          </button>

        <DialogHeader>
          <DialogTitle>Tailored materials — {selectedJob?.company}</DialogTitle>
        </DialogHeader>

        {!tailorResult ? <div>Loading…</div> : (
          <div className="space-y-3">
            <div>
              <div className="text-xs text-zinc-500">Revised bullets</div>
              <div className="rounded-xl border p-3 text-sm space-y-1">
                {tailorResult.revised_bullets?.map((b: string, i: number) => (<div key={i}>• {b}</div>))}
              </div>
            </div>
            <div>
              <div className="text-xs text-zinc-500">Cover letter</div>
              <Textarea rows={8} defaultValue={tailorResult.cover_letter} />
            </div>
            <div className="flex gap-2">
              {tailorResult.resume_docx_url && <a className="inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-sm" href={tailorResult.resume_docx_url} target="_blank" rel="noreferrer">Download Résumé</a>}
              {tailorResult.cover_letter_url && <a className="inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-sm" href={tailorResult.cover_letter_url} target="_blank" rel="noreferrer">Download Cover Letter</a>}
            </div>
          </div>
        )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
