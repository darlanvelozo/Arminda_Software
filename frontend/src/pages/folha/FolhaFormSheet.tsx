/**
 * FolhaFormSheet — Onda 2.6.
 *
 * Sheet com formulário de criação/edição de Folha. Edição é apenas para
 * `observacoes` e `tipo` — competência fica imutável após criação porque
 * o constraint UNIQUE(competencia, tipo) deve refletir a competência real
 * da folha aberta.
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
import { Textarea } from "@/components/ui/textarea";
import { extractDomainErrorMessage } from "@/lib/api";
import { useCreateFolha, useUpdateFolha } from "@/lib/queries/folhas";
import type { FolhaDetail } from "@/types";

const TIPOS = [
  { value: "mensal", label: "Mensal" },
  { value: "13_primeira", label: "13º — 1ª parcela" },
  { value: "13_segunda", label: "13º — 2ª parcela" },
  { value: "ferias", label: "Férias" },
  { value: "rescisao", label: "Rescisão" },
  { value: "licenca_premio", label: "Licença-prêmio (indenização)" },
  { value: "complementar", label: "Complementar" },
] as const;

const folhaSchema = z.object({
  competencia: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, "Use o formato AAAA-MM-DD.")
    .refine((v) => v.endsWith("-01"), "Competência deve ser o dia 1 do mês."),
  tipo: z.enum([
    "mensal",
    "13_primeira",
    "13_segunda",
    "ferias",
    "rescisao",
    "licenca_premio",
    "complementar",
  ]),
  observacoes: z.string(),
});

type FolhaFormValues = z.infer<typeof folhaSchema>;

interface FolhaFormSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  folha: FolhaDetail | null;
}

function competenciaSugerida(): string {
  const hoje = new Date();
  const ano = hoje.getFullYear();
  const mes = String(hoje.getMonth() + 1).padStart(2, "0");
  return `${ano}-${mes}-01`;
}

export function FolhaFormSheet({ open, onOpenChange, folha }: FolhaFormSheetProps) {
  const isEdit = folha !== null;
  const createMut = useCreateFolha();
  const updateMut = useUpdateFolha();

  const form = useForm<FolhaFormValues>({
    resolver: zodResolver(folhaSchema),
    defaultValues: {
      competencia: competenciaSugerida(),
      tipo: "mensal",
      observacoes: "",
    },
  });

  useEffect(() => {
    if (open && folha) {
      form.reset({
        competencia: folha.competencia,
        tipo: folha.tipo,
        observacoes: folha.observacoes ?? "",
      });
    } else if (open && !folha) {
      form.reset({
        competencia: competenciaSugerida(),
        tipo: "mensal",
        observacoes: "",
      });
    }
  }, [open, folha, form]);

  async function onSubmit(values: FolhaFormValues) {
    try {
      if (isEdit && folha) {
        await updateMut.mutateAsync({
          id: folha.id,
          // Competência imutável após criação
          payload: { tipo: values.tipo, observacoes: values.observacoes },
        });
        toast.success("Folha atualizada.");
      } else {
        await createMut.mutateAsync(values);
        toast.success("Folha criada.");
      }
      onOpenChange(false);
    } catch (e) {
      toast.error(extractDomainErrorMessage(e) ?? "Erro ao salvar folha.");
    }
  }

  const submitting = createMut.isPending || updateMut.isPending;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="overflow-y-auto">
        <SheetHeader>
          <SheetTitle>{isEdit ? "Editar folha" : "Nova folha"}</SheetTitle>
          <SheetDescription>
            {isEdit
              ? "Competência fica imutável; ajuste tipo e observações."
              : "Crie a folha do mês. O cálculo é disparado pela tela de detalhe."}
          </SheetDescription>
        </SheetHeader>

        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="px-4 py-3 space-y-4"
          >
            <FormField
              control={form.control}
              name="competencia"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Competência *</FormLabel>
                  <FormControl>
                    <Input
                      type="date"
                      {...field}
                      disabled={isEdit}
                      aria-disabled={isEdit}
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
                  <FormLabel>Tipo *</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
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

            <FormField
              control={form.control}
              name="observacoes"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Observações</FormLabel>
                  <FormControl>
                    <Textarea
                      rows={3}
                      placeholder="Notas operacionais (opcional)"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <SheetFooter className="flex gap-2 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={submitting}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? "Salvando…" : isEdit ? "Salvar" : "Criar folha"}
              </Button>
            </SheetFooter>
          </form>
        </Form>
      </SheetContent>
    </Sheet>
  );
}
