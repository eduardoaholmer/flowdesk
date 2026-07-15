import type { Control, FieldErrors, UseFormRegister } from "react-hook-form";
import { Controller } from "react-hook-form";

import { useProjects } from "@/features/projects/hooks";
import { useWorkspaceMembers } from "@/features/workspaces/hooks";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/components/ui/select";
import { Textarea } from "@/shared/components/ui/textarea";
import { MAX_PICKER_PAGE_SIZE } from "@/shared/lib/constants";

import type { IssuePriority, IssueStatus } from "../types";

export interface IssueFormValues {
  title: string;
  description?: string;
  project_id?: string;
  status: IssueStatus;
  priority: IssuePriority;
  assignee_id?: string;
  estimate?: string;
  due_date?: string;
}

const NONE = "__none__";

const STATUS_OPTIONS: { value: IssueStatus; label: string }[] = [
  { value: "BACKLOG", label: "Backlog" },
  { value: "TODO", label: "Todo" },
  { value: "IN_PROGRESS", label: "In Progress" },
  { value: "IN_REVIEW", label: "In Review" },
  { value: "DONE", label: "Done" },
  { value: "CANCELED", label: "Canceled" },
];

const PRIORITY_OPTIONS: { value: IssuePriority; label: string }[] = [
  { value: "NO_PRIORITY", label: "No priority" },
  { value: "LOW", label: "Low" },
  { value: "MEDIUM", label: "Medium" },
  { value: "HIGH", label: "High" },
  { value: "URGENT", label: "Urgent" },
];

export function IssueFormFields({
  workspaceId,
  register,
  control,
  errors,
  idPrefix,
}: {
  workspaceId: string;
  register: UseFormRegister<IssueFormValues>;
  control: Control<IssueFormValues>;
  errors: FieldErrors<IssueFormValues>;
  idPrefix: string;
}) {
  const { data: projects } = useProjects(workspaceId, {
    page: 1,
    per_page: MAX_PICKER_PAGE_SIZE,
    sort: "-created_at",
  });
  const { data: members } = useWorkspaceMembers(workspaceId);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-1.5">
        <Label htmlFor={`${idPrefix}-title`}>Título</Label>
        <Input
          id={`${idPrefix}-title`}
          placeholder="Corrigir bug de login"
          {...register("title")}
        />
        {errors.title && <p className="text-xs text-destructive">{errors.title.message}</p>}
      </div>

      <div className="flex flex-col gap-1.5">
        <Label htmlFor={`${idPrefix}-description`}>Descrição</Label>
        <Textarea
          id={`${idPrefix}-description`}
          placeholder="Detalhes da issue"
          {...register("description")}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1.5">
          <Label>Status</Label>
          <Controller
            control={control}
            name="status"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {STATUS_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label>Prioridade</Label>
          <Controller
            control={control}
            name="priority"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PRIORITY_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1.5">
          <Label>Projeto</Label>
          <Controller
            control={control}
            name="project_id"
            render={({ field }) => (
              <Select
                value={field.value ?? NONE}
                onValueChange={(value) => field.onChange(value === NONE ? undefined : value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Sem projeto" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={NONE}>Sem projeto</SelectItem>
                  {projects?.data.map((project) => (
                    <SelectItem key={project.id} value={project.id}>
                      {project.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label>Responsável</Label>
          <Controller
            control={control}
            name="assignee_id"
            render={({ field }) => (
              <Select
                value={field.value ?? NONE}
                onValueChange={(value) => field.onChange(value === NONE ? undefined : value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Sem responsável" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={NONE}>Sem responsável</SelectItem>
                  {members?.map((member) => (
                    <SelectItem key={member.user.id} value={member.user.id}>
                      {member.user.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`${idPrefix}-estimate`}>Estimativa (pontos)</Label>
          <Input
            id={`${idPrefix}-estimate`}
            type="number"
            min={0}
            placeholder="0"
            {...register("estimate")}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`${idPrefix}-due-date`}>Vencimento</Label>
          <Input id={`${idPrefix}-due-date`} type="date" {...register("due_date")} />
        </div>
      </div>
    </div>
  );
}
