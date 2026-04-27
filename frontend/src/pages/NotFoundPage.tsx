import { Link } from "react-router-dom";

function NotFoundPage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6 py-12">
      <div className="text-center space-y-4">
        <h1 className="text-6xl font-bold text-primary">404</h1>
        <p className="text-lg text-muted-foreground">Página não encontrada</p>
        <Link to="/" className="text-sm text-primary hover:underline">
          ← Voltar para início
        </Link>
      </div>
    </main>
  );
}

export default NotFoundPage;
