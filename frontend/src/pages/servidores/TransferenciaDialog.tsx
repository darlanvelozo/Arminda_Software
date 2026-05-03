/**
 * TransferenciaDialog — Bloco 1.3c.
 *
 * Dialog para transferir um vínculo para outra lotação. Encerra o vínculo
 * atual e cria um novo na nova lotação, em transação atômica.
 * POST /api/people/vinculos/{id}/transferir/.
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
import { useLotacoesList } from "@/lib/queries/lotacoes";
import { useTransferirVinculo } from "@/lib/queries/vinculos";

const schema = z.object({
  nova_lotacao_id: z.number().int().positive("Selecione a nova lotação."),
  data_transferencia: z.string().min(10, "Data é obrigatória."),
});

type FormValues = z.infer<typeof schema>;

interface TransferenciaDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  vinculoId: number;
  lotacaoAtualId: number;
  lotacaoAtualNome: string;
}

export function TransferenciaDialog({
  open,
  onOpenChange,
  vinculoId,
  lotacaoAtualId,
  lotacaoAtualNome,
}: TransferenciaDialogProps) {
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { nova_lotacao_id: 0, data_transferencia: "" },
  });

  useEffect(() => {
    if (open) form.reset({ nova_lotacao_id: 0, data_transferencia: "" });
  }, [open, form]);

  const lotacoesQuery = useLotacoesList({ ativo: true, ordering: "nome" });
  const lotacoesElegiveis =
    lotacoesQuery.data?.results.filter((l) => l.id !== lotacaoAtualId) ?? [];

  const transferirMutation = useTransferirVinculo();
  const isSubmitting = transferirMutation.isPending;

  async function onSubmit(values: FormValues) {
    try {
      await transferirMutation.mutateAsync({ id: vinculoId, payload: values });
      toast.success("Transferência concluída.");
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
      if (!mappedAny) toast.error(extractDomainErrorMessage(e) ?? "Falha ao transferir.");
    }
  }

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Transferir vínculo</AlertDialogTitle>
          <AlertDialogDescription>
            O vínculo atual em <strong>{lotacaoAtualNome}</strong> será encerrado na
            data informada e um novo vínculo será criado na lotação selecionada
            (mesmo cargo, regime e salário-base). Operação atômica.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4" noValidate>
            <FormField
              control={form.control}
              name="nova_lotacao_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nova lotação</FormLabel>
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
                      {lotacoesElegiveis.map((l) => (
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
              name="data_transferencia"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Data da transferência</FormLabel>
                  <FormControl>
                    <Input type="date" disabled={isSubmitting} {...field} />
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
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Transferindo..." : "Confirmar transferência"}
              </Button>
            </div>
          </form>
        </Form>
      </AlertDialogContent>
    </AlertDialog>
  );
}
