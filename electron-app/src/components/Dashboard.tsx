import React, { useEffect, useMemo, useState } from 'react';
import { api } from '../services/api';
import type { TaskDefinition, TaskRun, TaskRunRequest, User } from '../types/api';
import { useAuth } from '../context/AuthContext';

interface DashboardProps {
  user: User;
}

const TASK_ORDER = ['download_zip', 'annotate_ok', 'export_relation'];

const sortTasks = (tasks: TaskDefinition[]): TaskDefinition[] =>
  [...tasks].sort((a, b) => TASK_ORDER.indexOf(a.slug) - TASK_ORDER.indexOf(b.slug));

export const Dashboard: React.FC<DashboardProps> = ({ user }) => {
  const { logout } = useAuth();
  const appVersion = window.seiautomation?.version ?? 'dev';
  const [tasks, setTasks] = useState<TaskDefinition[]>([]);
  const [runs, setRuns] = useState<TaskRun[]>([]);
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [headless, setHeadless] = useState<boolean>(user.allow_auto_credentials);
  const [autoCredentials, setAutoCredentials] = useState<boolean>(user.allow_auto_credentials);
  const [devMode, setDevMode] = useState<boolean>(false);
  const [blocoId, setBlocoId] = useState<string>('');
  const [limit, setLimit] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const allowAuto = user.allow_auto_credentials;

  const selectedSlugs = useMemo(() => Object.keys(selected).filter((slug) => selected[slug]), [selected]);

  const loadTasks = async () => {
    const { data } = await api.get<TaskDefinition[]>('/tasks/');
    setTasks(sortTasks(data));
    setSelected((prev) => {
      const next: Record<string, boolean> = {};
      data.forEach((task) => {
        next[task.slug] = prev[task.slug] ?? false;
      });
      return next;
    });
  };

  const loadRuns = async () => {
    const { data } = await api.get<TaskRun[]>('/tasks/runs');
    setRuns(data);
  };

  useEffect(() => {
    void loadTasks();
    void loadRuns();
    const interval = setInterval(() => {
      void loadRuns();
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleToggleTask = (slug: string) => {
    setSelected((prev) => ({ ...prev, [slug]: !prev[slug] }));
  };

  const handleRunTasks = async () => {
    if (selectedSlugs.length === 0) {
      setError('Selecione pelo menos uma tarefa.');
      return;
    }
    setLoading(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const payloadBase: Omit<TaskRunRequest, 'task_slug'> = {
        headless: allowAuto ? headless : false,
        auto_credentials: allowAuto ? autoCredentials : false,
        bloco_id: blocoId ? Number(blocoId) : undefined,
        limit: limit ? Number(limit) : undefined,
        dev_mode: devMode,
      };

      const responses: TaskRun[] = [];
      for (const slug of selectedSlugs) {
        const { data } = await api.post<TaskRun>('/tasks/run', {
          ...payloadBase,
          task_slug: slug,
        });
        responses.push(data);
      }
      setSuccessMessage(`${responses.length} tarefa(s) disparadas.`);
      await loadRuns();
    } catch (err) {
      console.error(err);
      setError('Falha ao enviar as tarefas. Verifique os dados e tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard">
      <header className="dashboard__header">
        <div>
          <h1>SEIAutomation</h1>
          <p>{user.full_name || user.email}</p>
          <small className="muted">Versão {appVersion}</small>
        </div>
        <button type="button" onClick={logout} className="secondary">
          Sair
        </button>
      </header>

      <section className="dashboard__card">
        <h2>Tarefas disponíveis</h2>
        <div className="tasks-grid">
          {tasks.map((task) => (
            <label key={task.slug} className="task-item">
              <input
                type="checkbox"
                checked={selected[task.slug] ?? false}
                onChange={() => handleToggleTask(task.slug)}
                disabled={loading}
              />
              <span>
                <strong>{task.name}</strong>
                <small>{task.description}</small>
              </span>
            </label>
          ))}
        </div>
      </section>

      <section className="dashboard__card">
        <h2>Parâmetros</h2>
        <div className="form-grid">
          <label>
            ID do bloco
            <input
              type="number"
              min="1"
              placeholder="Ex.: 55"
              value={blocoId}
              onChange={(event) => setBlocoId(event.target.value)}
              disabled={loading}
            />
          </label>
          <label>
            Limitar quantidade
            <input
              type="number"
              min="1"
              placeholder="Todos"
              value={limit}
              onChange={(event) => setLimit(event.target.value)}
              disabled={loading}
            />
          </label>
          <label className={!allowAuto ? 'disabled' : undefined}>
            <input
              type="checkbox"
              checked={allowAuto ? headless : false}
              onChange={(event) => setHeadless(event.target.checked)}
              disabled={!allowAuto || loading}
            />
            <span>Executar em modo headless</span>
          </label>
          <label className={!allowAuto ? 'disabled' : undefined}>
            <input
              type="checkbox"
              checked={allowAuto ? autoCredentials : false}
              onChange={(event) => setAutoCredentials(event.target.checked)}
              disabled={!allowAuto || loading}
            />
            <span>Preencher credenciais automaticamente</span>
          </label>
          <label>
            <input
              type="checkbox"
              checked={devMode}
              onChange={(event) => setDevMode(event.target.checked)}
              disabled={loading}
            />
            <span>Modo desenvolvedor</span>
          </label>
        </div>
        <button type="button" onClick={handleRunTasks} disabled={loading}>
          {loading ? 'Enviando…' : 'Executar tarefas selecionadas'}
        </button>
        {error && <div className="alert alert--error">{error}</div>}
        {successMessage && <div className="alert alert--success">{successMessage}</div>}
      </section>

      <section className="dashboard__card">
        <h2>Execuções recentes</h2>
        <div className="runs">
          {runs.length === 0 ? (
            <p className="muted">Nenhuma execução registrada ainda.</p>
          ) : (
            runs.map((run) => (
              <article key={run.id} className={`run run--${run.status.toLowerCase()}`}>
                <header>
                  <strong>{run.task_name}</strong>
                  <span>{new Date(run.created_at).toLocaleString()}</span>
                </header>
                <pre>{run.log || 'Sem logs disponíveis ainda.'}</pre>
              </article>
            ))
          )}
        </div>
      </section>
    </div>
  );
};
