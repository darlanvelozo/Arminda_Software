/**
 * UsuariosTab — gestão de usuários do município ativo (Onda 1.5).
 *
 * Apenas admin_municipio (e staff_arminda) acessam. Lista, cria,
 * troca papel e remove papel. O User em si nunca é deletado — só
 * o vínculo com o município.
 */

import { zodResolver } from "@hookform/resolvers/zod";
import {
  AlertCircle,
  MoreHorizontal,
  Plus,
  ShieldAlert,
  Trash2,
  UserCog,
} from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { extractDomainErrorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import {
  useCreateUsuario,
  useDeletePapel,
  useUpdatePapel,
  useUsuariosList,
  type UsuarioMunicipioPapel,
} from "@/lib/queries/usuarios";

const PAPEIS = [
  { value: "admin_municipio", label: "Administrador" },
  { value: "rh_municipio", label: "RH" },
  { value: "financeiro_municipio", label: "Financeiro" },
  { value: "leitura_municipio", label: "Leitura" },
] as const;

function papelLabel(value: string): string {
  return PAPEIS.find((p) => p.value === value)?.label ?? value;
}

export function UsuariosTab() {
  const { papelAtual } = useAuth();
  const isAdmin = papelAtual === "admin_municipio" || papelAtual === "staff_arminda";

  const { data, isLoading, isError, error } = useUsuariosList();
  const updateMutation = useUpdatePapel();
  const deleteMutation = useDeletePapel();

  const [createOpen, setCreateOpen] = useState(false);
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);

  if (!isAdmin) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex items-center gap-3 text-muted-foreground">
            <ShieldAlert className="h-5 w-5" />
            <p className="text-sm">
              Apenas administradores do município podem gerir usuários.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  async function trocarPapel(item: UsuarioMunicipioPapel, novoPapel: string) {
    if (item.papel === novoPapel) return;
    try {
      await updateMutation.mutateAsync({ id: item.id, papel: novoPapel });
      toast.success("Papel atualizado.");
    } catch (e) {
      toast.error(extractDomainErrorMessage(e) ?? "Falha ao atualizar.");
    }
  }

  async function confirmarRemocao() {
    if (confirmDeleteId === null) return;
    try {
      await deleteMutation.mutateAsync(confirmDeleteId);
      toast.success("Acesso removido.");
      setConfirmDeleteId(null);
    } catch (e) {
      toast.error(extractDomainErrorMessage(e) ?? "Falha ao remover.");
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-3 space-y-0">
          <div>
            <CardTitle className="text-base">Usuários do município</CardTitle>
            <p className="text-xs text-muted-foreground mt-1">
              Gerencie quem tem acesso ao município ativo e qual papel exerce.
            </p>
          </div>
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4 mr-1" /> Novo usuário
          </Button>
        </CardHeader>
        <CardContent className="p-0">
          <div className="border-t">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Usuário</TableHead>
                  <TableHead className="w-[160px]">Papel</TableHead>
                  <TableHead className="w-[140px]">Status</TableHead>
                  <TableHead className="w-[64px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading && (
                  <>
                    {Array.from({ length: 3 }).map((_, i) => (
                      <TableRow key={i}>
                        <TableCell>
                          <Skeleton className="h-4 w-48" />
                        </TableCell>
                        <TableCell>
                          <Skeleton className="h-5 w-24" />
                        </TableCell>
                        <TableCell>
                          <Skeleton className="h-5 w-20" />
                        </TableCell>
                        <TableCell />
                      </TableRow>
                    ))}
                  </>
                )}
                {isError && (
                  <TableRow>
                    <TableCell colSpan={4} className="py-8 text-center text-sm text-destructive">
                      <AlertCircle className="h-4 w-4 inline mr-1" />
                      {extractDomainErrorMessage(error) ?? "Falha ao carregar usuários."}
                    </TableCell>
                  </TableRow>
                )}
                {!isLoading && !isError && data?.results.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={4} className="py-8 text-center text-sm text-muted-foreground">
                      Nenhum usuário cadastrado no município.
                    </TableCell>
                  </TableRow>
                )}
                {data?.results.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>
                      <div className="font-medium text-sm">
                        {item.usuario.nome_completo || item.usuario.email}
                      </div>
                      {item.usuario.nome_completo && (
                        <div className="text-xs text-muted-foreground font-mono">
                          {item.usuario.email}
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      <Select
                        value={item.papel}
                        onValueChange={(v) => trocarPapel(item, v)}
                      >
                        <SelectTrigger className="h-8 text-xs">
                          <SelectValue>{papelLabel(item.papel)}</SelectValue>
                        </SelectTrigger>
                        <SelectContent>
                          {PAPEIS.map((p) => (
                            <SelectItem key={p.value} value={p.value}>
                              {p.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col gap-1">
                        {item.usuario.is_active ? (
                          <Badge variant="success" className="w-fit">Ativo</Badge>
                        ) : (
                          <Badge variant="muted" className="w-fit">Inativo</Badge>
                        )}
                        {item.usuario.precisa_trocar_senha && (
                          <Badge variant="warning" className="w-fit">Senha pendente</Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" aria-label="Ações">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem disabled>
                            <UserCog className="h-4 w-4 mr-2" /> Ver perfil
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={() => setConfirmDeleteId(item.id)}
                            className="text-destructive focus:text-destructive"
                          >
                            <Trash2 className="h-4 w-4 mr-2" /> Remover acesso
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <NovoUsuarioSheet open={createOpen} onOpenChange={setCreateOpen} />

      <AlertDialog
        open={confirmDeleteId !== null}
        onOpenChange={(o) => !o && setConfirmDeleteId(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remover acesso ao município?</AlertDialogTitle>
            <AlertDialogDescription>
              O usuário não vai mais conseguir entrar neste município. Outros
              municípios em que ele tem papel não são afetados. O usuário em si
              continua existindo.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleteMutation.isPending}>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={(e) => {
                e.preventDefault();
                confirmarRemocao();
              }}
              disabled={deleteMutation.isPending}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleteMutation.isPending ? "Removendo..." : "Remover"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

const novoUsuarioSchema = z.object({
  email: z.string().email("E-mail inválido."),
  nome_completo: z.string().min(2, "Nome muito curto.").max(200),
  papel: z.enum([
    "admin_municipio",
    "rh_municipio",
    "financeiro_municipio",
    "leitura_municipio",
  ]),
  senha_temporaria: z
    .string()
    .min(8, "Senha temporária deve ter pelo menos 8 caracteres.")
    .max(128),
});

type NovoUsuarioValues = z.infer<typeof novoUsuarioSchema>;

function NovoUsuarioSheet({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (o: boolean) => void;
}) {
  const form = useForm<NovoUsuarioValues>({
    resolver: zodResolver(novoUsuarioSchema),
    defaultValues: {
      email: "",
      nome_completo: "",
      papel: "rh_municipio",
      senha_temporaria: "",
    },
  });

  const createMutation = useCreateUsuario();

  async function onSubmit(values: NovoUsuarioValues) {
    try {
      await createMutation.mutateAsync(values);
      toast.success("Usuário criado. Avise-o que precisa trocar a senha no primeiro login.");
      onOpenChange(false);
      form.reset();
    } catch (err) {
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
            form.setError(field as keyof NovoUsuarioValues, { type: "server", message });
            mappedAny = true;
          }
        }
      }
      if (!mappedAny) toast.error(extractDomainErrorMessage(err) ?? "Falha ao criar.");
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-md flex flex-col">
        <SheetHeader>
          <SheetTitle>Novo usuário</SheetTitle>
          <SheetDescription>
            Cria o usuário e atribui o papel no município ativo. Se o e-mail já
            existir em outro município, o sistema reaproveita o cadastro.
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
              name="nome_completo"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nome completo</FormLabel>
                  <FormControl>
                    <Input
                      autoComplete="name"
                      disabled={createMutation.isPending}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>E-mail</FormLabel>
                  <FormControl>
                    <Input
                      type="email"
                      autoComplete="email"
                      placeholder="usuario@municipio.gov.br"
                      disabled={createMutation.isPending}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="papel"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Papel</FormLabel>
                  <Select
                    value={field.value}
                    onValueChange={field.onChange}
                    disabled={createMutation.isPending}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {PAPEIS.map((p) => (
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
            <FormField
              control={form.control}
              name="senha_temporaria"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Senha temporária</FormLabel>
                  <FormControl>
                    <Input
                      type="text"
                      autoComplete="new-password"
                      disabled={createMutation.isPending}
                      {...field}
                    />
                  </FormControl>
                  <p className="text-xs text-muted-foreground">
                    O usuário será forçado a trocá-la no primeiro login.
                  </p>
                  <FormMessage />
                </FormItem>
              )}
            />

            <SheetFooter className="pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={createMutation.isPending}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? "Criando..." : "Criar usuário"}
              </Button>
            </SheetFooter>
          </form>
        </Form>
      </SheetContent>
    </Sheet>
  );
}
