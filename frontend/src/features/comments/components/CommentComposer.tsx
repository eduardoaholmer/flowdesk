import { useState } from "react";

import { Button } from "@/shared/components/ui/button";
import { Textarea } from "@/shared/components/ui/textarea";

import { useCreateComment } from "../hooks";

export function CommentComposer({
  workspaceId,
  issueId,
}: {
  workspaceId: string;
  issueId: string;
}) {
  const [body, setBody] = useState("");
  const createComment = useCreateComment(workspaceId, issueId);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const trimmed = body.trim();
    if (!trimmed) return;
    createComment.mutate(
      { body: trimmed },
      {
        onSuccess: () => setBody(""),
      },
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-2">
      <Textarea
        placeholder="Escreva um comentário… use @email para mencionar alguém do workspace"
        value={body}
        onChange={(event) => setBody(event.target.value)}
        rows={3}
      />
      <div className="flex justify-end">
        <Button type="submit" size="sm" disabled={!body.trim() || createComment.isPending}>
          {createComment.isPending ? "Enviando…" : "Comentar"}
        </Button>
      </div>
    </form>
  );
}
