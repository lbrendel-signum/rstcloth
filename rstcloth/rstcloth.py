"""Create a ReStructuredText document"""
import functools
import sys
import textwrap
import typing

from tabulate import tabulate

from rstcloth.utils import first_whitespace_position

Content = str | list[str]
Field = typing.Iterable[tuple[str, str]]
TableData = list[list]
Width = int | str
Widths = list[int] | str


def _indent(content: Content, indent: int) -> Content:
    """Prepends each nonempty line in content parameter with spaces.

    :param content: text to be indented
    :param indent: number of spaces to indent this element
    :return: modified content where each nonempty line is indented
    """
    if indent == 0:
        return content
    spaces = " " * indent
    if isinstance(content, str):
        content = content.splitlines()
    return "\n".join([spaces + line if line else line for line in content])


class RstCloth:
    """Create a ReStructuredText document programmatically.

    :param stream: output stream for writing ReStructuredText content
    :param line_width: Maximum length of each ReStructuredText content line.
        In some edge cases this limit might be crossed.

    """

    def __init__(self, stream: typing.TextIO = sys.stdout, line_width: int = 72) -> None:
        """Create a ReStructuredText document"""
        self._stream = stream
        self._line_width = line_width

    def fill(self, text: str, initial_indent: int = 0, subsequent_indent: int = 0) -> str:
        """Break text parameter into separate lines.

        Each line is indented accordingly to initial_indent and subsequent_indent parameters.

        :param text: input string to be wrapped and indented
        :param initial_indent: first line indentation size
        :param subsequent_indent: subsequent lines indentation size
        :return: wrapped and indented text

        """
        return textwrap.fill(
            text=text,
            width=self._line_width,
            initial_indent=" " * initial_indent,
            subsequent_indent=" " * subsequent_indent,
            expand_tabs=False,
            break_long_words=False,
            break_on_hyphens=False,
        )

    def _add(self, content: Content) -> None:
        """Places content into output stream.

        :param content: the text to write into this element
        """
        if isinstance(content, list):
            self._stream.write("\n".join(content) + "\n")
        else:
            self._stream.write(content + "\n")

    @property
    def data(self) -> str:
        """Return ReStructuredText document content as a string.

        :return: the content of output stream
        """
        self._stream.seek(0)
        return self._stream.read()

    def newline(self, count: int = 1) -> None:
        """Place a new line(s) into ReStructuredText document.

        :param count: the number of newlines to add

        """
        if count == 1:
            self._add("")
        else:
            # subtract one because every item gets one \n for free.
            self._add("\n" * (count - 1))

    def table(self, header: list, data: TableData | None, indent: int = 0) -> None:
        """Construct grid table.

        :param header: a list of header values (strings), to use for the table
        :param data: a list of lists of row data (same length as the header
            list each)
        :param indent: number of spaces to indent this elemen
        """
        t = tabulate(tabular_data=data, headers=header, tablefmt="grid", disable_numparse=True)
        self._add("\n" + _indent(t, indent) + "\n")

    def simple_table(self, header: list, data: TableData | None, indent: int = 0) -> None:
        """Construct a simple grid table.

        :param header: a list of header values (strings), to use for the table
        :param data: a list of lists of row data (same length as the header
            list each)
        :param indent: number of spaces to indent this element

        """
        t = tabulate(tabular_data=data, headers=header, tablefmt="rst", disable_numparse=True)
        self._add("\n" + _indent(t, indent) + "\n")

    def table_list(
        self,
        headers: typing.Iterable,
        data: TableData | None,
        widths: Widths | None = None,
        width: Width | None = None,
        indent: int = 0,
    ) -> None:
        """Construct list table.

        :param headers: a list of header values (strings), to use for the table
        :param data: a list of lists of row data (same length as the header
            list each)
        :param widths: list of relative column widths or the special
            value "auto"
        :param width: forces the width of the table to the specified
            length or percentage of the line width
        :param indent: number of spaces to indent this element
        """
        fields = []
        rows = []
        if headers:
            fields.append(("header-rows", "1"))
            rows.extend([headers])
        if widths is not None:
            if not isinstance(widths, str):
                widths = " ".join(map(str, widths))
            fields.append(("widths", widths))
        if width is not None:
            fields.append(("width", str(width)))

        self.directive("list-table", fields=fields, indent=indent)
        self.newline()

        if data:
            rows.extend(data)
        for row in rows:
            self.li(row[0], bullet="* -", indent=indent + 3)
            for cell in row[1:]:
                self.li(cell, bullet="  -", indent=indent + 3)
        self.newline()

    def directive(
        self,
        name: str,
        arg: str | None = None,
        fields: Field | None = None,
        content: Content | None = None,
        indent: int = 0,
    ) -> None:
        """Contruct reStructuredText directive.

        :param name: the directive itself to use
        :param arg: the argument to pass into the directive
        :param fields: fields to append as children underneath the directive
        :param content: the text to write into this element
        :param indent: number of spaces to indent this element
        """
        if arg is None:
            marker = f".. {name}::"
            self._add(_indent(marker, indent))
        else:
            first_whitespace = first_whitespace_position(arg)
            # If directive itself is too long to be fitted in a line or
            # directive with an argument can't be wrapped without breaking
            # the directive in half then it is better to exceed the line width
            # limitation.
            if len(name) + first_whitespace + indent + 6 > self._line_width:
                marker = f".. {name}::"
                self._add(_indent(marker, indent))
                self.content(arg, indent=indent + 3)
            else:
                marker = f".. {name}:: {arg}"
                result = self.fill(marker, initial_indent=indent, subsequent_indent=indent + 3)
                self._add(result)

        if fields is not None:
            for k, v in fields:
                self.field(name=k, value=v, indent=indent + 3)

        if content is not None:
            if isinstance(content, str):
                content = [content]
            self.newline()
            for line in content:
                self.content(line, indent=indent + 3)
            self.newline()

    @classmethod
    def role(cls, name: Content, value: str, text: str | None = None) -> str:
        """Return role with optional hyperlink.

        :param name: the name of the role
        :param value: the value of the role
        :param text: text after the role
        :return: role element
        """
        if isinstance(name, list):
            name = ":".join(name)

        if text is None:
            return f":{name}:`{value}`"
        link = cls.inline_link(text=text, link=value)
        return f":{name}:{link}"

    @staticmethod
    def bold(string: str) -> str:
        """Return strongly emphasised (boldface) text.

        :param string: the text to write into this element
        :return: bolded text
        """
        return f"**{string}**"

    @staticmethod
    def emph(string: str) -> str:
        """Return emphasised (italics) text.

        :param string: the text to write into this element
        :return: emphasised text
        """
        return f"*{string}*"

    @staticmethod
    def pre(string: str) -> str:
        """Return inline literals.

        :param string: the text to write into this element
        :return: inline literals
        """
        return f"``{string}``"

    @staticmethod
    def inline_link(text: str, link: str) -> str:
        """Return hyperlink reference.

        :param text: the printed value of the link
        :param link: the url the link should goto
        :return: hyperlink reference

        """
        return f"`{text} <{link}>`_"

    @staticmethod
    def footnote_ref(name: str) -> str:
        """Return footnote reference.

        :param name: the text to write into this element
        :return: footnote reference
        """
        return f"[#{name}]_"

    def replacement(self, name: str, value: str, indent: int = 0) -> None:
        """Contruct replacement directive.

        :param name: the name of the replacement
        :param value: the value for the replacement
        :param indent: number of spaces to indent this element
        """
        output = f".. |{name}| replace:: {value}"
        self._add(_indent(output, indent))

    def codeblock(
        self, content: Content, indent: int = 0, language: str | None = None
    ) -> None:
        """Contruct literal block.

        :param content: the text to write into this element
        :param indent: number of spaces to indent this element
        :param language: formal language indication for syntax
            highlighter
        :return: literal block
        """
        if language is None:
            self._add(self.fill("::", initial_indent=indent))
        else:
            self.directive(name="code-block", arg=language, indent=indent)
            self.newline()
        self._add(_indent(content, indent + 3))

    def footnote(self, ref: str, text: str, indent: int = 0) -> None:
        """Contruct footnote directive.

        :param ref: the reference value
        :param text: the text to write into this element
        :param indent: number of spaces to indent this element
        """
        self._add(self.fill(f".. [#{ref}] {text}", indent, indent + 3))

    def definition(self, name: str, text: str, indent: int = 0, bold: bool = False) -> None:  # noqa: FBT001, FBT002
        """Contruct definition list item.

        :param name: the name of the definition
        :param text: the text to write into this element
        :param indent: number of spaces to indent this element
        :param bold: should definition name be bolded
        """
        if bold is True:
            name = self.bold(name)

        self._add(self.fill(name, indent, indent))
        self._add(self.fill(text, indent + 3, indent + 3))

    def li(self, content: Content, bullet: str = "-", indent: int = 0) -> None:
        """Contruct bullet list item.

        :param content: the text to write into this element
        :param bullet: the character of the bullet
        :param indent: number of spaces to indent this element
        """
        bullet += " "
        hanging_indent_len = indent + len(bullet)

        if isinstance(content, list):
            content = bullet + "\n".join(content)
            self._add(self.fill(content, indent, indent + hanging_indent_len))
        else:
            self._add(self.fill(bullet + content, indent, hanging_indent_len))

    def field(self, name: str, value: str, indent: int = 0) -> None:
        """Contruct a field.

        :param name: the name of the field
        :param value: the value of the field
        :param indent: number of spaces to indent this element
        """
        first_whitespace = first_whitespace_position(value)
        if len(name) + first_whitespace + indent + 3 > self._line_width:
            marker = f":{name}:"
            self._add(_indent(marker, indent))
            self.content(value, indent=indent + 3)
        else:
            marker = f":{name}: {value}"
            result = self.fill(marker, initial_indent=indent, subsequent_indent=indent + 3)
            self._add(result)

    def ref_target(self, name: str, indent: int = 0) -> None:
        """Contruct hyperlink reference target.

        :param name: the name of the reference target
        :param indent: number of spaces to indent this element
        """
        o = f".. _{name}:"
        self._add(_indent(o, indent))

    def content(self, content: Content, indent: int = 0) -> None:
        """Contruct paragraph's content.

        :param content: the text to write into this element
        :param indent: number of spaces to indent this element
        """
        if isinstance(content, list):
            content = " ".join(content)
        self._add(self.fill(content, indent, indent))

    def heading(self, text: str, char: str, overline: bool = False, indent: int = 0) -> None:  # noqa: FBT001, FBT002
        """Contruct section title.

        :param text: the text to write into this element
        :param char: the character to line the heading with
        :param overline: should overline be included
        :param indent: number of spaces to indent this element
        :return: section title
        """
        underline = char * len(text)
        content = [text, underline]
        if overline:
            content.insert(0, underline)
        self._add(_indent(content, indent))

    h1 = functools.partialmethod(heading, char="=")
    h2 = functools.partialmethod(heading, char="-")
    h3 = functools.partialmethod(heading, char="~")
    h4 = functools.partialmethod(heading, char="+")
    h5 = functools.partialmethod(heading, char="^")
    h6 = functools.partialmethod(heading, char=";")
    title = functools.partialmethod(heading, char="=", overline=True)

    # admonitions
    admonition = functools.partialmethod(directive, name="admonition")
    attention = functools.partialmethod(directive, name="attention")
    caution = functools.partialmethod(directive, name="caution")
    danger = functools.partialmethod(directive, name="danger")
    error = functools.partialmethod(directive, name="error")
    hint = functools.partialmethod(directive, name="hint")
    important = functools.partialmethod(directive, name="important")
    note = functools.partialmethod(directive, name="note")
    tip = functools.partialmethod(directive, name="tip")
    warning = functools.partialmethod(directive, name="warning")

    # bibliographic fields
    abstract = functools.partialmethod(field, name="Abstract")
    address = functools.partialmethod(field, name="Address")
    author = functools.partialmethod(field, name="Author")
    authors = functools.partialmethod(field, name="Authors")
    contact = functools.partialmethod(field, name="Contact")
    copyright = functools.partialmethod(field, name="Copyright")
    date = functools.partialmethod(field, name="Date")
    dedication = functools.partialmethod(field, name="Dedication")
    organization = functools.partialmethod(field, name="Organization")
    revision = functools.partialmethod(field, name="Revision")
    status = functools.partialmethod(field, name="Status")
    version = functools.partialmethod(field, name="Version")

    # raw directives
    def page_break(self, template: str | None = None) -> None:
        """Contruct page break.

        :param template: name of the next page template
        """
        content = "PageBreak" if template is None else f"PageBreak {template}"
        self.directive(name="raw", arg="pdf", content=content)

    def frame_break(self, heights: int) -> None:
        """Contruct frame break.

        :param heights: height in points
        """
        self.directive(name="raw", arg="pdf", content=f"FrameBreak {heights}")

    def spacer(self, horizontal: int, vertical: int) -> None:
        """Contruct a spacer.

        :param horizontal: horizontal size in points
        :param vertical: vertical size in points
        """
        self.directive(
            name="raw",
            arg="pdf",
            content=f"Spacer {horizontal} {vertical}",
        )

    def table_of_contents(
        self,
        name: str | None = None,
        depth: int | None = None,
        backlinks: str | None = None,
    ) -> None:
        """Contruct table of contents.

        :param name: table of contents alternative title
        :param depth: the number of section levels that are collected
            in the table of contents
        :param backlinks: generate links from section headers back to
            the table of contents entries, the table of contents itself,
            or generate no backlinks
        """
        options = []
        if depth:
            options.append(("depth", str(depth)))
        if backlinks in ["entry", "top", "none"]:
            options.append(("backlinks", backlinks))
        self.directive(name="contents", arg=name, fields=options)

    def transition_marker(self) -> None:
        """Contruct transition marker."""
        self._add("\n---------\n")
