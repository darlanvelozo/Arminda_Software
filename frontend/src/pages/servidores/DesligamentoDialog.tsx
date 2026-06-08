/**
 * DesligamentoDialog — Bloco 1.3c.
 *
 * AlertDialog (com form embutido) para desligar o servidor — encerra TODOS os
 * vínculos ativos e marca o servidor como inativo, em transação atômica.
 * POST /api/people/servidores/{id}/desligar/.
 */

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
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
import { extractDomainErrorMessage } from "@/lib/api";
import { useDesligarServidor } from "@/lib/queries/servidores";

const MOTIVOS = [
  { value: "exoneracao", label: "Exoneração (estatutário)" },
  { value: "pedido_demissao", label: "Pedido de demissão" },
  { value: "sem_justa_causa", label: "Dispensa sem justa causa" },
  { value: "com_justa_causa", label: "Dispensa com justa causa" },
  { value: "termino_contrato", label: "Término de contrato" },
  { value: "aposentadoria", label: "Aposentadoria" },
  { value: "falecimento", label: "Falecimento" },
] as const;

const schema = z.object({
  data_desligamento: z.string().min(10, "Data é obrigatória."),
  motivo_demissao: z.string().min(1, "Selecione o motivo."),
  aviso_previo_indenizado: z.boolean(),
  tem_ferias_vencidas: z.boolean(),
  saldo_fgts: z.string(),
  motivo: z.string().max(500, "Motivo deve ter no máximo 500 caracteres."),
});

type FormValues = z.infer<typeof schema>;

interface DesligamentoDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  servidorId: number;
  servidorNome: string;
}

export function DesligamentoDialog({
  open,
  onOpenChange,
  servidorId,
  servidorNome,
}: DesligamentoDialogProps) {
  const EMPTY: FormValues = {
    data_desligamento: "",
    motivo_demissao: "",
    aviso_previo_indenizado: false,
    tem_ferias_vencidas: false,
    saldo_fgts: "0",
    motivo: "",
  };

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: EMPTY,
  });

  useEffect(() => {
    if (open) form.reset(EMPTY);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, form]);

  const desligarMutation = useDesligarServidor();
  const isSubmitting = desligarMutation.isPending;

  async function onSubmit(values: FormValues) {
    try {
      await desligarMutation.mutateAsync({ id: servidorId, payload: values });
      toast.success(`${servidorNome} desligado.`);
      onOpenChange(false);
    } catch (e) {
      const data =
        typeof e === "object" && e !== null && "response" in e
          ? (e as { response?: { data?: Record<string, unknown> } }).response?.data
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
      if (!mappedAny) toast.error(extractDomainErrorMessage(e) ?? "Falha ao desligar.");
    }
  }

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Desligar servidor?</AlertDialogTitle>
          <AlertDialogDescription>
            Esta ação encerra <strong>todos os vínculos ativos</strong> de{" "}
            <strong>{servidorNome}</strong> e marca o servidor como inativo. A operação é
            atômica e fica registrada no histórico.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4" noValidate>
            <FormField
              control={form.control}
              name="data_desligamento"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Data de desligamento</FormLabel>
                  <FormControl>
                    <Input type="date" disabled={isSubmitting} {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="motivo_demissao"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Motivo do desligamento</FormLabel>
                  <Select
                    value={field.value}
                    onValueChange={field.onChange}
                    disabled={isSubmitting}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione…" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {MOTIVOS.map((m) => (
                        <SelectItem key={m.value} value={m.value}>
                          {m.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">
                    Define as verbas na folha de rescisão (saldo, 13º, férias, aviso).
                  </p>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-3">
              <FormField
                control={form.control}
                name="aviso_previo_indenizado"
                render={({ field }) => (
                  <label className="flex items-center gap-2 text-sm cursor-pointer">
                    <input
                      type="checkbox"
                      checked={field.value}
                      onChange={(e) => field.onChange(e.target.checked)}
                      disabled={isSubmitting}
                      className="h-4 w-4 rounded border-input text-primary focus:ring-2 focus:ring-ring"
                    />
                    Aviso prévio indenizado
                  </label>
                )}
              />
              <FormField
                control={form.control}
                name="tem_ferias_vencidas"
                render={({ field }) => (
                  <label className="flex items-center gap-2 text-sm cursor-pointer">
                    <input
                      type="checkbox"
                      checked={field.value}
                      onChange={(e) => field.onChange(e.target.checked)}
                      disabled={isSubmitting}
                      className="h-4 w-4 rounded border-input text-primary focus:ring-2 focus:ring-ring"
                    />
                    Tem férias vencidas
                  </label>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="saldo_fgts"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Saldo do FGTS (para multa de 40%)</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      step="0.01"
                      placeholder="0.00"
                      disabled={isSubmitting}
                      {...field}
                    />
                  </FormControl>
                  <p className="text-xs text-muted-foreground">
                    Só para celetista sem justa causa. Deixe 0 se não se aplica.
                  </p>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="motivo"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Observação (opcional)</FormLabel>
                  <FormControl>
                    <textarea
                      {...field}
                      rows={3}
                      placeholder="Ex.: Aposentadoria, exoneração a pedido, fim de contrato..."
                      disabled={isSubmitting}
                      className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isSubmitting}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={isSubmitting}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              >
                {isSubmitting ? "Desligando..." : "Confirmar desligamento"}
              </Button>
            </div>
          </form>
        </Form>
      </AlertDialogContent>
    </AlertDialog>
  );
}
