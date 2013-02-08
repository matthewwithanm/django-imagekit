from pilkit.exceptions import UnknownExtension, UnknownFormat


class AlreadyRegistered(Exception):
    pass


class NotRegistered(Exception):
    pass


class MissingGeneratorId(Exception):
    pass


# Aliases for backwards compatibility
UnknownExtensionError = UnknownExtension
UnknownFormatError = UnknownFormat
