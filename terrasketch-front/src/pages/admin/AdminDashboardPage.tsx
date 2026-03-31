import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  Users,
  FolderOpen,
  Cpu,
  LogOut,
  Search,
  ChevronDown,
  CheckCircle,
  XCircle,
  Clock,
  RefreshCw,
  TrendingUp,
  Map,
  Activity,
} from 'lucide-react';

// ─── Types ────────────────────────────────────────────────────────────────────

interface Stats {
  users: {
    total: number;
    new_7d: number;
    new_30d: number;
    by_role: Record<string, number>;
  };
  subscriptions: {
    active: number;
    trialing: number;
    by_plan: Record<string, number>;
  };
  projects: {
    total: number;
    new_30d: number;
    by_status: Record<string, number>;
  };
  ai_generation: {
    total_jobs: number;
    completed: number;
    failed: number;
    running: number;
    jobs_30d: number;
    success_rate: number;
  };
}

interface AdminUser {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_verified: boolean;
  is_active: boolean;
  created_at: string;
  subscription_plan: string | null;
  subscription_status: string | null;
  projects_count: number;
}

interface AdminProject {
  id: string;
  name: string;
  status: string;
  user_email: string;
  city: string;
  budget_tier: string | null;
  created_at: string;
  ai_plans_count: number;
}

interface AIJob {
  id: string;
  status: string;
  progress_pct: number;
  current_step: string | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  project_name: string;
  user_email: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const API_BASE = 'http://localhost:8000/api/backoffice';

async function apiFetch<T>(path: string, token: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...options?.headers,
    },
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('fr-FR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
  });
}

// ─── Badge ────────────────────────────────────────────────────────────────────

const ROLE_COLORS: Record<string, string> = {
  particular: 'bg-blue-100 text-blue-700',
  pro: 'bg-purple-100 text-purple-700',
  agency: 'bg-orange-100 text-orange-700',
  admin: 'bg-red-100 text-red-700',
};

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-600',
  in_progress: 'bg-blue-100 text-blue-700',
  completed: 'bg-green-100 text-green-700',
  archived: 'bg-yellow-100 text-yellow-700',
  pending: 'bg-yellow-100 text-yellow-700',
  running: 'bg-blue-100 text-blue-700',
  failed: 'bg-red-100 text-red-700',
  active: 'bg-green-100 text-green-700',
  trialing: 'bg-purple-100 text-purple-700',
  cancelled: 'bg-gray-100 text-gray-600',
};

function Badge({ label }: { label: string }) {
  const color = ROLE_COLORS[label] ?? STATUS_COLORS[label] ?? 'bg-gray-100 text-gray-600';
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${color}`}>
      {label}
    </span>
  );
}

// ─── KPI Card ─────────────────────────────────────────────────────────────────

function KpiCard({
  icon: Icon,
  label,
  value,
  sub,
  color,
}: {
  icon: React.ElementType;
  label: string;
  value: number | string;
  sub?: string;
  color: string;
}) {
  return (
    <div className="card flex items-start gap-4">
      <div className={`w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0 ${color}`}>
        <Icon className="w-6 h-6 text-white" />
      </div>
      <div>
        <p className="text-sm text-gray-500">{label}</p>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

// ─── Sidebar ──────────────────────────────────────────────────────────────────

type Section = 'overview' | 'users' | 'projects' | 'ai';

function Sidebar({
  active,
  onChange,
}: {
  active: Section;
  onChange: (s: Section) => void;
}) {
  const links: { id: Section; label: string; icon: React.ElementType }[] = [
    { id: 'overview', label: 'Vue d\'ensemble', icon: LayoutDashboard },
    { id: 'users', label: 'Utilisateurs', icon: Users },
    { id: 'projects', label: 'Projets', icon: FolderOpen },
    { id: 'ai', label: 'Génération IA', icon: Cpu },
  ];

  return (
    <aside className="w-60 bg-white border-r border-gray-200 flex flex-col min-h-screen">
      <div className="px-5 py-4 border-b border-gray-200 flex items-center gap-3">
        <div className="w-9 h-9 bg-green-600 rounded-lg flex items-center justify-center">
          <Map className="w-5 h-5 text-white" />
        </div>
        <div>
          <p className="font-bold text-gray-900 text-sm">TerraSketch</p>
          <p className="text-xs text-gray-400">Admin</p>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {links.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => onChange(id)}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              active === id
                ? 'bg-green-50 text-green-700'
                : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
            }`}
          >
            <Icon className="w-4 h-4 flex-shrink-0" />
            {label}
          </button>
        ))}
      </nav>

      <div className="px-3 py-4 border-t border-gray-200">
        <a
          href="/dashboard"
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-500 hover:bg-gray-50 hover:text-gray-900 transition-colors"
        >
          <LogOut className="w-4 h-4" />
          Retour app
        </a>
      </div>
    </aside>
  );
}

