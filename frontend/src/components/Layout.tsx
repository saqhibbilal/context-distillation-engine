import { Outlet, Link, useLocation } from 'react-router-dom';

export function Layout() {
  const loc = useLocation();
  return (
    <div className="flex min-h-screen bg-[#0a0a0b]">
      <aside className="w-56 border-r border-zinc-800/80 bg-zinc-950/50 flex flex-col">
        <div className="p-5 border-b border-zinc-800/80">
          <Link to="/" className="font-quantico text-lg font-bold tracking-tight text-zinc-100">
            Context Distiller
          </Link>
        </div>
        <nav className="flex-1 p-3 space-y-0.5">
          <Link
            to="/"
            className={`block px-3 py-2 rounded text-sm font-medium transition-colors ${
              loc.pathname === '/' ? 'bg-zinc-800 text-white' : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
            }`}
          >
            Ingest
          </Link>
          <Link
            to="/dashboard"
            className={`block px-3 py-2 rounded text-sm font-medium transition-colors ${
              loc.pathname.startsWith('/dashboard') ? 'bg-zinc-800 text-white' : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
            }`}
          >
            Dashboard
          </Link>
        </nav>
      </aside>
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
