/**
 * PrevidenciaTab — config do regime próprio de previdência (RPPS) — Onda 2.4.
 *
 * Edita a config vigente do município: modo (flat/progressivo), alíquotas
 * do servidor e patronal, teto, regimes cobertos e vigência. No modo
 * progressivo, as faixas são informadas como JSON (validado no backend).
 *
 * Só financeiro/admin escrevem; leitura vê em modo somente-exibição (o
 * backend bloqueia o PATCH/POST com 403, surfaceado via toast).
 */

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { extractDomainErrorMessage } from "@/lib/api";
import {
  useCreateRegimePrevidenciario,
  useRegimesPrevidenciarios,
  useUpdateRegimePrevidenciario,
} from "@/lib/queries/previdencia";

const REGIMES = [
  { value: "estatutario", label: "Efetivo (concursado)" },
  { value: "celetista", label: "Celetista" },
  { value: "comissionado", label: "Comissionado" },
  { value: "temporario", label: "Contratado temporário" },
  { value: "eletivo", label: "Eletivo" },
  { value: "estagiario", label: "Estagiário" },
] as const;

const schema = z
  .object({
    nome: z.string().min(2, "Informe o nome do regime/instituto."),
    modo_contribuicao: z.enum(["flat", "progressivo"]),
    aliquota_servidor: z.string(),
    aliquota_patronal: z.string(),
    teto: z.string(),
    faixas_json: z.string(),
    regimes_aplicaveis: z.array(z.string()),
    vigencia_inicio: z.string().min(1, "Informe o início da vigência."),
    vigencia_fim: z.string(),
  })
  .superRefine((v, ctx) => {
    if (v.modo_contribuicao === "progressivo") {
      try {
        const parsed = JSON.parse(v.faixas_json || "[]");
        if (!Array.isArray(parsed) || parsed.length === 0) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            path: ["faixas_json"],
            message: "Modo progressivo exige ao menos uma faixa.",
          });
        }
      } catch {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["faixas_json"],
          message: "JSON de faixas inválido.",
        });
      }
    }
  });

type FormValues = z.infer<typeof schema>;

const FAIXAS_EXEMPLO = JSON.stringify(
  [
    { ate: "1500.00", aliquota: "0.075" },
    { ate: null, aliquota: "0.14" },
  ],
  null,
  2,
);

const EMPTY: FormValues = {
  nome: "",
  modo_contribuicao: "flat",
  aliquota_servidor: "0.14",
  aliquota_patronal: "0.22",
  teto: "",
  faixas_json: "[]",
  regimes_aplicaveis: ["estatutario"],
  vigencia_inicio: "",
  vigencia_fim: "",
};

