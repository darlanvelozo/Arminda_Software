/**
 * LotacaoFormSheet — Bloco 1.3b.
 *
 * Sheet com formulário de criação/edição de Lotação.
 * O dropdown de Lotação Pai mostra a primeira página de lotações ativas
 * (ordenadas por nome). Para municípios com >20 lotações, refinar com busca.
 */

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
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
  useCreateLotacao,
  useLotacoesList,
  useUpdateLotacao,
} from "@/lib/queries/lotacoes";
import type { LotacaoDetail } from "@/types";

const NONE_VALUE = "__none__";

const lotacaoSchema = z.object({
  codigo: z
    .string()
    .min(1, "Código é obrigatório.")
    .max(20, "Código deve ter no máximo 20 caracteres."),
  nome: z
    .string()
    .min(2, "Nome muito curto.")
    .max(200, "Nome deve ter no máximo 200 caracteres."),
  sigla: z.string().max(20, "Sigla deve ter no máximo 20 caracteres."),
  lotacao_pai: z.number().int().nullable(),
  ativo: z.boolean(),
});

type LotacaoFormValues = z.infer<typeof lotacaoSchema>;

interface LotacaoFormSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  lotacao: LotacaoDetail | null;
}

export function LotacaoFormSheet({ open, onOpenChange, lotacao }: LotacaoFormSheetProps) {
  const isEdit = lotacao !== null;

  const form = useForm<LotacaoFormValues>({
    resolver: zodResolver(lotacaoSchema),
    defaultValues: {
      codigo: "",
      nome: "",
      sigla: "",
      lotacao_pai: null,
      ativo: true,
    },
  });

  // Carrega possíveis pais (apenas ativos). Não pode ser pai de si mesma.
  const paiQuery = useLotacoesList({ ativo: true, ordering: "nome" });
  const possiveisPais =
    paiQuery.data?.results.filter((l) => !isEdit || l.id !== lotacao?.id) ?? [];

  useEffect(() => {
    if (open && lotacao) {
      form.reset({
        codigo: lotacao.codigo,
        nome: lotacao.nome,
        sigla: lotacao.sigla || "",
        lotacao_pai: lotacao.lotacao_pai ?? null,
        ativo: lotacao.ativo,
      });
    } else if (open && !lotacao) {
      form.reset({
        codigo: "",
        nome: "",
        sigla: "",
        lotacao_pai: null,
        ativo: true,
      });
    }
  }, [open, lotacao, form]);

  const createMutation = useCreateLotacao();
  const updateMutation = useUpdateLotacao();
  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  function applyBackendErrors(error: unknown) {
    const generic = extractDomainErrorMessage(error) ?? "Erro ao salvar lotação.";
    const data =
      typeof error === "object" && error !== null && "response" in error
        ? (error as { response?: { data?: Record<string, unknown> } }).response?.data
        : undefined;
    let mappedAny = false;
    if (data && typeof data === "object") {
      for (const [field, value] of Object.entries(data)) {
        if (field === "detail" || field === "code") continue;
        if (field in form.getValues()) {
          const message = Array.isArray(value) ? String(value[0]) : String(value);
          form.setError(field as keyof LotacaoFormValues, { type: "server", message });
          mappedAny = true;
        }
      }
    }
    if (!mappedAny) toast.error(generic);
  }

  async function onSubmit(values: LotacaoFormValues) {
    try {
      if (isEdit && lotacao) {
        await updateMutation.mutateAsync({ id: lotacao.id, payload: values });
        toast.success("Lotação atualizada.");
      } else {
        await createMutation.mutateAsync(values);
        toast.success("Lotação criada.");
      }
      onOpenChange(false);
    } catch (err) {
      applyBackendErrors(err);
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-md flex flex-col">
        <SheetHeader>
          <SheetTitle>{isEdit ? "Editar lotação" : "Nova lotação"}</SheetTitle>
          <SheetDescription>
            {isEdit
              ? "Atualize os dados da lotação. Alterações ficam no histórico."
              : "Cadastre uma nova lotação (secretaria, departamento ou setor)."}
          </SheetDescription>
        </SheetHeader>

        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="mt-6 flex-1 overflow-y-auto space-y-5"
            noValidate
          >
            <FormField
              control={form.control}
              name="codigo"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Código</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Ex.: SEMED"
                      autoComplete="off"
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
              name="nome"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nome</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Ex.: Secretaria Municipal de Educação"
                      autoComplete="off"
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
              name="sigla"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Sigla (opcional)</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Ex.: SEMED"
                      autoComplete="off"
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
              name="lotacao_pai"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Lotação pai (opcional)</FormLabel>
                  <Select
                    value={field.value === null ? NONE_VALUE : String(field.value)}
                    onValueChange={(v) =>
                      field.onChange(v === NONE_VALUE ? null : Number(v))
                    }
                    disabled={isSubmitting || paiQuery.isLoading}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Sem lotação pai" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value={NONE_VALUE}>— Sem pai (raiz) —</SelectItem>
                      {possiveisPais.map((l) => (
                        <SelectItem key={l.id} value={String(l.id)}>
                          {l.sigla ? `${l.sigla} — ${l.nome}` : l.nome}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="ativo"
              render={({ field }) => (
                <FormItem className="flex flex-row items-start gap-3 space-y-0 rounded-md border p-3">
                  <FormControl>
                    <input
                      type="checkbox"
                      checked={field.value}
                      onChange={(e) => field.onChange(e.target.checked)}
                      disabled={isSubmitting}
                      className="mt-0.5 h-4 w-4 rounded border-input text-primary focus:ring-2 focus:ring-ring"
                    />
                  </FormControl>
                  <div className="space-y-1 leading-none">
                    <FormLabel className="cursor-pointer">Lotação ativa</FormLabel>
                    <p className="text-xs text-muted-foreground">
                      Lotações inativas não aparecem em formulários de admissão.
                    </p>
                  </div>
                </FormItem>
              )}
            />

            <SheetFooter className="pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isSubmitting}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting
                  ? "Salvando..."
                  : isEdit
                    ? "Salvar alterações"
                    : "Criar lotação"}
              </Button>
            </SheetFooter>
          </form>
        </Form>
      </SheetContent>
    </Sheet>
  );
}
