import React, { useEffect, useState } from "react";
import { api, formatApiError } from "@/lib/apiClient";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Plus, PencilSimple, Trash, UsersFour } from "@phosphor-icons/react";
import { useAuth } from "@/context/AuthContext";

const ROLE_LABEL = { admin: "Administrador", editor: "Editor", user: "Usuario" };
const ROLE_TINT = {
  admin: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
  editor: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  user: "bg-muted text-muted-foreground",
};

const emptyForm = {
  id: null,
  email: "",
  name: "",
  password: "",
  role: "user",
  allowed_apps: [],
};

export default function AdminUsersPage() {
  const { user: me } = useAuth();
  const [users, setUsers] = useState([]);
  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const [u, a] = await Promise.all([api.get("/admin/users"), api.get("/admin/apps")]);
      setUsers(u.data);
      setApps(a.data);
    } catch (e) {
      toast.error(formatApiError(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const openCreate = () => {
    setForm(emptyForm);
    setDialogOpen(true);
  };
  const openEdit = (u) => {
    setForm({
      id: u.id,
      email: u.email,
      name: u.name,
      password: "",
      role: u.role,
      allowed_apps: u.allowed_apps || [],
    });
    setDialogOpen(true);
  };

  const toggleApp = (appId) => {
    setForm((f) => ({
      ...f,
      allowed_apps: f.allowed_apps.includes(appId)
        ? f.allowed_apps.filter((x) => x !== appId)
        : [...f.allowed_apps, appId],
    }));
  };

  const save = async () => {
    setSaving(true);
    try {
      if (form.id) {
        const payload = {
          name: form.name,
          role: form.role,
          allowed_apps: form.allowed_apps,
        };
        if (form.password) payload.password = form.password;
        await api.patch(`/admin/users/${form.id}`, payload);
        toast.success("Usuario actualizado");
      } else {
        await api.post("/admin/users", {
          email: form.email,
          name: form.name,
          password: form.password,
          role: form.role,
          allowed_apps: form.allowed_apps,
        });
        toast.success("Usuario creado");
      }
      setDialogOpen(false);
      load();
    } catch (e) {
      toast.error(formatApiError(e));
    } finally {
      setSaving(false);
    }
  };

  const confirmDelete = async () => {
    if (!deleting) return;
    try {
      await api.delete(`/admin/users/${deleting.id}`);
      toast.success("Usuario eliminado");
      setDeleting(null);
      load();
    } catch (e) {
      toast.error(formatApiError(e));
    }
  };

  return (
    <div className="space-y-8" data-testid="admin-users-page">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="eyebrow mb-2">Administración</div>
          <h1 className="font-display text-3xl sm:text-4xl font-bold tracking-tight">
            Usuarios y accesos
          </h1>
          <p className="text-muted-foreground mt-2 max-w-2xl">
            Crea usuarios, asigna roles y define a qué aplicaciones tienen acceso.
          </p>
        </div>
        <Button onClick={openCreate} data-testid="create-user-btn" className="h-10">
          <Plus size={16} weight="bold" className="mr-2" />
          Nuevo usuario
        </Button>
      </div>

      <div className="rounded-md border border-border bg-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm" data-testid="users-table">
            <thead className="bg-muted/50 text-xs uppercase tracking-[0.15em] text-muted-foreground">
              <tr>
                <th className="text-left px-4 py-3 font-medium">Nombre</th>
                <th className="text-left px-4 py-3 font-medium">Email</th>
                <th className="text-left px-4 py-3 font-medium">Rol</th>
                <th className="text-left px-4 py-3 font-medium">Aplicaciones</th>
                <th className="text-right px-4 py-3 font-medium">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                    Cargando…
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                    <UsersFour size={28} className="mx-auto mb-2" />
                    No hay usuarios registrados.
                  </td>
                </tr>
              ) : (
                users.map((u) => (
                  <tr key={u.id} className="hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3 font-medium">{u.name}</td>
                    <td className="px-4 py-3 text-muted-foreground">{u.email}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-block text-[10px] uppercase tracking-[0.2em] px-2 py-1 rounded-sm ${ROLE_TINT[u.role]}`}
                      >
                        {ROLE_LABEL[u.role]}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {u.role === "admin" ? (
                          <span className="text-xs text-muted-foreground italic">Todas</span>
                        ) : (u.allowed_apps || []).length === 0 ? (
                          <span className="text-xs text-muted-foreground italic">
                            Sin asignaciones
                          </span>
                        ) : (
                          (u.allowed_apps || []).map((aid) => {
                            const a = apps.find((x) => x.id === aid);
                            return (
                              <span
                                key={aid}
                                className="text-xs px-2 py-0.5 rounded-sm bg-muted text-foreground"
                              >
                                {a?.name || aid}
                              </span>
                            );
                          })
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-8"
                          onClick={() => openEdit(u)}
                          data-testid={`edit-user-btn-${u.id}`}
                        >
                          <PencilSimple size={14} weight="bold" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-8 text-destructive hover:text-destructive"
                          disabled={u.id === me?.id}
                          onClick={() => setDeleting(u)}
                          data-testid={`delete-user-btn-${u.id}`}
                        >
                          <Trash size={14} weight="bold" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create/Edit dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg" data-testid="user-dialog">
          <DialogHeader>
            <DialogTitle>{form.id ? "Editar usuario" : "Nuevo usuario"}</DialogTitle>
            <DialogDescription>
              {form.id
                ? "Modifica los datos del usuario y sus accesos a las aplicaciones."
                : "Completa la información para crear un nuevo usuario del portal."}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label className="text-xs uppercase tracking-[0.2em]">Nombre</Label>
              <Input
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                data-testid="user-name-input"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-xs uppercase tracking-[0.2em]">Email</Label>
              <Input
                type="email"
                value={form.email}
                disabled={!!form.id}
                onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                data-testid="user-email-input"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-xs uppercase tracking-[0.2em]">
                {form.id ? "Nueva contraseña (opcional)" : "Contraseña"}
              </Label>
              <Input
                type="password"
                value={form.password}
                onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                placeholder={form.id ? "Dejar en blanco para mantener" : "Mínimo 6 caracteres"}
                data-testid="user-password-input"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-xs uppercase tracking-[0.2em]">Rol</Label>
              <Select
                value={form.role}
                onValueChange={(v) => setForm((f) => ({ ...f, role: v }))}
              >
                <SelectTrigger data-testid="user-role-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">Administrador</SelectItem>
                  <SelectItem value="editor">Editor</SelectItem>
                  <SelectItem value="user">Usuario</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-3">
              <Label className="text-xs uppercase tracking-[0.2em]">
                Aplicaciones habilitadas
              </Label>
              <div className="grid grid-cols-1 gap-2 rounded-md border border-border p-3">
                {apps.map((a) => (
                  <label
                    key={a.id}
                    htmlFor={`app-${a.id}`}
                    className="flex items-center gap-3 cursor-pointer p-2 rounded-sm hover:bg-muted transition-colors"
                  >
                    <Checkbox
                      id={`app-${a.id}`}
                      checked={form.allowed_apps.includes(a.id)}
                      onCheckedChange={() => toggleApp(a.id)}
                      data-testid={`app-check-${a.id}`}
                    />
                    <div>
                      <div className="text-sm font-medium">{a.name}</div>
                      <div className="text-xs text-muted-foreground">{a.description}</div>
                    </div>
                  </label>
                ))}
              </div>
              {form.role === "admin" && (
                <p className="text-xs text-muted-foreground">
                  Los administradores tienen acceso a todas las aplicaciones automáticamente.
                </p>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)} data-testid="cancel-user-btn">
              Cancelar
            </Button>
            <Button onClick={save} disabled={saving} data-testid="save-user-btn">
              {saving ? "Guardando…" : "Guardar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete confirm */}
      <AlertDialog open={!!deleting} onOpenChange={(o) => !o && setDeleting(null)}>
        <AlertDialogContent data-testid="delete-user-dialog">
          <AlertDialogHeader>
            <AlertDialogTitle>¿Eliminar usuario?</AlertDialogTitle>
            <AlertDialogDescription>
              Se eliminará permanentemente la cuenta{" "}
              <strong>{deleting?.email}</strong>. Los registros creados por este usuario
              permanecerán en el sistema.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="cancel-delete-btn">Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              data-testid="confirm-delete-btn"
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
