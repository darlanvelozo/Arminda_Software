/**
 * BulkEditDrawer (Onda 1.6b).
 *
 * Aplica updates em lote em N servidores selecionados na ServidoresListPage.
 * Foca nos campos pré-eSocial que costumam vir em branco do legado:
 * - Endereço (tipo_logradouro, cidade, UF, CEP)
 * - Estado civil, raça, nacionalidade, grau de instrução
 * - Ativo/inativo
 *
 * Para FKs (órgão emissor, sindicato), também aplica em massa nos vínculos
 * ativos dos servidores selecionados, em chamada separada.
 *
 * Princípio: campo deixado em branco = não atualiza. O operador só envia
 * o que mudou.
 */

import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { extractDomainErrorMessage } from "@/lib/api";
import {
  useBulkUpdateServidores,
  useBulkUpdateVinculos,
} from "@/lib/queries/servidores";
import {
  useOrgaosEmissoresList,
  useSindicatosList,
} from "@/lib/queries/orgaos-sindicatos";
import type { ServidorDetail } from "@/types";

interface BulkEditDrawerProps {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  servidores: { id: number; nome: string; matricula: string }[];
  /** Vínculos ativos dos servidores selecionados, para bulk em FK. */
  vinculosAtivosIds: number[];
  onSuccess: () => void;
}

type FormState = {
  tipo_logradouro: string;
  logradouro: string;
  numero: string;
  bairro: string;
  cidade: string;
  uf: string;
  cep: string;
  nacionalidade: string;
  raca: string;
  estado_civil: string;
  instrucao: string;
  ativo: string; // "" | "true" | "false"
  orgao_emissor_id: string;
  sindicato_id: string;
};

const ESTADO_VAZIO: FormState = {
  tipo_logradouro: "",
  logradouro: "",
  numero: "",
  bairro: "",
  cidade: "",
  uf: "",
  cep: "",
  nacionalidade: "",
  raca: "",
  estado_civil: "",
  instrucao: "",
  ativo: "",
  orgao_emissor_id: "",
  sindicato_id: "",
};

const TIPO_LOGRADOURO_OPCOES = [
  { value: "rua", label: "Rua" },
  { value: "avenida", label: "Avenida" },
  { value: "praca", label: "Praça" },
  { value: "travessa", label: "Travessa" },
  { value: "rodovia", label: "Rodovia" },
  { value: "estrada", label: "Estrada" },
  { value: "viela", label: "Viela" },
  { value: "alameda", label: "Alameda" },
  { value: "largo", label: "Largo" },
  { value: "outro", label: "Outro" },
] as const;

const ESTADO_CIVIL_OPCOES = [
  { value: "solteiro", label: "Solteiro(a)" },
  { value: "casado", label: "Casado(a)" },
  { value: "divorciado", label: "Divorciado(a)" },
  { value: "viuvo", label: "Viúvo(a)" },
  { value: "uniao_estavel", label: "União estável" },
] as const;

const RACA_OPCOES = [
  { value: "1", label: "Branca" },
  { value: "2", label: "Preta" },
  { value: "3", label: "Parda" },
  { value: "4", label: "Amarela" },
  { value: "5", label: "Indígena" },
  { value: "6", label: "Não informada" },
] as const;

const INSTRUCAO_OPCOES = [
  { value: "01", label: "Analfabeto" },
  { value: "02", label: "Até 4ª série" },
  { value: "03", label: "Fundamental incompleto" },
  { value: "04", label: "Fundamental completo" },
  { value: "05", label: "Médio incompleto" },
  { value: "06", label: "Médio completo" },
  { value: "07", label: "Superior incompleto" },
  { value: "08", label: "Superior completo" },
  { value: "09", label: "Pós-graduação" },
  { value: "10", label: "Mestrado" },
  { value: "11", label: "Doutorado" },
] as const;

const SENTINEL_VAZIO = "__VAZIO__";

