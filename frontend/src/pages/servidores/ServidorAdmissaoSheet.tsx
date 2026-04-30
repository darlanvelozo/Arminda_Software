/**
 * ServidorAdmissaoSheet — Bloco 1.3b.
 *
 * Sheet com formulário único de admissão (cria Servidor + Vínculo em transação
 * atômica via POST /api/people/servidores/admitir/).
 *
 * Campos validados client-side com Zod; CPF e datas validados também no backend
 * (ValidationError vem como { campo: [...] }).
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
import { useCargosList } from "@/lib/queries/cargos";
import { useLotacoesList } from "@/lib/queries/lotacoes";
import { useAdmitirServidor } from "@/lib/queries/servidores";

const REGIMES = [
  { value: "estatutario", label: "Estatutário" },
  { value: "celetista", label: "Celetista" },
  { value: "comissionado", label: "Comissionado" },
  { value: "temporario", label: "Temporário" },
  { value: "estagiario", label: "Estagiário" },
] as const;

const admissaoSchema = z.object({
  // Pessoais
  matricula: z.string().min(1, "Matrícula é obrigatória.").max(30),
  nome: z.string().min(2, "Nome muito curto.").max(200),
  cpf: z.string().min(11, "CPF inválido.").max(14),
  data_nascimento: z.string().min(10, "Data de nascimento é obrigatória."),
  sexo: z.enum(["M", "F"]),
  estado_civil: z.string(),
  pis_pasep: z.string(),
  email: z.string().email("E-mail inválido.").or(z.literal("")),
  telefone: z.string(),
  // Vínculo
  cargo_id: z.number().int().positive("Selecione o cargo."),
  lotacao_id: z.number().int().positive("Selecione a lotação."),
  regime: z.enum(["estatutario", "celetista", "comissionado", "temporario", "estagiario"]),
  data_admissao: z.string().min(10, "Data de admissão é obrigatória."),
  salario_base: z.string().min(1, "Salário-base é obrigatório."),
  carga_horaria: z.coerce.number().int().min(1).max(60),
});

type AdmissaoFormValues = z.infer<typeof admissaoSchema>;

interface ServidorAdmissaoSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: (servidorId: number) => void;
}

export function ServidorAdmissaoSheet({
  open,
  onOpenChange,
  onSuccess,
}: ServidorAdmissaoSheetProps) {
  const form = useForm<AdmissaoFormValues>({
    resolver: zodResolver(admissaoSchema),
    defaultValues: {
      matricula: "",
      nome: "",
      cpf: "",
      data_nascimento: "",
      sexo: "M",
      estado_civil: "",
      pis_pasep: "",
      email: "",
      telefone: "",
      cargo_id: 0,
      lotacao_id: 0,
      regime: "estatutario",
      data_admissao: "",
      salario_base: "",
      carga_horaria: 40,
    },
  });

  useEffect(() => {
    if (open) {
      form.reset();
    }
  }, [open, form]);

  const cargosQuery = useCargosList({ ativo: true, ordering: "nome" });
  const lotacoesQuery = useLotacoesList({ ativo: true, ordering: "nome" });

  const admitirMutation = useAdmitirServidor();
  const isSubmitting = admitirMutation.isPending;

  function applyBackendErrors(error: unknown) {
    const generic = extractDomainErrorMessage(error) ?? "Erro ao admitir servidor.";
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
          form.setError(field as keyof AdmissaoFormValues, { type: "server", message });
          mappedAny = true;
        }
      }
    }
    if (!mappedAny) toast.error(generic);
  }

  async function onSubmit(values: AdmissaoFormValues) {
    try {
      const created = await admitirMutation.mutateAsync(values);
      toast.success(`${created.nome} admitido com sucesso.`);
      onOpenChange(false);
      onSuccess?.(created.id);
    } catch (err) {
      applyBackendErrors(err);
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-xl flex flex-col">
        <SheetHeader>
          <SheetTitle>Admitir servidor</SheetTitle>
          <SheetDescription>
            Cria o servidor e o primeiro vínculo funcional em transação atômica.
          </SheetDescription>
        </SheetHeader>

        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="mt-6 flex-1 overflow-y-auto space-y-6 pr-1"
            noValidate
          >
            <fieldset className="space-y-4">
              <legend className="text-sm font-semibold">Dados pessoais</legend>

              <div className="grid grid-cols-2 gap-3">
                <FormField
                  control={form.control}
                  name="matricula"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Matrícula</FormLabel>
                      <FormControl>
                        <Input autoComplete="off" disabled={isSubmitting} {...field} />
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
                      <FormLabel>CPF</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="000.000.000-00"
                          autoComplete="off"
                          disabled={isSubmitting}
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

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
                  name="sexo"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Sexo</FormLabel>
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
                          <SelectItem value="M">Masculino</SelectItem>
                          <SelectItem value="F">Feminino</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <FormField
                  control={form.control}
                  name="pis_pasep"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>PIS/PASEP (opcional)</FormLabel>
                      <FormControl>
                        <Input autoComplete="off" disabled={isSubmitting} {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="estado_civil"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Estado civil (opcional)</FormLabel>
                      <Select
                        value={field.value || "__"}
                        onValueChange={(v) => field.onChange(v === "__" ? "" : v)}
                        disabled={isSubmitting}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Não informado" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="__">Não informado</SelectItem>
                          <SelectItem value="solteiro">Solteiro(a)</SelectItem>
                          <SelectItem value="casado">Casado(a)</SelectItem>
                          <SelectItem value="divorciado">Divorciado(a)</SelectItem>
                          <SelectItem value="viuvo">Viúvo(a)</SelectItem>
                          <SelectItem value="uniao_estavel">União estável</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <FormField
                  control={form.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>E-mail (opcional)</FormLabel>
                      <FormControl>
                        <Input
                          type="email"
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
                  name="telefone"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Telefone (opcional)</FormLabel>
                      <FormControl>
                        <Input autoComplete="off" disabled={isSubmitting} {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </fieldset>

            <fieldset className="space-y-4 pt-2 border-t">
              <legend className="text-sm font-semibold pt-3">Vínculo inicial</legend>

              <div className="grid grid-cols-2 gap-3">
                <FormField
                  control={form.control}
                  name="cargo_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Cargo</FormLabel>
                      <Select
                        value={field.value ? String(field.value) : ""}
                        onValueChange={(v) => field.onChange(Number(v))}
                        disabled={isSubmitting || cargosQuery.isLoading}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Selecione..." />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {cargosQuery.data?.results.map((c) => (
                            <SelectItem key={c.id} value={String(c.id)}>
                              {c.codigo} — {c.nome}
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
                  name="lotacao_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Lotação</FormLabel>
                      <Select
                        value={field.value ? String(field.value) : ""}
                        onValueChange={(v) => field.onChange(Number(v))}
                        disabled={isSubmitting || lotacoesQuery.isLoading}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Selecione..." />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {lotacoesQuery.data?.results.map((l) => (
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
              </div>

              <div className="grid grid-cols-2 gap-3">
                <FormField
                  control={form.control}
                  name="regime"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Regime</FormLabel>
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
                          {REGIMES.map((r) => (
                            <SelectItem key={r.value} value={r.value}>
                              {r.label}
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
                  name="data_admissao"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Data de admissão</FormLabel>
                      <FormControl>
                        <Input type="date" disabled={isSubmitting} {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <FormField
                  control={form.control}
                  name="salario_base"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Salário-base (R$)</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          step="0.01"
                          min="0"
                          placeholder="0.00"
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
                  name="carga_horaria"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Carga horária (semanal)</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          min="1"
                          max="60"
                          disabled={isSubmitting}
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </fieldset>

            <SheetFooter className="pt-4 border-t">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isSubmitting}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Admitindo..." : "Admitir servidor"}
              </Button>
            </SheetFooter>
          </form>
        </Form>
      </SheetContent>
    </Sheet>
  );
}
