import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { api, formatApiError } from "@/lib/apiClient";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { ArrowLeft, CheckCircle, ListBullets, PencilSimple } from "@phosphor-icons/react";

export default function AppFormPage() {
  const { appId } = useParams();
  const navigate = useNavigate();
  const [appDef, setAppDef] = useState(null);
  const [values, setValues] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [submissions, setSubmissions] = useState([]);
  const [loadingList, setLoadingList] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get(`/apps/${appId}`);
        setAppDef(data);
        const init = {};
        for (const f of data.fields) init[f.name] = "";
        setValues(init);
      } catch (e) {
        toast.error(formatApiError(e));
        navigate("/portal");
      }
    })();
  }, [appId, navigate]);

  const loadSubmissions = async () => {
    setLoadingList(true);
    try {
      const { data } = await api.get(`/apps/${appId}/submissions`);
      setSubmissions(data);
    } catch (e) {
      toast.error(formatApiError(e));
    } finally {
      setLoadingList(false);
    }
  };

  useEffect(() => {
    if (appDef) loadSubmissions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [appDef]);

  const submit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post(`/apps/${appId}/submissions`, { data: values });
      toast.success("Registro guardado correctamente");
      const init = {};
      for (const f of appDef.fields) init[f.name] = "";
      setValues(init);
      loadSubmissions();
    } catch (err) {
      toast.error(formatApiError(err));
    } finally {
      setSubmitting(false);
    }
  };

  if (!appDef) {
    return <div className="text-sm text-muted-foreground">Cargando formulario…</div>;
  }

  return (
    <div className="space-y-8" data-testid="app-form-page">
      <div>
        <Link
          to="/portal"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
          data-testid="back-to-portal"
        >
          <ArrowLeft size={14} weight="bold" />
          Volver al portal
        </Link>
        <div className="eyebrow mt-4 mb-2">Aplicación · Formulario</div>
        <h1 className="font-display text-3xl sm:text-4xl font-bold tracking-tight">
          {appDef.name}
        </h1>
        <p className="text-muted-foreground mt-2 max-w-2xl">{appDef.description}</p>
      </div>

      <Tabs defaultValue="nuevo">
        <TabsList data-testid="app-tabs">
          <TabsTrigger value="nuevo" data-testid="tab-nuevo">
            <PencilSimple size={14} weight="bold" className="mr-2" />
            Nuevo registro
          </TabsTrigger>
          <TabsTrigger value="lista" data-testid="tab-lista">
            <ListBullets size={14} weight="bold" className="mr-2" />
            Registros ({submissions.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="nuevo" className="mt-6">
          <form
            onSubmit={submit}
            className="max-w-2xl rounded-md border border-border bg-card p-6 sm:p-8 space-y-5"
            data-testid="app-form"
          >
            {appDef.fields.map((f) => (
              <FieldRenderer
                key={f.name}
                field={f}
                value={values[f.name]}
                onChange={(v) => setValues((s) => ({ ...s, [f.name]: v }))}
              />
            ))}
            <div className="pt-2">
              <Button
                type="submit"
                disabled={submitting}
                className="w-full sm:w-auto h-11 px-8"
                data-testid="submit-form-btn"
              >
                <CheckCircle size={16} weight="bold" className="mr-2" />
                {submitting ? "Guardando…" : "Guardar registro"}
              </Button>
            </div>
          </form>
        </TabsContent>

        <TabsContent value="lista" className="mt-6">
          <SubmissionsTable
            appDef={appDef}
            submissions={submissions}
            loading={loadingList}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function FieldRenderer({ field, value, onChange }) {
  const id = `field-${field.name}`;
  return (
    <div className="space-y-2">
      <Label htmlFor={id} className="text-xs uppercase tracking-[0.2em]">
        {field.label} {field.required && <span className="text-destructive">*</span>}
      </Label>
      {field.type === "textarea" ? (
        <Textarea
          id={id}
          value={value || ""}
          onChange={(e) => onChange(e.target.value)}
          rows={4}
          required={field.required}
          data-testid={`field-${field.name}`}
        />
      ) : field.type === "select" ? (
        <Select value={value || ""} onValueChange={onChange}>
          <SelectTrigger id={id} data-testid={`field-${field.name}`}>
            <SelectValue placeholder="Selecciona una opción" />
          </SelectTrigger>
          <SelectContent>
            {field.options.map((opt) => (
              <SelectItem key={opt} value={opt}>
                {opt}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      ) : (
        <Input
          id={id}
          type={field.type}
          value={value || ""}
          onChange={(e) => onChange(e.target.value)}
          required={field.required}
          data-testid={`field-${field.name}`}
        />
      )}
    </div>
  );
}

function SubmissionsTable({ appDef, submissions, loading }) {
  const cols = useMemo(() => appDef.fields.slice(0, 4), [appDef]);
  if (loading) return <div className="text-sm text-muted-foreground">Cargando registros…</div>;
  if (submissions.length === 0) {
    return (
      <div className="rounded-md border border-dashed border-border p-10 text-center bg-muted/30">
        <div className="font-display text-lg font-semibold">No hay registros</div>
        <p className="text-sm text-muted-foreground mt-2">
          Aún no se ha registrado ningún envío para esta aplicación.
        </p>
      </div>
    );
  }
  return (
    <div className="rounded-md border border-border overflow-hidden bg-card">
      <div className="overflow-x-auto">
        <table className="w-full text-sm" data-testid="submissions-table">
          <thead className="bg-muted/50 text-xs uppercase tracking-[0.15em] text-muted-foreground">
            <tr>
              {cols.map((c) => (
                <th key={c.name} className="text-left px-4 py-3 font-medium">
                  {c.label}
                </th>
              ))}
              <th className="text-left px-4 py-3 font-medium">Registrado por</th>
              <th className="text-right px-4 py-3 font-medium">Fecha</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {submissions.map((s) => (
              <tr key={s.id} className="hover:bg-muted/30 transition-colors">
                {cols.map((c) => (
                  <td key={c.name} className="px-4 py-3 truncate max-w-[220px]">
                    {String(s.data?.[c.name] ?? "—")}
                  </td>
                ))}
                <td className="px-4 py-3 text-muted-foreground">{s.user_email}</td>
                <td className="px-4 py-3 text-right text-muted-foreground tabular-nums">
                  {new Date(s.created_at).toLocaleString("es")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
