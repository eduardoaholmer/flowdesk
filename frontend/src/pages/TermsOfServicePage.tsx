import { Link } from "react-router-dom";

export function TermsOfServicePage() {
  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4 px-6 py-16 text-sm text-t2">
      <Link to="/" className="text-xs text-t3 hover:underline">
        &larr; Voltar para o FlowDesk
      </Link>
      <h1 className="font-heading text-2xl font-semibold tracking-tight text-t1">
        Termos de Serviço
      </h1>
      <p>
        O FlowDesk é um projeto de portfólio (clone de propósito educacional do Linear) mantido
        por Eduardo Holmer, disponibilizado "como está", sem garantias, para fins de demonstração
        e aprendizado.
      </p>
      <h2 className="mt-4 font-heading text-lg font-semibold text-t1">Uso do serviço</h2>
      <p>
        Ao criar uma conta você concorda em não usar o FlowDesk para armazenar dados sensíveis ou
        confidenciais reais, já que este é um ambiente de demonstração sem garantias de
        disponibilidade, backup ou continuidade. O serviço pode ser modificado, suspenso ou
        descontinuado a qualquer momento, sem aviso prévio.
      </p>
      <h2 className="mt-4 font-heading text-lg font-semibold text-t1">Login social</h2>
      <p>
        Ao entrar via Google ou GitHub, você autoriza o FlowDesk a criar/vincular uma conta usando
        o e-mail verificado pelo provedor, conforme descrito na{" "}
        <Link className="underline" to="/privacy">
          Política de Privacidade
        </Link>
        .
      </p>
      <h2 className="mt-4 font-heading text-lg font-semibold text-t1">Contato</h2>
      <p>
        Dúvidas sobre estes termos:{" "}
        <a className="underline" href="mailto:eduardoaholmer@gmail.com">
          eduardoaholmer@gmail.com
        </a>
        .
      </p>
    </div>
  );
}
