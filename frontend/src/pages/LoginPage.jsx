import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { useNavigate } from "react-router-dom";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { ShieldCheck, ArrowRight, Buildings } from "@phosphor-icons/react";

export default function LoginPage() {
  const { login, error } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const ok = await login(email, password);
    setLoading(false);
    if (ok) navigate("/portal", { replace: true });
  };

  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-5 bg-background">
      {/* Left visual pane */}
      <div className="hidden lg:flex lg:col-span-3 relative overflow-hidden bg-[hsl(222,47%,9%)]">
        <div className="absolute inset-0 bg-grid opacity-20" />
        <div
          className="absolute inset-0 bg-cover bg-center opacity-30"
          style={{
            backgroundImage:
              "url(https://images.unsplash.com/photo-1462556791646-c201b8241a94?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA3MDB8MHwxfHNlYXJjaHwzfHxhYnN0cmFjdCUyMG1vZGVybiUyMGFyY2hpdGVjdHVyZSUyMGdsYXNzfGVufDB8fHx8MTc4ODE3Nzc0M3ww&ixlib=rb-4.1.0&q=85)",
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-tr from-[hsl(222,47%,7%)] via-transparent to-transparent" />
        <div className="relative z-10 flex flex-col justify-between p-14 text-white w-full">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-md bg-[hsl(217,91%,60%)] grid place-items-center">
              <Buildings size={22} weight="bold" />
            </div>
            <span className="font-display text-lg font-semibold tracking-tight">
              Portal Corporativo
            </span>
          </div>

          <div className="max-w-xl space-y-6">
            <div className="eyebrow text-white/60">Suite Interna · Acceso Seguro</div>
            <h1 className="font-display text-5xl font-bold leading-[1.05] tracking-tight">
              Un solo acceso.<br />
              <span className="text-white/70">Todas tus aplicaciones.</span>
            </h1>
            <p className="text-white/70 text-base max-w-md leading-relaxed">
              Ingresa con tus credenciales corporativas para acceder a los formularios
              y paneles que tu rol tenga habilitados.
            </p>
            <div className="flex items-center gap-2 pt-6 text-xs uppercase tracking-[0.2em] text-white/50">
              <ShieldCheck size={16} weight="bold" />
              Autenticación cifrada · JWT
            </div>
          </div>

          <div className="text-xs text-white/40 uppercase tracking-[0.2em]">
            v1.0 · Uso interno autorizado
          </div>
        </div>
      </div>

      {/* Right form pane */}
      <div className="col-span-1 lg:col-span-2 flex items-center justify-center p-8 sm:p-14">
        <div className="w-full max-w-md">
          <div className="flex items-center gap-2 lg:hidden mb-8">
            <div className="h-9 w-9 rounded-md bg-primary grid place-items-center text-primary-foreground">
              <Buildings size={20} weight="bold" />
            </div>
            <span className="font-display text-base font-semibold">Portal Corporativo</span>
          </div>

          <div className="eyebrow mb-3">Inicio de Sesión</div>
          <h2 className="font-display text-3xl sm:text-4xl font-bold tracking-tight mb-2">
            Bienvenido de vuelta
          </h2>
          <p className="text-muted-foreground text-sm mb-10">
            Accede al portal con tu correo corporativo.
          </p>

          <form onSubmit={submit} className="space-y-5" data-testid="login-form">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-xs uppercase tracking-[0.2em]">
                Correo Electrónico
              </Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="tu.nombre@empresa.com"
                data-testid="login-email-input"
                className="h-11"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="text-xs uppercase tracking-[0.2em]">
                Contraseña
              </Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                data-testid="login-password-input"
                className="h-11"
              />
            </div>

            {error && (
              <div
                className="text-sm text-destructive border border-destructive/30 bg-destructive/5 rounded-md px-3 py-2"
                data-testid="login-error"
              >
                {error}
              </div>
            )}

            <Button
              type="submit"
              disabled={loading}
              data-testid="login-submit-btn"
              className="w-full h-11 group transition-colors"
            >
              {loading ? "Ingresando…" : "Ingresar al portal"}
              <ArrowRight
                className="ml-2 transition-transform group-hover:translate-x-0.5"
                size={16}
                weight="bold"
              />
            </Button>
          </form>

          <div className="mt-10 rounded-md border border-border bg-muted/40 p-4 text-xs text-muted-foreground leading-relaxed">
            <div className="eyebrow mb-2">Cuentas de Prueba</div>
            <div className="grid grid-cols-1 gap-1 font-mono">
              <div>admin@portal.com · admin123</div>
              <div>editor@portal.com · editor123</div>
              <div>user@portal.com · user123</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
