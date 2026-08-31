import React from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import {
  Buildings,
  SquaresFour,
  UsersFour,
  SignOut,
  User as UserIcon,
  CaretDown,
} from "@phosphor-icons/react";

const ROLE_LABEL = { admin: "Administrador", editor: "Editor", user: "Usuario" };

export default function PortalLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const doLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  const navItem =
    "flex items-center gap-3 px-3 py-2 rounded-md text-sm text-muted-foreground hover:text-foreground hover:bg-muted transition-colors";
  const activeItem = "bg-muted text-foreground";

  return (
    <div className="min-h-screen bg-background grid grid-cols-1 lg:grid-cols-[260px_1fr]">
      {/* Sidebar */}
      <aside className="hidden lg:flex flex-col border-r border-border bg-muted/40">
        <div className="h-16 flex items-center gap-2 px-5 border-b border-border">
          <div className="h-8 w-8 rounded-md bg-primary grid place-items-center text-primary-foreground">
            <Buildings size={18} weight="bold" />
          </div>
          <div className="font-display font-semibold tracking-tight">Portal</div>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          <div className="eyebrow px-3 pt-4 pb-2">Navegación</div>
          <NavLink
            to="/portal"
            end
            data-testid="nav-portal"
            className={({ isActive }) => `${navItem} ${isActive ? activeItem : ""}`}
          >
            <SquaresFour size={18} weight="regular" />
            Mis aplicaciones
          </NavLink>

          {user?.role === "admin" && (
            <>
              <div className="eyebrow px-3 pt-6 pb-2">Administración</div>
              <NavLink
                to="/admin/usuarios"
                data-testid="nav-admin-users"
                className={({ isActive }) => `${navItem} ${isActive ? activeItem : ""}`}
              >
                <UsersFour size={18} weight="regular" />
                Usuarios y accesos
              </NavLink>
            </>
          )}
        </nav>

        <div className="p-4 text-xs text-muted-foreground border-t border-border">
          <div className="eyebrow mb-1">Sesión</div>
          <div className="truncate">{user?.email}</div>
        </div>
      </aside>

      {/* Main */}
      <div className="flex flex-col min-h-screen">
        {/* Top bar */}
        <header className="h-16 border-b border-border bg-background/80 backdrop-blur-xl sticky top-0 z-30 flex items-center justify-between px-6">
          <div className="lg:hidden flex items-center gap-2">
            <div className="h-8 w-8 rounded-md bg-primary grid place-items-center text-primary-foreground">
              <Buildings size={18} weight="bold" />
            </div>
            <span className="font-display font-semibold">Portal</span>
          </div>

          <div className="hidden lg:block">
            <div className="eyebrow">Espacio de Trabajo</div>
            <div className="font-display text-sm font-semibold tracking-tight">
              Portal Corporativo Interno
            </div>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                className="gap-2 h-10 rounded-md"
                data-testid="user-menu-trigger"
              >
                <div className="h-6 w-6 rounded-sm bg-primary/10 text-primary grid place-items-center">
                  <UserIcon size={14} weight="bold" />
                </div>
                <span className="hidden sm:inline text-sm">{user?.name || user?.email}</span>
                <CaretDown size={12} weight="bold" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-64">
              <DropdownMenuLabel>
                <div className="text-sm font-semibold truncate">{user?.name}</div>
                <div className="text-xs text-muted-foreground truncate">{user?.email}</div>
                <div className="mt-1 inline-block text-[10px] uppercase tracking-[0.2em] px-2 py-0.5 rounded-sm bg-primary/10 text-primary">
                  {ROLE_LABEL[user?.role] || user?.role}
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={doLogout}
                data-testid="logout-btn"
                className="cursor-pointer"
              >
                <SignOut size={16} weight="bold" className="mr-2" />
                Cerrar sesión
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </header>

        <main className="flex-1 p-6 lg:p-10 max-w-[1400px] w-full">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
