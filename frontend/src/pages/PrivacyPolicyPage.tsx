import { Link } from "react-router-dom";

export function PrivacyPolicyPage() {
  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4 px-6 py-16 text-sm text-t2">
      <Link to="/" className="text-xs text-t3 hover:underline">
        &larr; Voltar para o FlowDesk
      </Link>
      <h1 className="font-heading text-2xl font-semibold tracking-tight text-t1">
        Política de Privacidade
      </h1>
      <p>
        O FlowDesk é um projeto de portfólio (clone de propósito educacional do Linear) mantido
        por Eduardo Holmer, sem fins comerciais. Esta página existe para deixar claro como os
        dados de quem testa a aplicação são tratados.
      </p>
      <h2 className="mt-4 font-heading text-lg font-semibold text-t1">Dados coletados</h2>
      <p>
        Ao criar uma conta (por e-mail/senha ou login social via Google/GitHub), armazenamos nome,
        e-mail e, quando aplicável, a foto de perfil fornecida pelo provedor. No login social, o
        FlowDesk recebe do provedor apenas o necessário para identificar a conta: e-mail
        verificado, nome e avatar — nenhum dado além do escopo `openid email profile` (Google) ou
        `read:user user:email` (GitHub) é solicitado.
      </p>
      <p>
        Dados de uso do produto (issues, projetos, comentários) ficam restritos ao workspace de
        quem os criou e não são compartilhados com terceiros nem usados para fins publicitários.
      </p>
      <h2 className="mt-4 font-heading text-lg font-semibold text-t1">Retenção e exclusão</h2>
      <p>
        Como este é um ambiente de demonstração, dados podem ser removidos periodicamente sem
        aviso prévio. Para solicitar a exclusão da sua conta e dos dados associados antes disso,
        entre em contato pelo e-mail abaixo.
      </p>
      <h2 className="mt-4 font-heading text-lg font-semibold text-t1">Contato</h2>
      <p>
        Dúvidas sobre esta política:{" "}
        <a className="underline" href="mailto:eduardoaholmer@gmail.com">
          eduardoaholmer@gmail.com
        </a>
        .
      </p>
    </div>
  );
}
