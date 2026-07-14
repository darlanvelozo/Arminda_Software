/**
 * EsocialPage — Onda 4.1.
 *
 * Geração e listagem de eventos do eSocial por órgão emissor. Onda 4.1 cobre
 * S-1000 e S-1005 (camada de geração de XML + validação XSD; assinatura e
 * transmissão vêm depois — ADR-0020).
 */

import { FileCode2, ShieldCheck, ShieldAlert } from "lucide-react";
import { useRef, useState } from "react";
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
import { Input } from "@/components/ui/input";
import { extractDomainErrorMessage } from "@/lib/api";
import {
  baixarEventoXml,
  useAssinarEvento,
  useCertificados,
  useEventosEsocial,
  useGerarEvento,
  useGerarEventosFolha,
  useUploadCertificado,
  type GerarEventoInput,
} from "@/lib/queries/esocial";
import { useFolhasList } from "@/lib/queries/folhas";
import { useOrgaosEmissoresList } from "@/lib/queries/orgaos-sindicatos";
import { useRubricasList } from "@/lib/queries/rubricas";

const TIPOS = [
  { value: "S-1000", label: "S-1000 — Informações do empregador" },
  { value: "S-1005", label: "S-1005 — Tabela de estabelecimentos" },
  { value: "S-1010", label: "S-1010 — Tabela de rubricas" },
] as const;

const STATUS_VARIANT: Record<
  string,
  "default" | "secondary" | "destructive" | "outline" | "success"
> = {
  gerado: "secondary",
  validado: "default",
  assinado: "success",
  rejeitado: "destructive",
};