export function BulkEditDrawer({
  open,
  onOpenChange,
  servidores,
  vinculosAtivosIds,
  onSuccess,
}: BulkEditDrawerProps) {
  const [form, setForm] = useState<FormState>(ESTADO_VAZIO);
  const [submitting, setSubmitting] = useState(false);

  const bulkServidores = useBulkUpdateServidores();
  const bulkVinculos = useBulkUpdateVinculos();
  const orgaos = useOrgaosEmissoresList();
  const sindicatos = useSindicatosList();

  useEffect(() => {
    if (!open) setForm(ESTADO_VAZIO);
  }, [open]);

  const updates = useMemo(() => {
    const u: Record<string, unknown> = {};
    if (form.tipo_logradouro) u.tipo_logradouro = form.tipo_logradouro;
    if (form.logradouro) u.logradouro = form.logradouro.trim();
    if (form.numero) u.numero = form.numero.trim();
    if (form.bairro) u.bairro = form.bairro.trim();
    if (form.cidade) u.cidade = form.cidade.trim();
    if (form.uf) u.uf = form.uf.trim().toUpperCase();
    if (form.cep) u.cep = form.cep.trim();
    if (form.nacionalidade) u.nacionalidade = form.nacionalidade.trim();
    if (form.raca) u.raca = form.raca;
    if (form.estado_civil) u.estado_civil = form.estado_civil;
    if (form.instrucao) u.instrucao = form.instrucao;
    if (form.ativo === "true") u.ativo = true;
    if (form.ativo === "false") u.ativo = false;
    return u;
  }, [form]);

  const updatesVinculo = useMemo(() => {
    const u: Record<string, unknown> = {};
    if (form.orgao_emissor_id) u.orgao_emissor = Number(form.orgao_emissor_id);
    if (form.sindicato_id) u.sindicato = Number(form.sindicato_id);
    return u;
  }, [form.orgao_emissor_id, form.sindicato_id]);

  const totalAlteracoes =
    Object.keys(updates).length + Object.keys(updatesVinculo).length;

  async function aplicar() {
    if (totalAlteracoes === 0) {
      toast.info("Nenhum campo preenchido para aplicar.");
      return;
    }
    setSubmitting(true);
    try {
      let atualizadosServidores = 0;
      let atualizadosVinculos = 0;
      if (Object.keys(updates).length > 0) {
        const r = await bulkServidores.mutateAsync({
          servidor_ids: servidores.map((s) => s.id),
          updates,
        });
        atualizadosServidores = r.atualizados;
      }
      if (Object.keys(updatesVinculo).length > 0 && vinculosAtivosIds.length > 0) {
        const r = await bulkVinculos.mutateAsync({
          vinculo_ids: vinculosAtivosIds,
          updates: updatesVinculo,
        });
        atualizadosVinculos = r.atualizados;
      }
      toast.success(
        `Atualizados ${atualizadosServidores} servidor(es)` +
          (atualizadosVinculos > 0 ? ` e ${atualizadosVinculos} vínculo(s)` : "") +
          ".",
      );
      onSuccess();
      onOpenChange(false);
    } catch (err) {
      toast.error(extractDomainErrorMessage(err) ?? "Falha no bulk-update.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="overflow-y-auto sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>Editar em lote ({servidores.length})</SheetTitle>
          <SheetDescription>
            Campos deixados em branco não são alterados. Aplica somente o que
            você preencher abaixo.
          </SheetDescription>
        </SheetHeader>

        <div className="space-y-6 py-4">
          <section className="space-y-3">
            <h3 className="text-sm font-medium">Endereço</h3>
            <div className="grid grid-cols-2 gap-3">
              <FieldSelect
                label="Tipo de logradouro"
                value={form.tipo_logradouro}
                onChange={(v) => setForm({ ...form, tipo_logradouro: v })}
                options={TIPO_LOGRADOURO_OPCOES}
              />
              <Field
                label="CEP"
                value={form.cep}
                onChange={(v) => setForm({ ...form, cep: v })}
                placeholder="49000-000"
              />
              <Field
                label="Cidade"
                value={form.cidade}
                onChange={(v) => setForm({ ...form, cidade: v })}
              />
              <Field
                label="UF"
                value={form.uf}
                onChange={(v) => setForm({ ...form, uf: v.toUpperCase() })}
                maxLength={2}
              />
              <Field
                label="Bairro"
                value={form.bairro}
                onChange={(v) => setForm({ ...form, bairro: v })}
                className="col-span-2"
              />
            </div>
          </section>

          <section className="space-y-3">
            <h3 className="text-sm font-medium">Identidade civil (eSocial)</h3>
            <div className="grid grid-cols-2 gap-3">
              <FieldSelect
                label="Estado civil"
                value={form.estado_civil}
                onChange={(v) => setForm({ ...form, estado_civil: v })}
                options={ESTADO_CIVIL_OPCOES}
              />
              <FieldSelect
                label="Raça/cor"
                value={form.raca}
                onChange={(v) => setForm({ ...form, raca: v })}
                options={RACA_OPCOES}
              />
              <FieldSelect
                label="Grau de instrução"
                value={form.instrucao}
                onChange={(v) => setForm({ ...form, instrucao: v })}
                options={INSTRUCAO_OPCOES}
                className="col-span-2"
              />
              <Field
                label="Nacionalidade"
                value={form.nacionalidade}
                onChange={(v) => setForm({ ...form, nacionalidade: v })}
                placeholder="Ex.: 10 = Brasileira"
                className="col-span-2"
              />
            </div>
          </section>

          <section className="space-y-3">
            <h3 className="text-sm font-medium">Vínculos ativos ({vinculosAtivosIds.length})</h3>
            {vinculosAtivosIds.length === 0 ? (
              <p className="text-xs text-muted-foreground">
                Nenhum servidor selecionado tem vínculo ativo — não é possível
                aplicar órgão emissor ou sindicato.
              </p>
            ) : (
              <div className="grid grid-cols-1 gap-3">
                <div>
                  <Label>Órgão emissor (CNPJ)</Label>
                  <Select
                    value={form.orgao_emissor_id || SENTINEL_VAZIO}
                    onValueChange={(v) =>
                      setForm({ ...form, orgao_emissor_id: v === SENTINEL_VAZIO ? "" : v })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Não alterar" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value={SENTINEL_VAZIO}>Não alterar</SelectItem>
                      {orgaos.data?.results.map((o) => (
                        <SelectItem key={o.id} value={String(o.id)}>
                          {o.sigla || o.nome} · {o.cnpj}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Sindicato</Label>
                  <Select
                    value={form.sindicato_id || SENTINEL_VAZIO}
                    onValueChange={(v) =>
                      setForm({ ...form, sindicato_id: v === SENTINEL_VAZIO ? "" : v })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Não alterar" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value={SENTINEL_VAZIO}>Não alterar</SelectItem>
                      {sindicatos.data?.results.map((s) => (
                        <SelectItem key={s.id} value={String(s.id)}>
                          {s.nome}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            )}
          </section>

          <section className="space-y-2 border-t pt-4">
            <Label>Status</Label>
            <Select
              value={form.ativo || SENTINEL_VAZIO}
              onValueChange={(v) =>
                setForm({ ...form, ativo: v === SENTINEL_VAZIO ? "" : v })
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Não alterar" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={SENTINEL_VAZIO}>Não alterar</SelectItem>
                <SelectItem value="true">Ativo</SelectItem>
                <SelectItem value="false">Inativo</SelectItem>
              </SelectContent>
            </Select>
          </section>
        </div>

        <SheetFooter className="flex-col gap-2 sm:flex-row sm:justify-end">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={submitting}
          >
            Cancelar
          </Button>
          <Button onClick={aplicar} disabled={submitting || totalAlteracoes === 0}>
            {submitting ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <CheckCircle2 className="h-4 w-4 mr-2" />
            )}
            Aplicar em {servidores.length} servidor(es)
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}

function Field(props: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  maxLength?: number;
  className?: string;
}) {
  return (
    <div className={props.className}>
      <Label className="text-xs">{props.label}</Label>
      <Input
        value={props.value}
        onChange={(e) => props.onChange(e.target.value)}
        placeholder={props.placeholder}
        maxLength={props.maxLength}
      />
    </div>
  );
}

function FieldSelect(props: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: ReadonlyArray<{ value: string; label: string }>;
  className?: string;
}) {
  return (
    <div className={props.className}>
      <Label className="text-xs">{props.label}</Label>
      <Select
        value={props.value || SENTINEL_VAZIO}
        onValueChange={(v) => props.onChange(v === SENTINEL_VAZIO ? "" : v)}
      >
        <SelectTrigger>
          <SelectValue placeholder="Não alterar" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={SENTINEL_VAZIO}>Não alterar</SelectItem>
          {props.options.map((o) => (
            <SelectItem key={o.value} value={o.value}>
              {o.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

export type { ServidorDetail };
