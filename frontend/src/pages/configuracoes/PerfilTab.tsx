/**
 * PerfilTab — edita dados do próprio usuário (Onda 1.5).
 *
 * Por enquanto, só `nome_completo` é editável (PATCH /api/auth/me/).
 * E-mail é imutável — exibido apenas para referência.
 */

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
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
import { Label } from "@/components/ui/label";
import { extractDomainErrorMessage } from "@/lib/api";
import { updateMe } from "@/lib/auth";
import { useAuth } from "@/lib/auth-context";

const schema = z.object({
  nome_completo: z
    .string()
    .min(2, "Nome muito curto.")
    .max(200, "Nome deve ter no máximo 200 caracteres."),
});

type FormValues = z.infer<typeof schema>;

export function PerfilTab() {
  const { user, refresh } = useAuth();

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { nome_completo: user?.nome_completo ?? "" },
  });

  const mutation = useMutation({
    mutationFn: updateMe,
    onSuccess: async () => {
      await refresh();
      toast.success("Perfil atualizado.");
    },
    onError: (err) => {
      toast.error(extractDomainErrorMessage(err) ?? "Falha ao atualizar.");
    },
  });

  if (!user) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Meu perfil</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="space-y-1.5">
          <Label>E-mail (não editável)</Label>
          <Input value={user.email} disabled readOnly className="font-mono text-sm" />
          <p className="text-xs text-muted-foreground">
            Para trocar o e-mail, fale com o suporte.
          </p>
        </div>

        <Form {...form}>
          <form
            onSubmit={form.handleSubmit((v) => mutation.mutate(v))}
            className="space-y-4"
            noValidate
          >
            <FormField
              control={form.control}
              name="nome_completo"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nome completo</FormLabel>
                  <FormControl>
                    <Input
                      autoComplete="name"
                      disabled={mutation.isPending}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex justify-end">
              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? "Salvando..." : "Salvar alterações"}
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
