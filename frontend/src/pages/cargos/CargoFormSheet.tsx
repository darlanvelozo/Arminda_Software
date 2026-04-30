/**
 * CargoFormSheet — Bloco 1.3b.
 *
 * Sheet (slide-from-right) com o formulário de criação/edição de Cargo.
 * Validação client-side via Zod; erros do backend mapeados por campo
 * (DRF retorna { campo: ["msg", ...] } em 400).
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
import { useCreateCargo, useUpdateCargo } from "@/lib/queries/cargos";
import type { CargoDetail } from "@/types";

const ESCOLARIDADES = [
  { value: "fundamental", label: "Fundamental" },
  { value: "medio", label: "Médio" },
  { value: "tecnico", label: "Técnico" },
  { value: "superior", label: "Superior" },
  { value: "pos_graduacao", label: "Pós-graduação" },
] as const;

const cargoSchema = z.object({
  codigo: z
    .string()
    .min(1, "Código é obrigatório.")
    .max(20, "Código deve ter no máximo 20 caracteres."),
  nome: z
    .string()
    .min(2, "Nome muito curto.")
    .max(200, "Nome deve ter no máximo 200 caracteres."),
  cbo: z.string().max(10, "CBO deve ter no máximo 10 caracteres."),
  nivel_escolaridade: z.enum([
    "fundamental",
    "medio",
    "tecnico",
    "superior",
    "pos_graduacao",
  ]),
  ativo: z.boolean(),
});

type CargoFormValues = z.infer<typeof cargoSchema>;

interface CargoFormSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  cargo: CargoDetail | null;
}

export function CargoFormSheet({ open, onOpenChange, cargo }: CargoFormSheetProps) {
  const isEdit = cargo !== null;

  const form = useForm<CargoFormValues>({
    resolver: zodResolver(cargoSchema),
    defaultValues: {
      codigo: "",
      nome: "",
      cbo: "",
      nivel_escolaridade: "medio",
      ativo: true,
    },
  });

  useEffect(() => {
    if (open && cargo) {
      form.reset({
        codigo: cargo.codigo,
        nome: cargo.nome,
        cbo: cargo.cbo || "",
        nivel_escolaridade: cargo.nivel_escolaridade,
        ativo: cargo.ativo,
      });
    } else if (open && !cargo) {
      form.reset({
        codigo: "",
        nome: "",
        cbo: "",
        nivel_escolaridade: "medio",
        ativo: true,
      });
    }
  }, [open, cargo, form]);

  const createMutation = useCreateCargo();
  const updateMutation = useUpdateCargo();
  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  function applyBackendErrors(error: unknown) {
    const generic = extractDomainErrorMessage(error) ?? "Erro ao salvar cargo.";
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
          form.setError(field as keyof CargoFormValues, { type: "server", message });
          mappedAny = true;
        }
      }
    }
    if (!mappedAny) toast.error(generic);
  }

  async function onSubmit(values: CargoFormValues) {
    try {
      if (isEdit && cargo) {
        await updateMutation.mutateAsync({ id: cargo.id, payload: values });
        toast.success("Cargo atualizado.");
      } else {
        await createMutation.mutateAsync(values);
        toast.success("Cargo criado.");
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
          <SheetTitle>{isEdit ? "Editar cargo" : "Novo cargo"}</SheetTitle>
          <SheetDescription>
            {isEdit
              ? "Atualize os dados do cargo. Alterações ficam registradas no histórico."
              : "Cadastre um novo cargo público para o município."}
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
                      placeholder="Ex.: PROF-EF"
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
                      placeholder="Ex.: Professor de Ensino Fundamental"
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
              name="cbo"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>CBO (opcional)</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Ex.: 2312"
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
              name="nivel_escolaridade"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Escolaridade exigida</FormLabel>
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
                      {ESCOLARIDADES.map((e) => (
                        <SelectItem key={e.value} value={e.value}>
                          {e.label}
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
                    <FormLabel className="cursor-pointer">Cargo ativo</FormLabel>
                    <p className="text-xs text-muted-foreground">
                      Cargos inativos não aparecem em formulários de admissão.
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
                {isSubmitting ? "Salvando..." : isEdit ? "Salvar alterações" : "Criar cargo"}
              </Button>
            </SheetFooter>
          </form>
        </Form>
      </SheetContent>
    </Sheet>
  );
}