export default function EsocialPage() {
  const { data: eventos, isLoading } = useEventosEsocial();
  const { data: orgaos } = useOrgaosEmissoresList();
  const { data: rubricas } = useRubricasList({ ativo: true, ordering: "codigo" });
  const { data: certificados } = useCertificados();
  const gerar = useGerarEvento();
  const gerarFolha = useGerarEventosFolha();
  const { data: folhas } = useFolhasList({});
  const [folhaSel, setFolhaSel] = useState("");
  const [incluirPgto, setIncluirPgto] = useState(true);
  const assinar = useAssinarEvento();

  async function onGerarFolha() {
    if (!orgao) return toast.error("Selecione o órgão emissor.");
    if (!folhaSel) return toast.error("Selecione a folha.");
    try {
      const r = await gerarFolha.mutateAsync({
        orgao_emissor: Number(orgao),
        folha: Number(folhaSel),
        incluir_pagamentos: incluirPgto,
      });
      if (r.erros.length === 0) {
        toast.success(`${r.gerados} evento(s) de remuneração gerados e validados.`);
      } else {
        toast.warning(`${r.gerados} gerados; ${r.erros.length} vínculo(s) com erro — veja o primeiro: ${r.erros[0].servidor}: ${r.erros[0].erro}`);
      }
    } catch (e) {
      toast.error(extractDomainErrorMessage(e) ?? "Falha ao gerar os eventos da folha.");
    }
  }
  const uploadCert = useUploadCertificado();
  const fileRef = useRef<HTMLInputElement>(null);

  const [orgao, setOrgao] = useState("");
  const [tipo, setTipo] = useState<GerarEventoInput["tipo"]>("S-1000");
  const [rubrica, setRubrica] = useState("");
  const [senhaCert, setSenhaCert] = useState("");

  const certDoOrgao = orgao
    ? (certificados?.results ?? []).find((c) => String(c.orgao_emissor) === orgao)
    : undefined;

  async function onUploadCert() {
    const file = fileRef.current?.files?.[0];
    if (!orgao) return toast.error("Selecione o órgão emissor primeiro.");
    if (!file) return toast.error("Escolha o arquivo .pfx do certificado.");
    if (!senhaCert) return toast.error("Informe a senha do certificado.");
    try {
      await uploadCert.mutateAsync({ orgao_emissor: Number(orgao), arquivo: file, senha: senhaCert });
      toast.success("Certificado guardado no cofre (cifrado).");
      setSenhaCert("");
      if (fileRef.current) fileRef.current.value = "";
    } catch (e) {
      toast.error(extractDomainErrorMessage(e) ?? "Falha ao guardar o certificado.");
    }
  }

  async function onAssinar(id: number) {
    try {
      await assinar.mutateAsync(id);
      toast.success("Evento assinado digitalmente.");
    } catch (e) {
      toast.error(extractDomainErrorMessage(e) ?? "Falha ao assinar (há certificado no cofre?).");
    }
  }

  async function onGerar() {
    if (!orgao) {
      toast.error("Selecione o órgão emissor.");
      return;
    }
    if (tipo === "S-1010" && !rubrica) {
      toast.error("Selecione a rubrica para o S-1010.");
      return;
    }
    try {
      await gerar.mutateAsync({
        tipo,
        orgao_emissor: Number(orgao),
        ...(tipo === "S-1010" ? { rubrica: Number(rubrica) } : {}),
      });
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
        {tipo === "S-1010" && (
          <div className="flex-1 min-w-[240px]">
            <label className="text-xs text-muted-foreground">Rubrica</label>
            <Select value={rubrica} onValueChange={setRubrica} disabled={gerar.isPending}>
              <SelectTrigger>
                <SelectValue placeholder="Selecione…" />
              </SelectTrigger>
              <SelectContent>
                {(rubricas?.results ?? []).map((r) => (
                  <SelectItem key={r.id} value={String(r.id)}>
                    {r.codigo} · {r.nome}
                    {r.natureza_esocial ? ` (nat. ${r.natureza_esocial})` : " — sem natureza"}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
        <Button onClick={onGerar} disabled={gerar.isPending}>
          {gerar.isPending ? "Gerando…" : "Gerar evento"}
        </Button>
      </div>
      {tipo === "S-1010" && (
        <p className="text-xs text-muted-foreground">
          O S-1010 exige a <strong>natureza eSocial (Tabela 3)</strong> na rubrica.
          Rubricas sem natureza aparecem marcadas — preencha-as em{" "}
          <strong>Rubricas</strong> antes de gerar.
        </p>
      )}

      {orgao && (
        <div className="rounded-md border bg-card p-3">
          {certDoOrgao ? (
            <div className="flex items-center gap-2 text-sm">
              <ShieldCheck className="h-4 w-4 text-emerald-600" />
              <span>
                Certificado no cofre: <strong>{certDoOrgao.titular}</strong> · vence em{" "}
                {certDoOrgao.validade_fim
                  ? new Date(certDoOrgao.validade_fim).toLocaleDateString("pt-BR")
                  : "—"}
                {typeof certDoOrgao.dias_para_vencer === "number" &&
                  ` (${certDoOrgao.dias_para_vencer} dias)`}
              </span>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <ShieldAlert className="h-4 w-4 text-amber-600" />
                Sem certificado no cofre para este órgão — necessário para assinar.
              </div>
              <div className="flex flex-wrap items-end gap-3">
                <div>
                  <label className="text-xs text-muted-foreground">Certificado (.pfx)</label>
                  <Input ref={fileRef} type="file" accept=".pfx,.p12" className="text-xs" />
                </div>
                <div className="w-40">
                  <label className="text-xs text-muted-foreground">Senha</label>
                  <Input
                    type="password"
                    value={senhaCert}
                    onChange={(e) => setSenhaCert(e.target.value)}
                    disabled={uploadCert.isPending}
                  />
                </div>
                <Button variant="outline" onClick={onUploadCert} disabled={uploadCert.isPending}>
                  {uploadCert.isPending ? "Guardando…" : "Guardar no cofre"}
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {orgao && (
        <div className="rounded-md border bg-card p-3 space-y-2">
          <p className="text-sm font-medium">Remuneração da folha (S-1200/S-1202)</p>
          <p className="text-xs text-muted-foreground">
            Gera, para cada servidor da folha, o evento de remuneração correto pelo
            regime (estatutário → S-1202/RPPS; demais → S-1200) — todos validados no
            XSD oficial. Opcionalmente gera também os pagamentos (S-1210).
          </p>
          <div className="flex flex-wrap items-end gap-3">
            <div className="flex-1 min-w-[220px]">
              <label className="text-xs text-muted-foreground">Folha calculada</label>
              <Select value={folhaSel} onValueChange={setFolhaSel} disabled={gerarFolha.isPending}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecione…" />
                </SelectTrigger>
                <SelectContent>
                  {(folhas?.results ?? [])
                    .filter((f) => f.status !== "aberta")
                    .map((f) => (
                      <SelectItem key={f.id} value={String(f.id)}>
                        {f.tipo_display} · {f.competencia.slice(0, 7)} ({f.status_display})
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
            <label className="flex items-center gap-2 text-sm cursor-pointer pb-2">
              <input
                type="checkbox"
                checked={incluirPgto}
                onChange={(e) => setIncluirPgto(e.target.checked)}
                className="h-4 w-4 rounded border-input"
              />
              Incluir pagamentos (S-1210)
            </label>
            <Button onClick={onGerarFolha} disabled={gerarFolha.isPending}>
              {gerarFolha.isPending ? "Gerando…" : "Gerar eventos da folha"}
            </Button>
          </div>
        </div>
      )}

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
                  {e.status !== "assinado" && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7"
                      onClick={() => e.id && onAssinar(e.id)}
                      disabled={assinar.isPending}
                    >
                      Assinar
                    </Button>
                  )}
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