// ─── Overview Section ─────────────────────────────────────────────────────────

function OverviewSection({ stats }: { stats: Stats }) {
  const { users, subscriptions, projects, ai_generation } = stats;

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Vue d'ensemble</h2>
        <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
          <KpiCard
            icon={Users}
            label="Utilisateurs"
            value={users.total}
            sub={`+${users.new_7d} cette semaine`}
            color="bg-blue-600"
          />
          <KpiCard
            icon={Activity}
            label="Abonnements actifs"
            value={subscriptions.active}
            sub={`${subscriptions.trialing} en essai`}
            color="bg-green-600"
          />
          <KpiCard
            icon={FolderOpen}
            label="Projets"
            value={projects.total}
            sub={`+${projects.new_30d} ce mois`}
            color="bg-purple-600"
          />
          <KpiCard
            icon={Cpu}
            label="Jobs IA (total)"
            value={ai_generation.total_jobs}
            sub={`${ai_generation.success_rate}% de succès`}
            color="bg-orange-500"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Répartition rôles */}
        <div className="card">
          <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
            <Users className="w-4 h-4 text-blue-500" />
            Rôles utilisateurs
          </h3>
          <ul className="space-y-2">
            {Object.entries(users.by_role).map(([role, count]) => (
              <li key={role} className="flex items-center justify-between text-sm">
                <Badge label={role} />
                <span className="font-semibold text-gray-800">{count}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Statuts projets */}
        <div className="card">
          <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
            <FolderOpen className="w-4 h-4 text-purple-500" />
            Statuts projets
          </h3>
          <ul className="space-y-2">
            {Object.entries(projects.by_status).map(([s, count]) => (
              <li key={s} className="flex items-center justify-between text-sm">
                <Badge label={s} />
                <span className="font-semibold text-gray-800">{count}</span>
              </li>
            ))}
            {Object.keys(projects.by_status).length === 0 && (
              <li className="text-sm text-gray-400">Aucun projet</li>
            )}
          </ul>
        </div>

        {/* IA */}
        <div className="card">
          <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-orange-500" />
            Génération IA
          </h3>
          <ul className="space-y-2 text-sm">
            <li className="flex justify-between">
              <span className="text-gray-500">Complétés</span>
              <span className="font-semibold text-green-600">{ai_generation.completed}</span>
            </li>
            <li className="flex justify-between">
              <span className="text-gray-500">Échoués</span>
              <span className="font-semibold text-red-500">{ai_generation.failed}</span>
            </li>
            <li className="flex justify-between">
              <span className="text-gray-500">En cours</span>
              <span className="font-semibold text-blue-500">{ai_generation.running}</span>
            </li>
            <li className="flex justify-between">
              <span className="text-gray-500">Ce mois</span>
              <span className="font-semibold text-gray-800">{ai_generation.jobs_30d}</span>
            </li>
            <li className="pt-2 border-t border-gray-100 flex justify-between">
              <span className="text-gray-500">Taux de succès</span>
              <span className="font-bold text-green-600">{ai_generation.success_rate}%</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}

// ─── Users Section ────────────────────────────────────────────────────────────

function UsersSection({ token }: { token: string }) {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [updating, setUpdating] = useState<string | null>(null);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.set('search', search);
      if (roleFilter) params.set('role', roleFilter);
      const data = await apiFetch<AdminUser[]>(`/users/?${params}`, token);
      setUsers(data);
    } catch {
      // silently ignore in demo
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchUsers(); }, [roleFilter]);

  const toggleActive = async (user: AdminUser) => {
    setUpdating(user.id);
    try {
      const updated = await apiFetch<AdminUser>(`/users/${user.id}/`, token, {
        method: 'PATCH',
        body: JSON.stringify({ is_active: !user.is_active }),
      });
      setUsers(prev => prev.map(u => (u.id === updated.id ? updated : u)));
    } finally {
      setUpdating(null);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Utilisateurs</h2>
        <span className="text-sm text-gray-400">{users.length} résultats</span>
      </div>

      {/* Filtres */}
      <div className="flex gap-3 flex-wrap">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            className="input-base pl-9 w-64"
            placeholder="Rechercher…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && fetchUsers()}
          />
        </div>
        <div className="relative">
          <select
            className="input-base pr-8 appearance-none"
            value={roleFilter}
            onChange={e => setRoleFilter(e.target.value)}
          >
            <option value="">Tous les rôles</option>
            <option value="particular">Particulier</option>
            <option value="pro">Pro</option>
            <option value="agency">Agence</option>
            <option value="admin">Admin</option>
          </select>
          <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
        </div>
        <button
          className="btn-secondary flex items-center gap-2"
          onClick={fetchUsers}
        >
          <RefreshCw className="w-4 h-4" />
          Actualiser
        </button>
      </div>

      {/* Table */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-400">Chargement…</div>
        ) : users.length === 0 ? (
          <div className="p-8 text-center text-gray-400">Aucun utilisateur trouvé.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Utilisateur</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Rôle</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Abonnement</th>
                  <th className="text-center px-4 py-3 font-medium text-gray-600">Projets</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Inscrit le</th>
                  <th className="text-center px-4 py-3 font-medium text-gray-600">Statut</th>
                  <th className="text-center px-4 py-3 font-medium text-gray-600">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map(user => (
                  <tr key={user.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-900">{user.full_name}</div>
                      <div className="text-gray-400 text-xs">{user.email}</div>
                    </td>
                    <td className="px-4 py-3"><Badge label={user.role} /></td>
                    <td className="px-4 py-3">
                      {user.subscription_plan ? (
                        <div className="space-y-0.5">
                          <span className="text-gray-700 capitalize">{user.subscription_plan}</span>
                          {user.subscription_status && (
                            <div><Badge label={user.subscription_status} /></div>
                          )}
                        </div>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center font-semibold text-gray-700">
                      {user.projects_count}
                    </td>
                    <td className="px-4 py-3 text-gray-500">{formatDate(user.created_at)}</td>
                    <td className="px-4 py-3 text-center">
                      {user.is_active ? (
                        <CheckCircle className="w-4 h-4 text-green-500 inline" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-400 inline" />
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={() => toggleActive(user)}
                        disabled={updating === user.id}
                        className={`text-xs font-medium px-3 py-1 rounded-lg transition-colors ${
                          user.is_active
                            ? 'bg-red-50 text-red-600 hover:bg-red-100'
                            : 'bg-green-50 text-green-600 hover:bg-green-100'
                        }`}
                      >
                        {updating === user.id ? '…' : user.is_active ? 'Désactiver' : 'Activer'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Projects Section ─────────────────────────────────────────────────────────

function ProjectsSection({ token }: { token: string }) {
  const [projects, setProjects] = useState<AdminProject[]>([]);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState('');

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set('status', statusFilter);
      const data = await apiFetch<AdminProject[]>(`/projects/?${params}`, token);
      setProjects(data);
    } catch {
      // silently ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchProjects(); }, [statusFilter]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Projets</h2>
        <span className="text-sm text-gray-400">{projects.length} résultats</span>
      </div>

      <div className="flex gap-3 flex-wrap">
        <div className="relative">
          <select
            className="input-base pr-8 appearance-none"
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
          >
            <option value="">Tous les statuts</option>
            <option value="draft">Brouillon</option>
            <option value="in_progress">En cours</option>
            <option value="completed">Terminé</option>
            <option value="archived">Archivé</option>
          </select>
          <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
        </div>
        <button className="btn-secondary flex items-center gap-2" onClick={fetchProjects}>
          <RefreshCw className="w-4 h-4" />
          Actualiser
        </button>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-400">Chargement…</div>
        ) : projects.length === 0 ? (
          <div className="p-8 text-center text-gray-400">Aucun projet trouvé.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Projet</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Propriétaire</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Statut</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Ville</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Budget</th>
                  <th className="text-center px-4 py-3 font-medium text-gray-600">Plans IA</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Créé le</th>
                </tr>
              </thead>
              <tbody>
                {projects.map(p => (
                  <tr key={p.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 font-medium text-gray-900">{p.name}</td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{p.user_email}</td>
                    <td className="px-4 py-3"><Badge label={p.status} /></td>
                    <td className="px-4 py-3 text-gray-600">{p.city || '—'}</td>
                    <td className="px-4 py-3">
                      {p.budget_tier ? <Badge label={p.budget_tier} /> : <span className="text-gray-400">—</span>}
                    </td>
                    <td className="px-4 py-3 text-center font-semibold text-purple-600">
                      {p.ai_plans_count}
                    </td>
                    <td className="px-4 py-3 text-gray-500">{formatDate(p.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── AI Jobs Section ──────────────────────────────────────────────────────────

const JOB_STATUS_ICON: Record<string, React.ReactNode> = {
  completed: <CheckCircle className="w-4 h-4 text-green-500" />,
  failed: <XCircle className="w-4 h-4 text-red-500" />,
  running: <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />,
  pending: <Clock className="w-4 h-4 text-yellow-500" />,
};

function AISection({ token }: { token: string }) {
  const [jobs, setJobs] = useState<AIJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState('');

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set('status', statusFilter);
      const data = await apiFetch<AIJob[]>(`/ai-jobs/?${params}`, token);
      setJobs(data);
    } catch {
      // silently ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchJobs(); }, [statusFilter]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Jobs de génération IA</h2>
        <span className="text-sm text-gray-400">{jobs.length} résultats</span>
      </div>

      <div className="flex gap-3 flex-wrap">
        <div className="relative">
          <select
            className="input-base pr-8 appearance-none"
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
          >
            <option value="">Tous</option>
            <option value="pending">En attente</option>
            <option value="running">En cours</option>
            <option value="completed">Complétés</option>
            <option value="failed">Échoués</option>
          </select>
          <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
        </div>
        <button className="btn-secondary flex items-center gap-2" onClick={fetchJobs}>
          <RefreshCw className="w-4 h-4" />
          Actualiser
        </button>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-400">Chargement…</div>
        ) : jobs.length === 0 ? (
          <div className="p-8 text-center text-gray-400">Aucun job trouvé.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left px-4 py-3 font-medium text-gray-600">ID</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Projet</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Utilisateur</th>
                  <th className="text-center px-4 py-3 font-medium text-gray-600">Statut</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Étape</th>
                  <th className="text-center px-4 py-3 font-medium text-gray-600">Progres</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Créé le</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map(job => (
                  <tr key={job.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-gray-500">{job.id}</td>
                    <td className="px-4 py-3 font-medium text-gray-900">{job.project_name}</td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{job.user_email}</td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex items-center justify-center gap-1">
                        {JOB_STATUS_ICON[job.status] ?? null}
                        <Badge label={job.status} />
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {job.error_message ? (
                        <span className="text-red-500 line-clamp-1">{job.error_message}</span>
                      ) : (
                        job.current_step || '—'
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <div className="w-16 bg-gray-100 rounded-full h-1.5">
                          <div
                            className="bg-green-500 h-1.5 rounded-full transition-all"
                            style={{ width: `${job.progress_pct}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500">{job.progress_pct}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-500">{formatDate(job.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Login Form ───────────────────────────────────────────────────────────────

function AdminLogin({ onLogin }: { onLogin: (token: string) => void }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/auth/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Connexion échouée');
      if (!data.user?.is_staff && data.user?.role !== 'admin') {
        throw new Error('Accès réservé aux administrateurs.');
      }
      onLogin(data.access);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Erreur inconnue');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="card w-full max-w-sm">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-green-600 rounded-lg flex items-center justify-center">
            <Map className="w-5 h-5 text-white" />
          </div>
          <div>
            <p className="font-bold text-gray-900">TerraSketch Admin</p>
            <p className="text-xs text-gray-400">Connexion administrateur</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              className="input-base"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Mot de passe</label>
            <input
              type="password"
              className="input-base"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />
          </div>
          {error && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {error}
            </p>
          )}
          <button type="submit" className="btn-primary w-full" disabled={loading}>
            {loading ? 'Connexion…' : 'Se connecter'}
          </button>
        </form>
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

const AdminDashboardPage: React.FC = () => {
  const [token, setToken] = useState<string | null>(() => sessionStorage.getItem('admin_token'));
  const [section, setSection] = useState<Section>('overview');
  const [stats, setStats] = useState<Stats | null>(null);
  const [statsLoading, setStatsLoading] = useState(false);

  useEffect(() => {
    if (!token) return;
    setStatsLoading(true);
    apiFetch<Stats>('/stats/', token)
      .then(setStats)
      .catch(() => setToken(null))
      .finally(() => setStatsLoading(false));
  }, [token]);

  const handleLogin = (t: string) => {
    sessionStorage.setItem('admin_token', t);
    setToken(t);
  };

  const handleLogout = () => {
    sessionStorage.removeItem('admin_token');
    setToken(null);
  };

  if (!token) return <AdminLogin onLogin={handleLogin} />;

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar active={section} onChange={setSection} />

      <main className="flex-1 overflow-auto">
        {/* Top bar */}
        <header className="bg-white border-b border-gray-200 px-8 py-4 flex items-center justify-between sticky top-0 z-10">
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <TrendingUp className="w-4 h-4" />
            <span>Dashboard Admin</span>
          </div>
          <button
            onClick={handleLogout}
            className="text-sm text-gray-500 hover:text-red-500 flex items-center gap-1.5 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Déconnexion
          </button>
        </header>

        <div className="px-8 py-6">
          {section === 'overview' && (
            statsLoading || !stats
              ? <div className="text-center text-gray-400 py-16">Chargement des statistiques…</div>
              : <OverviewSection stats={stats} />
          )}
          {section === 'users' && <UsersSection token={token} />}
          {section === 'projects' && <ProjectsSection token={token} />}
          {section === 'ai' && <AISection token={token} />}
        </div>
      </main>
    </div>
  );
};

export default AdminDashboardPage;
