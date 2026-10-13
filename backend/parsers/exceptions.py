class ParserError(Exception):
    """Base parser exception."""
    pass


class ProductNotFound(ParserError):
    """No products found."""
    pass


class InvalidHTML(ParserError):
    """HTML is invalid."""
    pass


class ParsingError(ParserError):
    """Unexpected parsing error."""
    pass