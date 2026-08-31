import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, formatApiError } from "@/lib/apiClient";
import { useAuth } from "@/context/AuthContext";
import { toast } from "sonner";
import {
  UsersFour,
  Warning,
  Package,
  IdentificationCard,
  ChatCircleDots,
  ArrowRight,
  FolderOpen,
} from "@phosphor-icons/react";

const ICONS = { UsersFour, Warning, Package, IdentificationCard, ChatCircleDots };
const ACCENT = {
  blue: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
  amber: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
  emerald: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  violet: "bg-violet-500/10 text-violet-600 dark:text-violet-400",
  rose: "bg-rose-500/10 text-rose-600 dark:text-rose-400",
};

export default function DashboardPage() {
  const { user } = useAuth();
  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get("/apps");
        setApps(data);
      } catch (e) {
        toast.error(formatApiError(e));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="space-y-10" data-testid="dashboard-page">
      <div>
        <div className="eyebrow mb-2">Panel Principal</div>
        <h1 className="font-display text-4xl sm:text-5xl font-bold tracking-tight">
          Hola, {user?.name?.split(" ")[0] || "usuario"}.
        </h1>
        <p className="text-muted-foreground mt-3 max-w-2xl leading-relaxed">
          Estas son las aplicaciones que tu rol tiene habilitadas. Selecciona una para
          registrar nuevos datos o revisar los envíos recientes.
        </p>
      </div>

      {loading ? (
        <div className="text-sm text-muted-foreground">Cargando aplicaciones…</div>
      ) : apps.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-5" data-testid="apps-grid">
          {apps.map((a) => {
            const Icon = ICONS[a.icon] || FolderOpen;
            return (
              <Link
                key={a.id}
                to={`/apps/${a.id}`}
                data-testid={`app-card-${a.id}`}
                className="group relative rounded-md border border-border bg-card p-6 hover:-translate-y-1 hover:shadow-md transition-transform"
              >
                <div className="flex items-start justify-between">
                  <div className={`h-11 w-11 rounded-md grid place-items-center ${ACCENT[a.accent] || ACCENT.blue}`}>
                    <Icon size={22} weight="bold" />
                  </div>
                  <ArrowRight
                    size={18}
                    weight="bold"
                    className="text-muted-foreground group-hover:text-foreground group-hover:translate-x-0.5 transition-transform"
                  />
                </div>
                <div className="mt-6">
                  <div className="eyebrow mb-2">Formulario</div>
                  <h3 className="font-display text-xl font-semibold tracking-tight">
                    {a.name}
                  </h3>
                  <p className="text-sm text-muted-foreground mt-2 leading-relaxed">
                    {a.description}
                  </p>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="rounded-md border border-dashed border-border p-10 text-center bg-muted/30">
      <FolderOpen size={36} weight="regular" className="mx-auto text-muted-foreground" />
      <h3 className="font-display text-xl font-semibold mt-4">Sin aplicaciones asignadas</h3>
      <p className="text-sm text-muted-foreground mt-2 max-w-md mx-auto">
        Tu cuenta aún no tiene acceso a ningún formulario. Solicita al administrador que
        te asigne permisos.
      </p>
    </div>
  );
}
