/**
 * RubricaFormSheet — Bloco 1.3b.
 *
 * Sheet com formulário de criação/edição de Rubrica.
 * O campo `formula` (DSL) é apenas TextField sem interpretação até o Bloco 2 —
 * mostra hint indicando que a fórmula ainda não é avaliada.
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
import { useCreateRubrica, useUpdateRubrica } from "@/lib/queries/rubricas";
import type { RubricaDetail } from "@/types";

const TIPOS = [
  { value: "provento", label: "Provento" },
  { value: "desconto", label: "Desconto" },
  { value: "informativa", label: "Informativa" },
] as const;

const rubricaSchema = z.object({
  codigo: z
    .string()
    .min(1, "Código é obrigatório.")
    .max(20, "Código deve ter no máximo 20 caracteres."),
  nome: z
    .string()
    .min(2, "Nome muito curto.")
    .max(200, "Nome deve ter no máximo 200 caracteres."),
  tipo: z.enum(["provento", "desconto", "informativa"]),
  incide_inss: z.boolean(),
  incide_irrf: z.boolean(),
  incide_fgts: z.boolean(),
  formula: z.string(),
  ativo: z.boolean(),
});

type RubricaFormValues = z.infer<typeof rubricaSchema>;

interface RubricaFormSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  rubrica: RubricaDetail | null;
}

export function RubricaFormSheet({ open, onOpenChange, rubrica }: RubricaFormSheetProps) {
  const isEdit = rubrica !== null;

  const form = useForm<RubricaFormValues>({
    resolver: zodResolver(rubricaSchema),
    defaultValues: {
      codigo: "",
      nome: "",
      tipo: "provento",
      incide_inss: false,
      incide_irrf: false,
      incide_fgts: false,
      formula: "",
      ativo: true,
    },
  });

  useEffect(() => {
    if (open && rubrica) {
      form.reset({
        codigo: rubrica.codigo,
        nome: rubrica.nome,
        tipo: rubrica.tipo,
        incide_inss: rubrica.incide_inss,
        incide_irrf: rubrica.incide_irrf,
        incide_fgts: rubrica.incide_fgts,
        formula: rubrica.formula || "",
        ativo: rubrica.ativo,
      });
    } else if (open && !rubrica) {
      form.reset({
        codigo: "",
        nome: "",
        tipo: "provento",
        incide_inss: false,
        incide_irrf: false,
        incide_fgts: false,
        formula: "",
        ativo: true,
      });
    }
  }, [open, rubrica, form]);

  const createMutation = useCreateRubrica();
  const updateMutation = useUpdateRubrica();
  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  function applyBackendErrors(error: unknown) {
    const generic = extractDomainErrorMessage(error) ?? "Erro ao salvar rubrica.";
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
          form.setError(field as keyof RubricaFormValues, { type: "server", message });
          mappedAny = true;
        }
      }
    }
    if (!mappedAny) toast.error(generic);
  }

  async function onSubmit(values: RubricaFormValues) {
    try {
      if (isEdit && rubrica) {
        await updateMutation.mutateAsync({ id: rubrica.id, payload: values });
        toast.success("Rubrica atualizada.");
      } else {
        await createMutation.mutateAsync(values);
        toast.success("Rubrica criada.");
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
          <SheetTitle>{isEdit ? "Editar rubrica" : "Nova rubrica"}</SheetTitle>
          <SheetDescription>
            {isEdit
              ? "Atualize a rubrica. A fórmula só será avaliada quando o engine de cálculo entrar (Bloco 2)."
              : "Cadastre uma nova rubrica (provento, desconto ou informativa)."}
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
                      placeholder="Ex.: SALARIO-BASE"
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
                      placeholder="Ex.: Salário-base"
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
              name="tipo"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Tipo</FormLabel>
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
                      {TIPOS.map((t) => (
                        <SelectItem key={t.value} value={t.value}>
                          {t.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <fieldset className="space-y-2 rounded-md border p-3">
              <legend className="text-sm font-medium px-1">Incidências</legend>
              <p className="text-xs text-muted-foreground">
                Marque os encargos sobre os quais esta rubrica incide.
              </p>
              <div className="grid grid-cols-3 gap-3 pt-2">
                <FormField
                  control={form.control}
                  name="incide_inss"
                  render={({ field }) => (
                    <label className="flex items-center gap-2 text-sm cursor-pointer">
                      <input
                        type="checkbox"
                        checked={field.value}
                        onChange={(e) => field.onChange(e.target.checked)}
                        disabled={isSubmitting}
                        className="h-4 w-4 rounded border-input text-primary focus:ring-2 focus:ring-ring"
                      />
                      INSS
                    </label>
                  )}
                />
                <FormField
                  control={form.control}
                  name="incide_irrf"
                  render={({ field }) => (
                    <label className="flex items-center gap-2 text-sm cursor-pointer">
                      <input
                        type="checkbox"
                        checked={field.value}
                        onChange={(e) => field.onChange(e.target.checked)}
                        disabled={isSubmitting}
                        className="h-4 w-4 rounded border-input text-primary focus:ring-2 focus:ring-ring"
                      />
                      IRRF
                    </label>
                  )}
                />
                <FormField
                  control={form.control}
                  name="incide_fgts"
                  render={({ field }) => (
                    <label className="flex items-center gap-2 text-sm cursor-pointer">
                      <input
                        type="checkbox"
                        checked={field.value}
                        onChange={(e) => field.onChange(e.target.checked)}
                        disabled={isSubmitting}
                        className="h-4 w-4 rounded border-input text-primary focus:ring-2 focus:ring-ring"
                      />
                      FGTS
                    </label>
                  )}
                />
              </div>
            </fieldset>

            <FormField
              control={form.control}
              name="formula"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Fórmula (DSL)</FormLabel>
                  <FormControl>
                    <textarea
                      {...field}
                      rows={4}
                      placeholder="Ex.: SALARIO_BASE * 0.10"
                      disabled={isSubmitting}
                      className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    />
                  </FormControl>
                  <p className="text-xs text-muted-foreground">
                    A fórmula será interpretada pelo engine de cálculo no Bloco 2. Por enquanto,
                    é apenas armazenada como texto.
                  </p>
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
                    <FormLabel className="cursor-pointer">Rubrica ativa</FormLabel>
                    <p className="text-xs text-muted-foreground">
                      Rubricas inativas não entram no cálculo de folha.
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
                    : "Criar rubrica"}
              </Button>
            </SheetFooter>
          </form>
        </Form>
      </SheetContent>
    </Sheet>
  );
}
