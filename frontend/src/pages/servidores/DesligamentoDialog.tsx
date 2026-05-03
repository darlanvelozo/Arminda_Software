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
import { extractDomainErrorMessage } from "@/lib/api";
import { useDesligarServidor } from "@/lib/queries/servidores";

const schema = z.object({
  data_desligamento: z.string().min(10, "Data é obrigatória."),
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
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { data_desligamento: "", motivo: "" },
  });

  useEffect(() => {
    if (open) form.reset({ data_desligamento: "", motivo: "" });
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
              name="motivo"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Motivo (opcional)</FormLabel>
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
