from pilkit.exceptions import UnknownExtension, UnknownFormat


class AlreadyRegistered(Exception):
    pass


class NotRegistered(Exception):
    pass


class MissingGeneratorId(Exception):
    pass


class MissingSource(ValueError):
    silent_variable_failure = True


# Aliases for backwards compatibility
UnknownExtensionError = UnknownExtension
UnknownFormatError = UnknownFormat
