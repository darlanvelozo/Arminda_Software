/**
 * SegurancaTab — troca de senha do próprio usuário (Onda 1.5).
 *
 * Validação client-side com Zod (mínimo 8 chars + confirmação igual);
 * o backend faz validação completa via `validate_password` do Django
 * (similaridade, lista de senhas comuns, mínimo numérico, etc.) e
 * mapeia erros por campo via `code` do ValidationError.
 */

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { Eye, EyeOff } from "lucide-react";
import { useState } from "react";
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
import { extractDomainErrorMessage } from "@/lib/api";
import { changePassword } from "@/lib/auth";

const schema = z
  .object({
    current_password: z.string().min(1, "Informe sua senha atual."),
    new_password: z
      .string()
      .min(8, "Nova senha deve ter pelo menos 8 caracteres.")
      .max(128),
    new_password_confirm: z.string().min(1, "Confirme a nova senha."),
  })
  .refine((data) => data.new_password === data.new_password_confirm, {
    path: ["new_password_confirm"],
    message: "As senhas não conferem.",
  })
  .refine((data) => data.new_password !== data.current_password, {
    path: ["new_password"],
    message: "Nova senha deve ser diferente da atual.",
  });

type FormValues = z.infer<typeof schema>;

export function SegurancaTab() {
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      current_password: "",
      new_password: "",
      new_password_confirm: "",
    },
  });

  const mutation = useMutation({
    mutationFn: changePassword,
    onSuccess: () => {
      form.reset();
      toast.success("Senha alterada.");
    },
    onError: (err) => {
      const data =
        typeof err === "object" && err !== null && "response" in err
          ? (err as { response?: { data?: Record<string, unknown> } }).response?.data
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
      if (!mappedAny) {
        toast.error(extractDomainErrorMessage(err) ?? "Falha ao alterar senha.");
      }
    },
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Trocar senha</CardTitle>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit((v) => mutation.mutate(v))}
            className="space-y-4 max-w-md"
            noValidate
          >
            <FormField
              control={form.control}
              name="current_password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Senha atual</FormLabel>
                  <FormControl>
                    <PasswordInput
                      visible={showCurrent}
                      onToggle={() => setShowCurrent((s) => !s)}
                      autoComplete="current-password"
                      disabled={mutation.isPending}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="new_password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nova senha</FormLabel>
                  <FormControl>
                    <PasswordInput
                      visible={showNew}
                      onToggle={() => setShowNew((s) => !s)}
                      autoComplete="new-password"
                      disabled={mutation.isPending}
                      {...field}
                    />
                  </FormControl>
                  <p className="text-xs text-muted-foreground">
                    Mínimo 8 caracteres. Evite senhas óbvias (ex.: 12345678).
                  </p>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="new_password_confirm"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Confirmar nova senha</FormLabel>
                  <FormControl>
                    <PasswordInput
                      visible={showNew}
                      onToggle={() => setShowNew((s) => !s)}
                      autoComplete="new-password"
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
                {mutation.isPending ? "Alterando..." : "Alterar senha"}
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}

interface PasswordInputProps extends React.ComponentProps<typeof Input> {
  visible: boolean;
  onToggle: () => void;
}

function PasswordInput({ visible, onToggle, ...props }: PasswordInputProps) {
  return (
    <div className="relative">
      <Input type={visible ? "text" : "password"} className="pr-10" {...props} />
      <button
        type="button"
        onClick={onToggle}
        tabIndex={-1}
        className="absolute right-1 top-1/2 -translate-y-1/2 p-2 text-muted-foreground hover:text-foreground rounded-sm"
        aria-label={visible ? "Ocultar senha" : "Mostrar senha"}
      >
        {visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
      </button>
    </div>
  );
}
