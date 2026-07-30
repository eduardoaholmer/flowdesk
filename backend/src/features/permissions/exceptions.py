from src.core.exceptions import ValidationError


class CannotOverrideOwnerRoleError(ValidationError):
    code = "cannot_override_owner_role"
    message = "O papel OWNER sempre tem todas as permissões — não pode ser customizado."


class LockedPermissionError(ValidationError):
    code = "locked_permission"
    message = "Esta permissão é exclusiva do OWNER e não pode ser concedida a outro papel."
