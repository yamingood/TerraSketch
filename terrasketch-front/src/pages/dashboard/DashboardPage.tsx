import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Map, Plus, FileText, Settings, RefreshCw,
  Cpu, Clock, CheckCircle, XCircle, ChevronRight,
  Leaf, LayoutDashboard, LogOut,
} from 'lucide-react';
import { api } from '../../api/client';
import type { Project } from '../../api/client';

// ─── Types ────────────────────────────────────────────────────────────────────

interface DashboardStats {
  total_projects: number;
  projects_by_status: Record<string, number>;
  recent_activity: unknown[];
}

interface GenerationJob {
  job_id?: string;
  id?: string;
  status: string;
  progress_pct: number;
  current_step: string | null;
  error_message?: string | null;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const STATUS_LABEL: Record<string, string> = {
  draft: 'Brouillon',
  in_progress: 'En cours',
  completed: 'Terminé',
  archived: 'Archivé',
};

const STATUS_COLOR: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-600',
  in_progress: 'bg-blue-100 text-blue-700',
  completed: 'bg-green-100 text-green-700',
  archived: 'bg-yellow-100 text-yellow-700',
};

function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${STATUS_COLOR[status] ?? 'bg-gray-100 text-gray-600'}`}>
      {STATUS_LABEL[status] ?? status}
    </span>
  );
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('fr-FR', {
    day: '2-digit', month: 'short', year: 'numeric',
  });
}

// ─── Generation Status Bar ────────────────────────────────────────────────────

function GenerationBar({ job, onDone }: { job: GenerationJob; onDone: (planId: string) => void }) {
  const [current, setCurrent] = useState(job);

  useEffect(() => {
    if (current.status === 'completed' || current.status === 'failed') return;
    const jobId = current.job_id ?? current.id ?? '';

    const interval = setInterval(async () => {
      try {
        const updated = await api.get<GenerationJob>(`/projects/generate/${jobId}/`);
        setCurrent(updated);
        if (updated.status === 'completed') {
          clearInterval(interval);
          onDone(jobId);
        }
        if (updated.status === 'failed') clearInterval(interval);
      } catch { clearInterval(interval); }
    }, 2000);

    return () => clearInterval(interval);
  }, [current.status]);

  const pct = current.progress_pct ?? 0;

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 text-sm font-medium text-blue-800">
          {current.status === 'completed'
            ? <CheckCircle className="w-4 h-4 text-green-500" />
            : current.status === 'failed'
            ? <XCircle className="w-4 h-4 text-red-500" />
            : <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />}
          {current.status === 'completed'
            ? 'Plan généré !'
            : current.status === 'failed'
            ? 'Échec de la génération'
            : 'Génération en cours…'}
        </div>
        <span className="text-xs text-blue-600">{pct}%</span>
      </div>
      <div className="w-full bg-blue-100 rounded-full h-1.5 mb-1">
        <div
          className="bg-blue-500 h-1.5 rounded-full transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      {current.current_step && (
        <p className="text-xs text-blue-600 mt-1">{current.current_step}</p>
      )}
      {current.error_message && (
        <p className="text-xs text-red-500 mt-1">{current.error_message}</p>
      )}
    </div>
  );
}

// ─── Project Card ─────────────────────────────────────────────────────────────

function ProjectCard({
  project,
  onGenerate,
  onView,
  generating,
}: {
  project: Project;
  onGenerate: (id: string) => void;
  onView: (id: string) => void;
  generating: boolean;
}) {
  return (
    <div className="card hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 truncate">{project.name}</h3>
          <p className="text-xs text-gray-400 mt-0.5">
            {project.city || 'Localisation non renseignée'} · {formatDate(project.created_at)}
          </p>
        </div>
        <StatusBadge status={project.status} />
      </div>

      <div className="flex gap-2 mt-4">
        <button
          onClick={() => onView(project.id)}
          className="flex-1 flex items-center justify-center gap-1.5 text-sm text-gray-600 border border-gray-200 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition-colors"
        >
          <Map className="w-3.5 h-3.5" /> Voir le plan
        </button>
        <button
          onClick={() => onGenerate(project.id)}
          disabled={generating}
          className="flex-1 flex items-center justify-center gap-1.5 text-sm bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white px-3 py-1.5 rounded-lg transition-colors"
        >
          <Cpu className="w-3.5 h-3.5" />
          {generating ? 'En cours…' : 'Générer IA'}
        </button>
      </div>
    </div>
  );
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();

  const [projects, setProjects] = useState<Project[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeJobs, setActiveJobs] = useState<Record<string, GenerationJob>>({});
  const [generatingFor, setGeneratingFor] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [projectsData, statsData] = await Promise.all([
        api.get<Project[]>('/projects/'),
        api.get<DashboardStats>('/projects/dashboard/stats/').catch(() => null),
      ]);
      setProjects(projectsData);
      if (statsData) setStats(statsData);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erreur de chargement');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleGenerate = async (projectId: string) => {
    setGeneratingFor(projectId);
    try {
      const job = await api.post<GenerationJob>(`/projects/${projectId}/generate/`, {});
      setActiveJobs(prev => ({ ...prev, [projectId]: job }));
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Erreur lors du lancement');
    } finally {
      setGeneratingFor(null);
    }
  };

  const handleJobDone = (projectId: string, _jobId: string) => {
    setActiveJobs(prev => {
      const next = { ...prev };
      delete next[projectId];
      return next;
    });
    loadData();
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    navigate('/onboarding');
  };

  // ── KPI summary ──────────────────────────────────────────────────────────────
  const kpis = [
    {
      label: 'Projets totaux',
      value: stats?.total_projects ?? projects.length,
      icon: FolderIcon,
      color: 'bg-blue-500',
    },
    {
      label: 'En cours',
      value: stats?.projects_by_status?.in_progress ?? projects.filter(p => p.status === 'in_progress').length,
      icon: Clock,
      color: 'bg-orange-400',
    },
    {
      label: 'Terminés',
      value: stats?.projects_by_status?.completed ?? projects.filter(p => p.status === 'completed').length,
      icon: CheckCircle,
      color: 'bg-green-500',
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside className="w-56 bg-white border-r border-gray-200 flex flex-col">
        <div className="px-5 py-4 border-b border-gray-200 flex items-center gap-3">
          <div className="w-9 h-9 bg-green-600 rounded-lg flex items-center justify-center">
            <Map className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-gray-900">TerraSketch</span>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {[
            { icon: LayoutDashboard, label: 'Tableau de bord', active: true, onClick: () => {} },
            { icon: Plus, label: 'Nouveau projet', active: false, onClick: () => navigate('/onboarding') },
            { icon: Leaf, label: 'Plantes', active: false, onClick: () => {} },
            { icon: Settings, label: 'Paramètres', active: false, onClick: () => {} },
          ].map(({ icon: Icon, label, active, onClick }) => (
            <button
              key={label}
              onClick={onClick}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                active ? 'bg-green-50 text-green-700' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </nav>

        <div className="px-3 py-4 border-t border-gray-200 space-y-1">
          <button
            onClick={() => navigate('/admin')}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-500 hover:bg-gray-50 hover:text-gray-900 transition-colors"
          >
            <Settings className="w-4 h-4" /> Admin
          </button>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-500 hover:bg-red-50 hover:text-red-600 transition-colors"
          >
            <LogOut className="w-4 h-4" /> Déconnexion
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto">
        {/* Top bar */}
        <header className="bg-white border-b border-gray-200 px-8 py-4 flex items-center justify-between sticky top-0 z-10">
          <h1 className="text-lg font-semibold text-gray-900">Tableau de bord</h1>
          <div className="flex items-center gap-3">
            <button
              onClick={loadData}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              title="Actualiser"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={() => navigate('/onboarding')}
              className="btn-primary flex items-center gap-2 text-sm"
            >
              <Plus className="w-4 h-4" /> Nouveau projet
            </button>
          </div>
        </header>

        <div className="px-8 py-6 space-y-8">
          {/* Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-700 flex items-center gap-2">
              <XCircle className="w-4 h-4 flex-shrink-0" />
              {error} —{' '}
              <button onClick={loadData} className="underline">Réessayer</button>
            </div>
          )}

          {/* KPIs */}
          <div className="grid grid-cols-3 gap-4">
            {kpis.map(({ label, value, icon: Icon, color }) => (
              <div key={label} className="card flex items-center gap-4">
                <div className={`w-10 h-10 ${color} rounded-lg flex items-center justify-center flex-shrink-0`}>
                  <Icon className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">{value}</p>
                  <p className="text-xs text-gray-500">{label}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Active generation jobs */}
          {Object.entries(activeJobs).map(([projectId, job]) => (
            <GenerationBar
              key={projectId}
              job={job}
              onDone={(jobId) => handleJobDone(projectId, jobId)}
            />
          ))}

          {/* Projects list */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-gray-900">Mes projets</h2>
              <span className="text-sm text-gray-400">{projects.length} projet{projects.length !== 1 ? 's' : ''}</span>
            </div>

            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {[1, 2, 3].map(i => (
                  <div key={i} className="card animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
                    <div className="h-3 bg-gray-100 rounded w-1/2 mb-4" />
                    <div className="h-8 bg-gray-100 rounded" />
                  </div>
                ))}
              </div>
            ) : projects.length === 0 ? (
              <div className="card text-center py-12">
                <Map className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500 font-medium mb-1">Aucun projet pour l'instant</p>
                <p className="text-sm text-gray-400 mb-4">
                  Importez votre premier plan cadastral pour commencer
                </p>
                <button
                  onClick={() => navigate('/onboarding')}
                  className="btn-primary inline-flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" /> Créer mon premier projet
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {projects.map(project => (
                  <ProjectCard
                    key={project.id}
                    project={project}
                    onGenerate={handleGenerate}
                    onView={(id) => navigate(`/plan/${id}`)}
                    generating={generatingFor === project.id}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Quick actions */}
          <div>
            <h2 className="text-base font-semibold text-gray-900 mb-4">Actions rapides</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button
                onClick={() => navigate('/onboarding')}
                className="card hover:shadow-md transition-shadow text-left flex items-center justify-between group"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <FileText className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Importer un cadastre</p>
                    <p className="text-sm text-gray-500">GeoJSON, Shapefile, DXF, EDIGÉO</p>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600" />
              </button>

              <button
                onClick={() => navigate('/plan/demo-plan')}
                className="card hover:shadow-md transition-shadow text-left flex items-center justify-between group"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                    <Map className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Plan de démonstration</p>
                    <p className="text-sm text-gray-500">Jardin méditerranéen généré par IA</p>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600" />
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

// Small inline icon (avoids heroicons dep for FolderOpen)
const FolderIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
  </svg>
);

export default DashboardPage;
