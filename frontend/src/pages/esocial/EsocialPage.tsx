/**
 * EsocialPage — Onda 4.1.
 *
 * Geração e listagem de eventos do eSocial por órgão emissor. Onda 4.1 cobre
 * S-1000 e S-1005 (camada de geração de XML + validação XSD; assinatura e
 * transmissão vêm depois — ADR-0020).
 */

import { FileCode2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { extractDomainErrorMessage } from "@/lib/api";
import {
  baixarEventoXml,
  useEventosEsocial,
  useGerarEvento,
  type GerarEventoInput,
} from "@/lib/queries/esocial";
import { useOrgaosEmissoresList } from "@/lib/queries/orgaos-sindicatos";

const TIPOS = [
  { value: "S-1000", label: "S-1000 — Informações do empregador" },
  { value: "S-1005", label: "S-1005 — Tabela de estabelecimentos" },
] as const;

const STATUS_VARIANT: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  gerado: "secondary",
  validado: "default",
  rejeitado: "destructive",
};

export default function EsocialPage() {
  const { data: eventos, isLoading } = useEventosEsocial();
  const { data: orgaos } = useOrgaosEmissoresList();
  const gerar = useGerarEvento();

  const [orgao, setOrgao] = useState("");
  const [tipo, setTipo] = useState<GerarEventoInput["tipo"]>("S-1000");

  async function onGerar() {
    if (!orgao) {
      toast.error("Selecione o órgão emissor.");
      return;
    }
    try {
      await gerar.mutateAsync({ tipo, orgao_emissor: Number(orgao) });
      toast.success("Evento gerado e validado contra o XSD.");
    } catch (e) {
      toast.error(extractDomainErrorMessage(e) ?? "Falha ao gerar o evento.");
    }
  }

  return (
    <div className="space-y-4">
      <header>
        <h1 className="font-semibold inline-flex items-center gap-2" style={{ fontSize: 22 }}>
          <FileCode2 className="h-5 w-5 text-muted-foreground" />
          eSocial
        </h1>
        <p className="text-sm text-muted-foreground">
          Geração dos eventos do eSocial por órgão emissor (S-1.3). Cada evento é
          validado contra o XSD oficial. Assinatura e transmissão entram em ondas
          seguintes.
        </p>
      </header>

      <div className="rounded-md border bg-card p-3 flex flex-wrap items-end gap-3">
        <div className="flex-1 min-w-[240px]">
          <label className="text-xs text-muted-foreground">Órgão emissor</label>
          <Select value={orgao} onValueChange={setOrgao} disabled={gerar.isPending}>
            <SelectTrigger>
              <SelectValue placeholder="Selecione…" />
            </SelectTrigger>
            <SelectContent>
              {(orgaos?.results ?? []).map((o) => (
                <SelectItem key={o.id} value={String(o.id)}>
                  {o.nome} · {o.cnpj}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex-1 min-w-[240px]">
          <label className="text-xs text-muted-foreground">Evento</label>
          <Select
            value={tipo}
            onValueChange={(v) => setTipo(v as GerarEventoInput["tipo"])}
            disabled={gerar.isPending}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {TIPOS.map((t) => (
                <SelectItem key={t.value} value={t.value}>
                  {t.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Button onClick={onGerar} disabled={gerar.isPending}>
          {gerar.isPending ? "Gerando…" : "Gerar evento"}
        </Button>
      </div>

      <div className="rounded-md border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Evento</TableHead>
              <TableHead>Órgão</TableHead>
              <TableHead>ID do evento</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Ação</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-6 text-muted-foreground">
                  Carregando…
                </TableCell>
              </TableRow>
            )}
            {!isLoading && (eventos?.results.length ?? 0) === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                  Nenhum evento gerado ainda. Selecione um órgão e gere acima.
                </TableCell>
              </TableRow>
            )}
            {eventos?.results.map((e) => (
              <TableRow key={e.id}>
                <TableCell className="text-sm">{e.tipo_display}</TableCell>
                <TableCell className="text-sm">
                  <div className="flex flex-col">
                    <span>{e.orgao_nome}</span>
                    <span className="text-xs text-muted-foreground font-mono">
                      {e.orgao_cnpj}
                    </span>
                  </div>
                </TableCell>
                <TableCell className="font-mono text-xs">{e.id_evento}</TableCell>
                <TableCell>
                  <Badge variant={STATUS_VARIANT[e.status] ?? "outline"}>
                    {e.status_display}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7"
                    onClick={() => e.id && baixarEventoXml(e.id, e.id_evento)}
                  >
                    Baixar XML
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