export function PrevidenciaTab() {
  const { data, isLoading } = useRegimesPrevidenciarios();
  const existente = data?.results?.[0] ?? null;

  const createMutation = useCreateRegimePrevidenciario();
  const updateMutation = useUpdateRegimePrevidenciario();
  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: EMPTY });
  const modo = form.watch("modo_contribuicao");

  useEffect(() => {
    if (existente) {
      form.reset({
        nome: existente.nome,
        modo_contribuicao: existente.modo_contribuicao,
        aliquota_servidor: String(existente.aliquota_servidor ?? "0.14"),
        aliquota_patronal: String(existente.aliquota_patronal ?? "0.22"),
        teto: existente.teto != null ? String(existente.teto) : "",
        faixas_json: JSON.stringify(existente.faixas ?? [], null, 2),
        regimes_aplicaveis:
          (existente.regimes_aplicaveis as string[] | undefined) ?? ["estatutario"],
        vigencia_inicio: existente.vigencia_inicio,
        vigencia_fim: existente.vigencia_fim ?? "",
      });
    }
  }, [existente, form]);

  async function onSubmit(values: FormValues) {
    const payload = {
      nome: values.nome,
      orgao_emissor: existente?.orgao_emissor ?? null,
      modo_contribuicao: values.modo_contribuicao,
      aliquota_servidor: values.aliquota_servidor,
      aliquota_patronal: values.aliquota_patronal,
      teto: values.teto.trim() === "" ? null : values.teto,
      faixas:
        values.modo_contribuicao === "progressivo"
          ? (JSON.parse(values.faixas_json || "[]") as unknown[])
          : [],
      regimes_aplicaveis: values.regimes_aplicaveis,
      vigencia_inicio: values.vigencia_inicio,
      vigencia_fim: values.vigencia_fim.trim() === "" ? null : values.vigencia_fim,
      ativo: true,
    };
    try {
      if (existente) {
        await updateMutation.mutateAsync({ id: existente.id, payload });
        toast.success("Regime previdenciário atualizado.");
      } else {
        await createMutation.mutateAsync(payload);
        toast.success("Regime previdenciário criado.");
      }
    } catch (err) {
      toast.error(extractDomainErrorMessage(err) ?? "Falha ao salvar a config de RPPS.");
    }
  }

  function toggleRegime(value: string, checked: boolean) {
    const atual = form.getValues("regimes_aplicaveis");
    form.setValue(
      "regimes_aplicaveis",
      checked ? [...atual, value] : atual.filter((r) => r !== value),
    );
  }

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Carregando…</p>;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Previdência própria (RPPS)</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground mb-5">
          Configure o regime próprio do município. Estatutários cobertos contribuem ao RPPS
          (em vez do INSS). Sem RPPS configurado, todos caem no RGPS/INSS.
        </p>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5" noValidate>
            <FormField
              control={form.control}
              name="nome"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nome do regime / instituto</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Ex.: IPM - Instituto de Previdência Municipal"
                      disabled={isSubmitting}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="modo_contribuicao"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Modo de contribuição do servidor</FormLabel>
                  <Select
                    value={field.value}
                    onValueChange={field.onChange}
                    disabled={isSubmitting}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="flat">Alíquota única</SelectItem>
                      <SelectItem value="progressivo">Tabela progressiva (EC 103)</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            {modo === "flat" && (
              <FormField
                control={form.control}
                name="aliquota_servidor"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Alíquota do servidor</FormLabel>
                    <FormControl>
                      <Input placeholder="0.14" disabled={isSubmitting} {...field} />
                    </FormControl>
                    <p className="text-xs text-muted-foreground">
                      Fração — ex.: 0.14 = 14%.
                    </p>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}

            {modo === "progressivo" && (
              <FormField
                control={form.control}
                name="faixas_json"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Faixas progressivas (JSON)</FormLabel>
                    <FormControl>
                      <textarea
                        {...field}
                        rows={7}
                        placeholder={FAIXAS_EXEMPLO}
                        disabled={isSubmitting}
                        className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
                      />
                    </FormControl>
                    <p className="text-xs text-muted-foreground">
                      Lista de {`{ "ate": <valor> | null, "aliquota": <fração> }`}. A última
                      faixa precisa ter <code>ate: null</code> (sem teto).
                    </p>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}

            <FormField
              control={form.control}
              name="aliquota_patronal"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Alíquota patronal</FormLabel>
                  <FormControl>
                    <Input placeholder="0.22" disabled={isSubmitting} {...field} />
                  </FormControl>
                  <p className="text-xs text-muted-foreground">
                    Contribuição do ente — exposta às fórmulas como ALIQ_RPPS_PATRONAL.
                  </p>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="teto"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Teto da base (opcional)</FormLabel>
                  <FormControl>
                    <Input placeholder="Sem teto" disabled={isSubmitting} {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormItem>
              <FormLabel>Regimes cobertos pelo RPPS</FormLabel>
              <div className="grid grid-cols-2 gap-2 pt-1">
                {REGIMES.map((r) => {
                  const checked = form.watch("regimes_aplicaveis").includes(r.value);
                  return (
                    <label key={r.value} className="flex items-center gap-2 text-sm cursor-pointer">
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={(e) => toggleRegime(r.value, e.target.checked)}
                        disabled={isSubmitting}
                        className="h-4 w-4 rounded border-input text-primary focus:ring-2 focus:ring-ring"
                      />
                      {r.label}
                    </label>
                  );
                })}
              </div>
            </FormItem>

            <div className="grid grid-cols-2 gap-3">
              <FormField
                control={form.control}
                name="vigencia_inicio"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Início da vigência</FormLabel>
                    <FormControl>
                      <Input type="date" disabled={isSubmitting} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="vigencia_fim"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Fim (opcional)</FormLabel>
                    <FormControl>
                      <Input type="date" disabled={isSubmitting} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="flex justify-end">
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Salvando…" : existente ? "Salvar alterações" : "Criar config"}
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
