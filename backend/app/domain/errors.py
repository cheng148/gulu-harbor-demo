class DomainError(Exception):
    """Base class for expected business failures."""


class ConversationNotFoundError(DomainError):
    pass


class ConversationAlreadyExistsError(DomainError):
    pass


class RevisionConflictError(DomainError):
    pass


class SessionExpiredError(DomainError):
    pass


class KnowledgeUnavailableError(DomainError):
    pass
