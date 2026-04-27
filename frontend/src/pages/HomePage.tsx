import { Link } from "react-router-dom";

function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6 py-12">
      <div className="max-w-2xl text-center space-y-6">
        <h1 className="text-5xl font-bold tracking-tight text-primary">Arminda</h1>
        <p className="text-xl text-muted-foreground">
          Folha de pagamento e gestão de pessoal para prefeituras.
        </p>
        <p className="text-sm text-muted-foreground">
          Sistema em construção · Bloco 0 — estrutura inicial
        </p>
        <div className="flex flex-wrap justify-center gap-3 pt-6">
          <Link
            to="/status"
            className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-6 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Status do sistema
          </Link>
          <a
            href="https://github.com/darlanvelozo/Arminda_Software"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex h-10 items-center justify-center rounded-md border border-input bg-background px-6 text-sm font-medium hover:bg-accent transition-colors"
          >
            Repositório
          </a>
        </div>
      </div>
    </main>
  );
}

export default HomePage;
