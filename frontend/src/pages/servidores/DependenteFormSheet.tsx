/**
 * DependenteFormSheet — Bloco 1.3c.
 *
 * Sheet de criação/edição de Dependente. CPF é opcional (alguns dependentes
 * jovens ainda não têm). Se "ir" estiver marcado, a flag entra no cálculo
 * de IRRF (Bloco 2). Se "salario_familia" estiver marcado, idem para o
 * cálculo do salário-família.
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
import { useCreateDependente, useUpdateDependente } from "@/lib/queries/dependentes";

/** Forma mínima aceita pelo formulário (compatível com embedded + detail). */
export interface DependenteForForm {
  id: number;
  nome: string;
  cpf?: string;
  data_nascimento: string;
  parentesco: string;
  ir?: boolean;
  salario_familia?: boolean;
}

const PARENTESCOS = [
  { value: "conjuge", label: "Cônjuge" },
  { value: "filho", label: "Filho(a)" },
  { value: "enteado", label: "Enteado(a)" },
  { value: "pai_mae", label: "Pai/Mãe" },
  { value: "outro", label: "Outro" },
] as const;

const schema = z.object({
  nome: z.string().min(2, "Nome muito curto.").max(200),
  cpf: z.string(),
  data_nascimento: z.string().min(10, "Data de nascimento é obrigatória."),
  parentesco: z.enum(["conjuge", "filho", "enteado", "pai_mae", "outro"]),
  ir: z.boolean(),
  salario_familia: z.boolean(),
});

type FormValues = z.infer<typeof schema>;

interface DependenteFormSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  servidorId: number;
  dependente: DependenteForForm | null;
}

export function DependenteFormSheet({
  open,
  onOpenChange,
  servidorId,
  dependente,
}: DependenteFormSheetProps) {
  const isEdit = dependente !== null;

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      nome: "",
      cpf: "",
      data_nascimento: "",
      parentesco: "filho",
      ir: false,
      salario_familia: false,
    },
  });

  useEffect(() => {
    if (open && dependente) {
      form.reset({
        nome: dependente.nome,
        cpf: dependente.cpf || "",
        data_nascimento: dependente.data_nascimento,
        parentesco: dependente.parentesco as FormValues["parentesco"],
        ir: dependente.ir ?? false,
        salario_familia: dependente.salario_familia ?? false,
      });
    } else if (open && !dependente) {
      form.reset({
        nome: "",
        cpf: "",
        data_nascimento: "",
        parentesco: "filho",
        ir: false,
        salario_familia: false,
      });
    }
  }, [open, dependente, form]);

  const createMutation = useCreateDependente();
  const updateMutation = useUpdateDependente();
  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  function applyBackendErrors(error: unknown) {
    const generic = extractDomainErrorMessage(error) ?? "Erro ao salvar dependente.";
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
          form.setError(field as keyof FormValues, { type: "server", message });
          mappedAny = true;
        }
      }
    }
    if (!mappedAny) toast.error(generic);
  }

  async function onSubmit(values: FormValues) {
    try {
      if (isEdit && dependente) {
        await updateMutation.mutateAsync({
          id: dependente.id,
          payload: { ...values, servidor: servidorId },
        });
        toast.success("Dependente atualizado.");
      } else {
        await createMutation.mutateAsync({ ...values, servidor: servidorId });
        toast.success("Dependente cadastrado.");
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
          <SheetTitle>{isEdit ? "Editar dependente" : "Novo dependente"}</SheetTitle>
          <SheetDescription>
            Dependentes do servidor para fins de IR e salário-família.
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
              name="nome"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nome completo</FormLabel>
                  <FormControl>
                    <Input autoComplete="off" disabled={isSubmitting} {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-3">
              <FormField
                control={form.control}
                name="data_nascimento"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Data de nascimento</FormLabel>
                    <FormControl>
                      <Input type="date" disabled={isSubmitting} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="cpf"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>CPF (opcional)</FormLabel>
                    <FormControl>
                      <Input autoComplete="off" disabled={isSubmitting} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="parentesco"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Parentesco</FormLabel>
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
                      {PARENTESCOS.map((p) => (
                        <SelectItem key={p.value} value={p.value}>
                          {p.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <fieldset className="space-y-3 rounded-md border p-3">
              <legend className="text-sm font-medium px-1">Benefícios fiscais</legend>
              <FormField
                control={form.control}
                name="ir"
                render={({ field }) => (
                  <label className="flex items-start gap-2 text-sm cursor-pointer">
                    <input
                      type="checkbox"
                      checked={field.value}
                      onChange={(e) => field.onChange(e.target.checked)}
                      disabled={isSubmitting}
                      className="mt-0.5 h-4 w-4 rounded border-input text-primary focus:ring-2 focus:ring-ring"
                    />
                    <span>
                      <span className="font-medium">Dependente para IR</span>
                      <span className="block text-xs text-muted-foreground">
                        Reduz a base de cálculo do IRRF.
                      </span>
                    </span>
                  </label>
                )}
              />
              <FormField
                control={form.control}
                name="salario_familia"
                render={({ field }) => (
                  <label className="flex items-start gap-2 text-sm cursor-pointer">
                    <input
                      type="checkbox"
                      checked={field.value}
                      onChange={(e) => field.onChange(e.target.checked)}
                      disabled={isSubmitting}
                      className="mt-0.5 h-4 w-4 rounded border-input text-primary focus:ring-2 focus:ring-ring"
                    />
                    <span>
                      <span className="font-medium">Salário-família</span>
                      <span className="block text-xs text-muted-foreground">
                        Servidor receberá a quota correspondente (filhos &lt; 14 ou inválidos).
                      </span>
                    </span>
                  </label>
                )}
              />
            </fieldset>

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
                    : "Adicionar dependente"}
              </Button>
            </SheetFooter>
          </form>
        </Form>
      </SheetContent>
    </Sheet>
  );
}
